import os
from scrapinghub import ScrapinghubClient
from .utils import post_to_slack

ENV_SCRAPINGHUB_API_KEY = "SCRAPINGHUB_APIKEY"
ENV_SCRAPINGHUB_PROJECT = "SCRAPINGHUB_PROJECT"
ENV_SLACK_WEBHOOK = "SLACK_WEBHOOK"


class TuttiPipeline:
    def last_job_item_ids(self):
        if (
            ENV_SCRAPINGHUB_PROJECT not in os.environ
            or ENV_SCRAPINGHUB_API_KEY not in os.environ
        ):
            return []

        client = ScrapinghubClient(os.environ[ENV_SCRAPINGHUB_API_KEY])
        project = client.get_project(os.environ[ENV_SCRAPINGHUB_PROJECT])
        jobs = project.jobs.list()

        if not jobs:
            return []

        # last = index 0
        last_job_key = jobs[0]["key"]
        last_job = client.get_job(last_job_key)

        return [item["id"] for item in last_job.items.iter()]

    def __init__(self):
        self.last_job_ids = self.last_job_item_ids()

    def handle_webhooks(self, item):
        if ENV_SLACK_WEBHOOK in os.environ:
            webhook = os.environ[ENV_SLACK_WEBHOOK]
            post_to_slack(item, webhook)

    def process_item(self, item, spider):
        if item["id"] not in self.last_job_ids:
            self.handle_webhooks(item)

        return item
