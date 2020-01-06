import os
from scrapinghub import ScrapinghubClient
from .utils import post_to_slack


class TuttiPipeline:
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
