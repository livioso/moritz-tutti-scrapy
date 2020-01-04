## Moritz

Get notified in Slack when a new offer that matches a [search query gets published](http://www.tutti.ch/ganze-schweiz) on [Tutti.ch](http://www.tutti.ch)

### Scrapinghhub

1. Fork this repository and setup a new [Scrapinghub project](https://scrapinghub.com).
2. Connect your fork to Scrapinghub and deploy the spider (connect to Github).
3. Set `SLACK_WEBHOOK`, `SCRAPINGHUB_API_KEY` and `SCRAPINGHUB_PROJECT` in the settings of your project.
4. Run the spider with desired `searchterm` argument on Scrapinghub (either manual or periodic).

### Development

_Installation_

```
python3 -m venv .venv
. ./.venv/bin/activate
pip install -r repository.txt
```

_Add add an `.env` file_

```
# Slack Webhook to be called
SLACK_WEBHOOK=https://hooks.slack.com/services/XXXXXXXX/XXXXXXXX/XXXXXXXX

# Optional: Scraping Hub Project & Key
# SCRAPINGHUB_API_KEY=xxx
# SCRAPINGHUB_PROJECT=xxx
```

_Running the spider_

```
scrapy crawl tutti -o ~/Desktop/offers.json -a searchterm=iphone -a pages=100
```

### Screenshot

<img src="https://github.com/livioso/Moritz/blob/master/screenshot.png?raw=True" width="360">
