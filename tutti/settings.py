from dotenv import load_dotenv
load_dotenv()

BOT_NAME = "tutti"

SPIDER_MODULES = ["tutti.spiders"]
NEWSPIDER_MODULE = "tutti.spiders"
ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {"tutti.pipelines.TuttiPipeline": 300}
