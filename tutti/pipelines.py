import os
from scrapinghub import ScrapinghubClient
from scrapy.utils.project import get_project_settings
from .utils import post_to_slack


class TuttiPipeline:
    def get_last_job_ids(self):

        project_id = self.settings.get("SCRAPY_PROJECT_ID")
        api_key = self.settings.get("SCRAPINGHUB_API_KEY")

        if not project_id or not api_key:
            return []

        client = ScrapinghubClient(api_key)
        project = client.get_project(project_id)
        jobs = project.jobs.list()

        if not jobs:
            return []

        # last = index 0
        last_job_key = jobs[0]["key"]
        last_job = client.get_job(last_job_key)

        return [item["id"] for item in last_job.items.iter()]

    def __init__(self):
        self.settings = get_project_settings()
        self.last_job_ids = self.get_last_job_ids()

    def handle_webhooks(self, item):
        slack_webhook = self.settings.get("SLACK_WEBHOOK")

        if slack_webhook:
            post_to_slack(item, slack_webhook)

    def process_item(self, item, spider):

        if item["id"] not in self.last_job_ids:
            self.handle_webhooks(item)

        return item
