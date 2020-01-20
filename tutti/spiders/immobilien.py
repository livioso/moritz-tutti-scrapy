# -*- coding: utf-8 -*-
import scrapy
import json
import re


class ImmobilienSpider(scrapy.Spider):
    name = "immobilien"

    def __init__(
        self,
        pages=1,
        searchterm=None,
        object_type=None,
        max_price=None,
        min_sqm=None,
        rooms=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.pages = int(pages)
        self.searchterm = searchterm if searchterm else ""
        self.object_type = object_type if object_type else "wohnungen"
        self.max_price = max_price if max_price else ""
        self.min_sqm = min_sqm if min_sqm else ""
        self.rooms = rooms if rooms else ""

    def start_requests(self):
        for page in range(1, self.pages + 1):
            yield scrapy.Request(
                callback=self.parse,
                dont_filter=True,
                url=f"https://www.tutti.ch/de/immobilien/objekttyp/{self.object_type}/standort/ort-{self.searchterm}/typ/mieten"
                + f"?floor_area={self.min_sqm}&price=,{self.max_price}&rooms={self.rooms}&paging={page}",
            )

    def transform_raw(self, data):
        return {
            "id": data["id"],
            "subject": data.get("subject"),
            "body": data.get("body"),
            "price": data.get("price"),
            "time": data.get("epoch_time"),
            "region": data.get("location_info", {}).get("region_name"),
            "plz": data.get("location_info", {}).get("plz"),
            "link": f"https://www.tutti.ch/vi/{data['id']}",
            "thumbnail": f"https://c.tutti.ch/images/{data.get('thumb_name')}",
            "images": [
                f"https://c.tutti.ch/images/{image}"
                for image in data.get("image_names", [])
            ],
            "_meta": data,
        }

    def parse(self, response):
        pattern = re.compile(r"window.__INITIAL_STATE__=(.*)", re.MULTILINE | re.DOTALL)

        data = response.xpath('//script[contains(., "INITIAL_STATE")]/text()').re(
            pattern
        )[0]

        items = json.loads(data)["items"]
        offers = reversed(sorted(items.items(), key=lambda item: item[1]["epoch_time"]))

        for _, offer in offers:
            yield self.transform_raw(offer)
