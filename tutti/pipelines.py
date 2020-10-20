import os
from scrapinghub import ScrapinghubClient
from .utils import post_to_slack


NO_EXECUTATION_TIME = 0


class TuttiPipeline:
    def open_spider(self, spider):
        self.spider = spider
        self.last_job_executation_time = self.get_last_job_executation_time()

    def process_item(self, item, spider):
        item_time = item["time"]

        if self.last_job_executation_time <= item_time:
            self.handle_webhooks(item)

        return item

    def get_last_job_executation_time(self):
        project_id = os.environ.get("SCRAPY_PROJECT_ID")
        api_key = self.spider.settings.get("SCRAPINGHUB_API_KEY")

        if not project_id or not api_key:
            return NO_EXECUTATION_TIME

        client = ScrapinghubClient(api_key)
        project = client.get_project(project_id)
        jobs = project.jobs.list()

        if not jobs:
            return NO_EXECUTATION_TIME

        for each in jobs:
            key = each["key"]
            job = client.get_job(key)

            metadata = dict(job.metadata.list())
            searchterm = metadata.get("spider_args", {}).get("searchterm", "")

            if self.spider.searchterm == searchterm:
                return int(metadata["running_time"] / 1000)

        return NO_EXECUTATION_TIME

    def handle_webhooks(self, item):
        slack_webhook = self.spider.settings.get("SLACK_WEBHOOK")

        if slack_webhook:
            post_to_slack(item, slack_webhook)
