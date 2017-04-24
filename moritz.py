# -*- coding: utf-8 -*-
from contextlib import contextmanager
from slacker import Slacker
from time import sleep
from lxml import html
import argparse
import requests
import os.path
import json
import re
import os


def sanitize(some_string):
    """
    Remove leading and trailing line breaks, tabs,
    carriage returns and whitespace, replace multiple
    whitespace with one whitespace.
    """
    return re.sub('\s+', ' ', some_string).strip('\n\t\r ')


def value_or_empty_string(from_node, xpath):
    found_node = from_node.xpath(xpath)
    return found_node[0] if len(found_node) > 0 else ''


def extract_product_information(root_node_product):
    """
    Extract the following product information
    ⋅ title         → a caption
    ⋅ description   → some more description
    ⋅ published     → published ["hh:mm" | "gestern" | "DD.MM"]
    ⋅ price         → price in CHF.
    ⋅ link          → URL to product
    """

    # each root product node should have an info section
    info_node = root_node_product.xpath('./div[@class="fl in-info"]')[0]

    # root product node has identifier, published date and price
    identifier = value_or_empty_string(root_node_product, '../@id')
    published = value_or_empty_string(root_node_product, './em[@class="fl in-date"]/text()')
    price = value_or_empty_string(root_node_product, './span[@class="fl in-price"]/strong/text()')
    thumb_url = value_or_empty_string(root_node_product, './div[@class="li-thumb fl in-thumb"]/a/img/@src')

    # info container has description, title and product link
    title = value_or_empty_string(info_node, './h3[@class="in-title"]/a/text()')
    description = value_or_empty_string(info_node, './p[@class="in-text"]/text()')
    link = value_or_empty_string(info_node, './h3[@class="in-title"]/a/@href')
    link = link.replace('http://', 'https://')

    return {
        'identifier': sanitize(identifier),
        'title': sanitize(title),
        'description': sanitize(description),
        'thumb_url': sanitize(thumb_url),
        'link': sanitize(link),
        'published': sanitize(published),
        'price': sanitize(price),
    }


def extract_products(tree):
    """ Get the list of product <div> from Tutti.ch """
    return tree.xpath('//div[@class="in-click-th cf"]')


def crawl(search):
    """ Yields the latest offers, forever. """

    # URL to the Tutti search, can be set via environment TUTTI_URL
    url_default = 'https://www.tutti.ch/ganze-schweiz/angebote?q={search_query}'
    url = os.environ.get('TUTTI_URL', url_default)

    while True:
        page = requests.get(url.format(search_query=search))
        tree = html.fromstring(page.content)

        offers = [
            extract_product_information(product)
            for product in extract_products(tree) if len(product) > 0
        ]

        # on the page it's newest to oldest but
        # we want the reversed order for the chat
        yield list(reversed(offers))


@contextmanager
def slacker():
    """ Keep the slacker session short-lived, use 'with slacker() as slack'"""
    slack = Slacker(os.environ['SLACK_API_TOKEN'])
    yield slack


def notify_offers_in_slack(slack, offers):
    """ Notify slack about offers, the caller needs to keep track if they are actually new"""

    for offer in offers:

        # defaults to moritz, but can be set via environment
        channel = os.environ.get('SLACK_CHANNEL', 'moritz')
        bot_user = os.environ.get('SLACK_BOT_USER', 'moritz_bot')

        # workaround for mobile: on mobile the title_link does not work (bug?)
        # therefore add a little link at the end of the description to tutti.ch
        text = '{} <{}|more>'.format(offer.get('description'), offer.get('link'))

        attachments = [{
            'color': "#55E3C7",
            'title': offer.get('title'),
            'title_link': offer.get('link'),
            'thumb_url': offer.get('thumb_url'),
            'footer': 'Price: {}.- CHF'.format(offer.get('price')),
            'text': text
        }]

        slack.chat.post_message(
            channel='#{}'.format(channel),
            attachments=attachments,
            as_user=bot_user
        )


def load_search_data_json(file_path):
    """ Just get the search data file as json, if existing otherwise {} """

    if not os.path.isfile(file_path):
        return {}

    with open(file_path, 'r') as data_file:
        return json.load(data_file)


def dump_search_data_json(search, notified_ids, file_path):
    """
    Dump the search into a combined file that keeps track
    of all the notified_ids for each search. The format
    looks like this:

    {
        'roomba': [42, 23, 45, 46],
        'quietcomfort qc35': [12, 24, 64]
    }

    """

    # update the notified_ids just for the current search
    searches = load_search_data_json(file_path)
    searches.update({search: list(notified_ids)})

    with open(file_path, 'w+') as data_file:
        json.dump(searches, data_file)


def crawl_forever(search, interval_every):
    file_path = os.environ.get('SEARCHES_JSON', 'data/searches.json')
    searches = load_search_data_json(file_path)
    notified_ids = set(searches.get(search, []))

    for offers in crawl(search):

        # figure out which ids have not been notified about yet
        new_offer_ids = set([offer.get('identifier') for offer in offers])
        unnotified_ids = new_offer_ids.difference(notified_ids)
        notified_ids = notified_ids.union(unnotified_ids)

        # only notify offers that have not been notified about
        unnotified_offers = [
            offer for offer in offers if offer['identifier'] in unnotified_ids
        ]

        if len(unnotified_offers) > 0:
            with slacker() as slack:
                notify_offers_in_slack(slack, unnotified_offers)

            # update json file dump since notified_ids has changed
            dump_search_data_json(search, notified_ids, file_path)

        # wait for next interval
        sleep(interval_every)


def main():
    parser = argparse.ArgumentParser(
        description='Crawl tutti.ch & notify about newly published offers in Slack.')

    parser.add_argument(
        '--search', required=True, type=str,
        help='Tell what to look for, e.g. "Roomba 780"'
    )

    parser.add_argument(
        '--interval-every', required=False, type=int, default=60,
        help='Time between intervals in seconds [optional, default: 60s]'
    )

    args = parser.parse_args()

    try:
        crawl_forever(
            search=args.search,
            interval_every=args.interval_every
        )
    except KeyboardInterrupt:
        raise


if __name__ == "__main__":
    main()
