# -*- coding: utf-8 -*-
from lxml import html
from time import sleep
import argparse
import requests
import re


def sanitize(some_string):
    """
    Remove leading and trailing line breaks, tabs,
    carriage returns and whitespace, replace multiple
    whitespace with one whitespace.
    """
    return re.sub('\s+', ' ', some_string).strip('\n\t\r')


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
    title = info_node.xpath('./h3[@class="in-title"]/a/text()')[0]
    description = info_node.xpath('./p[@class="in-text"]/text()')[0]
    link = info_node.xpath('./h3[@class="in-title"]/a/@href')[0]
    published = node.xpath('./em[@class="fl in-date"]/text()')[0]
    price = node.xpath('./span[@class="fl in-price"]/strong/text()')[0]
    identifier = node.xpath('../@id')[0]

    return {
        identifier: {
            'title': sanitize(title),
            'description': sanitize(description),
            'link': sanitize(link),
            'published': sanitize(published),
            'price': sanitize(price),
        }
    }


def extract_products(tree):
    """ Get the list of product <div> from Tutti.ch """
    return tree.xpath('//div[@class="in-click-th cf"]')


def crawl(search):
    while True:
        page = requests.get('http://www.tutti.ch/ganze-schweiz?q={}'.format(search))
        tree = html.fromstring(page.content)
        yield [extract_product_information(product) for product in extract_products(tree)]


def notify_slack(offers):
    print(offers)  # TODO


def crawl_forever(search, interval_every):

    notified_ids = set()  # TODO persist

    for offers in crawl(search):
        # figure out which ids have not been notified about yet
        new_offer_ids = set([offer.keys()[0] for offer in offers])
        unnotified_ids = new_offer_ids.difference(notified_ids)
        notified_ids = notified_ids.union(unnotified_ids)

        # only notify offers that have not been notified about
        notify_slack([offer for offer in offers if offer.keys()[0] in unnotified_ids])

        # wait for next interval
        sleep(interval_every)


def main():
    parser = argparse.ArgumentParser(
        description='Crawl tutti.ch & notify about newly published offers in Slack.'
    )

    parser.add_argument(
        '--search', required=True, type=str,
        help='Tells what to look for, e.g. "Roomba 780"'
    )

    parser.add_argument(
        '--interval-every', required=False, type=int, default=60,
        help='Time between intervals in seconds [optional, default: 60s]'
    )

    args = parser.parse_args()
    crawl_forever(search=args.search, interval_every=args.interval_every)


if __name__ == "__main__":
    main()
