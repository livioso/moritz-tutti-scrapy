# -*- coding: utf-8 -*-
from contextlib import contextmanager
from requests_html import HTMLSession
from slacker import Slacker
from time import sleep
import argparse
import hashlib
import os.path
import json
import os


def extract_title(offer):
    return offer.find('a')[1].text


def extract_description(offer):
    return offer.find('p', first=True).text


def extract_price(offer):
    return offer.find('strong', first=True).text


def extract_link(offer):
    return 'https://tutti.ch{}'.format(offer.find('a')[1].links.pop())


def extract_identifier(offer):
    return hashlib.md5(offer.text.encode('utf-8')).hexdigest()


def extract_published(offer):
    return offer.find('span', first=True).text


def extract_thumb_url(offer):
    return offer.find('img', first=True).attrs['src']


def extract_details(offer):
    """
    Extract the following product information
    ⋅ title         → a caption
    ⋅ description   → some more description
    ⋅ published     → published ["hh:mm" | "gestern" | "DD.MM" | heute]
    ⋅ price         → price in CHF.
    ⋅ link          → URL to product
    """

    return {
        'identifier': extract_identifier(offer),
        'title': extract_title(offer),
        'description': extract_description(offer),
        'thumb_url': extract_thumb_url(offer),
        'link': extract_link(offer),
        'published': extract_published(offer),
        'price': extract_price(offer),
    }


def extract_offers(response):
    """ Get the list of offers <div> from Tutti.ch """
    return response.html.find('div.pCKlD._1hpKF > div')


def crawl(search):
    """ Yields the latest offers, forever. """

    # URL to the Tutti search, can be set via environment TUTTI_URL
    url_default = 'https://www.tutti.ch/de/li/ganze-schweiz/angebote?q={search}&redirect=platform'
    url = os.environ.get('TUTTI_URL', url_default)
    url = url.format(search=search)

    session = HTMLSession()

    while True:

        response = session.get('https://www.tutti.ch/de/li/ganze-schweiz/angebote?q=Roomba&redirect=platform')

        # render the site in chromium:
        # initially, only a handful of images are visible
        # therefore scroll down till we have all images, always
        # waiting a bit.
        response.html.render(scrolldown=10, sleep=0.3, timeout=15)

        offers = [extract_details(offer) for offer in extract_offers(response)]

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

        price = offer.get('price')
        footer = 'Price: {} CHF'.format(price) if price != 'Gratis' else 'Price: Free'

        attachments = [{
            'color': "#55E3C7",
            'title': offer.get('title'),
            'title_link': offer.get('link'),
            'thumb_url': offer.get('thumb_url'),
            'footer': footer,
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
