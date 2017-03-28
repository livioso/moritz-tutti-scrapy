from lxml import html
import requests

page = requests.get('http://www.tutti.ch/zuerich?q=roomba')
tree = html.fromstring(page.content)

import ipdb
ipdb.set_trace()
