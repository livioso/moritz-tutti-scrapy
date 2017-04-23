# -*- coding: utf-8 -*-
from contextlib import contextmanager
from slacker import Slacker
from copy import deepcopy
from time import sleep
from lxml import html
import argparse
import requests
import json
import re
import os

# file where we keep track of the state
MORITZ_STATE_FILE = 'moritz_state_v4'


def sanitize(some_string):
    """
    Remove leading and trailing line breaks, tabs,
    carriage returns and whitespace, replace multiple
    whitespace with one whitespace.
    """
    return re.sub('\s+', ' ', some_string).strip('\n\t\r ')


def get_node_value_or_empty_string(from_node, xpath):
    found_node = from_node.xpath(xpath)
    node_value = found_node[0] if len(found_node) > 0 else ''
    return sanitize(node_value)


def extract_product_information(node):
    """
    Extract the following product information
    ⋅ title         → a caption
    ⋅ description   → some more description
    ⋅ published     → published ["hh:mm" | "gestern" | "DD.MM"]
    ⋅ price         → price in CHF.
    ⋅ link          → URL to product
    """

    # info container has description, title and product link
    info_node = node.xpath('./div[@class="fl in-info"]')[0]
    title = get_node_value_or_empty_string(info_node, './h3[@class="in-title"]/a/text()')
    description = get_node_value_or_empty_string(info_node, './p[@class="in-text"]/text()')
    link = get_node_value_or_empty_string(info_node, './h3[@class="in-title"]/a/@href')
    published = get_node_value_or_empty_string(info_node, './em[@class="fl in-date"]/text()')
    price = get_node_value_or_empty_string(info_node, './span[@class="fl in-price"]/strong/text()')
    identifier = get_node_value_or_empty_string(info_node, '../@id')

    return {
        'identifier': identifier,
        'title': title,
        'description': description,
        'link': link,
        'published': published,
        'price': price,
    }


def extract_products(tree):
    """ Get the list of product <div> from Tutti.ch """
    return tree.xpath('//div[@class="in-click-th cf"]')


def crawl(search):
    while True:
        url_query = 'https://www.tutti.ch/ganze-schweiz?q={}'
        page = requests.get(url_query.format(search))
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
    """ Notify slack about offers, the caller needs to keep track if the are actually new"""

    for offer in offers:

        template = '''
        >>> *{title} // {price}.- SFr.* _{description}_ 👉 <{link}|more information>
        '''

        message = template.format(
            title=offer.get('title'),
            price=offer.get('price'),
            description=offer.get('description'),
            published=offer.get('published'),
            link=offer.get('link')
        )

        # defaults to moritz, but can be set via environment
        channel = os.environ.get('SLACK_CHANNEL', 'moritz')
        slack.chat.post_message('#{}'.format(channel), message)


def rehydrate_search_state(slack, search):
    """ Rehydrate the previous search state. """

    response = slack.files.list()

    if response.error is not None:
        return

    # get all uploaded files that are dumps of the previous states
    state_files = [state_file for state_file in response.body['files']
                   if state_file['title'] == MORITZ_STATE_FILE]

    previous_search_state = None

    if len(state_files) > 0:
        previous_search_state_file = state_files[0]

        # get the last state file, requires us to set
        # a bearer token because we use a private url
        bearer = os.environ['SLACK_API_TOKEN']
        previous_search_state = requests.get(
            previous_search_state_file['url_private_download'],
            headers={'Authorization': 'Bearer {}'.format(bearer)}
        ).json()

    # FIXME check that search is in keys()
    return previous_search_state or {search: []}


def hydrate_search_state(slack, search, notified_ids):
    """
    Saves the current search state (which ids the user has been notified about)
    as json in a file on Slack. This file gets rehydrate when this program gets
    executed the next time. This allows us to persist the state in an easy way.
    """

    channel = os.environ.get('SLACK_CHANNEL', 'moritz')

    # merge the current and old ids, so we don't have duplicated or missing ids
    updated_search_state = deepcopy(rehydrate_search_state(slack, search))
    updated_search_state_merged_id = set(
        updated_search_state[search]).union(notified_ids)
    updated_search_state.update({search: list(updated_search_state_merged_id)})

    slack.files.upload(
        content=json.dumps(updated_search_state),
        title=MORITZ_STATE_FILE,
        channels=['#{}'.format(channel)],
    )


def crawl_forever(search, interval_every):
    with slacker() as slack:
        notified_ids = set(
            rehydrate_search_state(
                slack,
                search).get(
                search,
                []))

    for offers in crawl(search):

        # figure out which ids have not been notified about yet
        new_offer_ids = set([offer.get('identifier') for offer in offers])
        unnotified_ids = new_offer_ids.difference(notified_ids)
        notified_ids = notified_ids.union(unnotified_ids)

        # only notify offers that have not been notified abouu
        unnotified_offers = [
            offer for offer in offers if offer['identifier'] in unnotified_ids]

        with slacker() as slack:
            notify_offers_in_slack(slack, unnotified_offers)

        if len(unnotified_offers) > 0:
            with slacker() as slack:
                hydrate_search_state(slack, search, notified_ids)

        # wait for next interval
        sleep(interval_every)


def main():
    parser = argparse.ArgumentParser(
        description='Crawl tutti.ch & notify about newly published offers in Slack.')

    parser.add_argument(
        '--search', required=True, type=str,
        help='Tells what to look for, e.g. "Roomba 780"'
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
