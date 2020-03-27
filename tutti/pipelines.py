import os
import re
from scrapy.exceptions import DropItem
from scrapinghub import ScrapinghubClient
from .utils import post_to_slack


class MatchPriceMinMaxPipeline:
    def open_spider(self, spider):
        self.min_price = spider.min_price
        self.max_price = spider.max_price

    def process_item(self, item, spider):
        if self.max_price is None and self.min_price is None:
            return item

        matches = re.findall("[0-9]+", item["price"])

        if matches:
            price = int("".join(matches))

            if self.max_price and price > self.max_price:
                raise DropItem("Item price > max_price.")

            if self.min_price and price < self.min_price:
                raise DropItem("Item price < min_price.")

        return item


class MatchSearchtermPipeline:
    """
    Default Tutti.ch search does not work well:
    I.e. searchterm "Peak Design" matches everything
    that either has Peak or Design in the text.
    This pipeline drops items that don't have the
    full searchterm "Peak Design" (case insensitive).
    """

    def open_spider(self, spider):
        self.searchterm = spider.searchterm.lower()

    def process_item(self, item, spider):
        item_content = (item["subject"] + item["body"]).lower()

        if self.searchterm not in item_content:
            raise DropItem("Item does not contain searchterm.")

        return item


class SlackNotifierPipeline:
    def open_spider(self, spider):
        self.spider = spider
        self.last_job_ids = self.get_last_job_ids()

    def process_item(self, item, spider):
        if item["id"] not in self.last_job_ids:
            self.handle_webhooks(item)

        return item

    def get_last_job_ids(self):
        project_id = os.environ.get("SCRAPY_PROJECT_ID")
        api_key = self.spider.settings.get("SCRAPINGHUB_API_KEY")

        if not project_id or not api_key:
            return []

        client = ScrapinghubClient(api_key)
        project = client.get_project(project_id)
        jobs = project.jobs.list()

        if not jobs:
            return []

        # find last job for spider searchterm same spider
        # can be invoked with different searchterms
        last_matching_job = None

        for each in jobs:
            key = each["key"]
            job = client.get_job(key)

            metadata = dict(job.metadata.list())
            searchterm = metadata.get("spider_args", {}).get("searchterm", "")

            if self.spider.searchterm == searchterm:
                last_matching_job = job
                break

        if not last_matching_job:
            return []

        return [item["id"] for item in last_matching_job.items.iter()]

    def handle_webhooks(self, item):
        slack_webhook = self.spider.settings.get("SLACK_WEBHOOK")

        if slack_webhook:
            post_to_slack(item, slack_webhook)
