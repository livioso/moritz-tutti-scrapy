## Moritz

General purpose Tutti crawler with optional [pipeline](./tutti/pipelines.py) posting to Slack when a new offer matching a searchterm gets published on [Tutti.ch](http://www.tutti.ch).

### Scrapinghhub

1. Setup a new [Scrapinghub project](https://scrapinghub.com).
2. Deploy the spider using `shub deploy`.
3. Optional: Set `SLACK_WEBHOOK` and `SCRAPINGHUB_API_KEY` in the settings of your project to receive Slack notifications.
4. Run the spider with desired `searchterm` argument on Scrapinghub (manual or periodic).

### Development

_Installation_

```
python3 -m venv .venv
. ./.venv/bin/activate
pip install -r repository.txt
```

_Add add an optional `.env` file_

```
# Optional: Slack Webhook to be called
# SLACK_WEBHOOK=https://hooks.slack.com/services/XXXXXXXX/XXXXXXXX/XXXXXXXX

# Optional: Scraping Hub Project & Key
# only make sense for development
# SCRAPINGHUB_API_KEY=xxx
# SCRAPY_PROJECT_ID=xxx
```

_Running the spider to crawl for a searchterm_

Example 1: Crawl the latest `roomba` offers:

```
scrapy crawl tutti -a searchterm=roomba
```

Example 2: Crawl the latest 100 pages of all offers and dump results to a json:

```
scrapy crawl tutti -o offers.json -a pages=100
```

### Screenshot of Slack integration

<img src="https://github.com/livioso/Moritz/blob/master/screenshot.png?raw=True" width="360">
