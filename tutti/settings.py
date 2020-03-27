import importlib
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass

# custom settings
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
SCRAPINGHUB_API_KEY = os.environ.get("SCRAPINGHUB_API_KEY")

# standard settings
BOT_NAME = "tutti"
ROBOTSTXT_OBEY = True
SPIDER_MODULES = ["tutti.spiders"]
NEWSPIDER_MODULE = "tutti.spiders"

ITEM_PIPELINES = {
    "tutti.pipelines.MatchPriceMinMaxPipeline": 100,
    "tutti.pipelines.MatchSearchtermPipeline": 101,
    "tutti.pipelines.SlackNotifierPipeline": 300,
}
