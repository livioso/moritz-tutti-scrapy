import os
import re
import json
import scrapy
import urllib


class TuttiSpider(scrapy.Spider):
    name = "tutti"

    def __init__(self, searchterm="", pages=1, **kwargs):
        super().__init__(**kwargs)
        self.searchterm = searchterm
        self.pages = int(pages)

    def start_requests(self):
        for page in range(1, self.pages + 1):
            params = urllib.parse.urlencode({"o": page, "q": self.searchterm})

            yield scrapy.Request(
                callback=self.parse,
                dont_filter=True,
                url=f"https://www.tutti.ch/de/li/ganze-schweiz/angebote?{params}",
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
