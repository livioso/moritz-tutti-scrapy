## Moritz
Get instantly notified in Slack when a new offer that matches a [search query gets published](http://www.tutti.ch/ganze-schweiz) on [Tutti.ch](http://www.tutti.ch)

### Getting Started
```
# ... build it
docker build -t moritz .

# ... run it
docker run --rm \
  -e "SLACK_API_TOKEN=YOUR_API_TOKEN" \
  -e "SLACK_CHANNEL=moritz" \
  -v ~/.moritz:/usr/src/app/data \
  -it moritz:latest python moritz.py --search="roomba"
```

### Usage
```
usage: moritz.py [-h] --search SEARCH [--interval-every INTERVAL_EVERY]

Crawl tutti.ch & get notified about newly published offers in Slack.

optional arguments:
  -h, --help                            show this help message and exit
  --search SEARCH                       Tell what to look for, e.g. "Roomba 780"
  --interval-every INTERVAL_EVERY       Time between intervals in seconds [optional, default: 60s]
```

### Screenshot
<img src="https://github.com/livioso/Moritz/blob/master/screenshot.png?raw=True" width="360">
