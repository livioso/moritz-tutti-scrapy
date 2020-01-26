import requests


def post_to_slack(item, webhook):
    coordinates = item.get("coordinates")

    if coordinates:
        params = f"ll={coordinates['lat']},{coordinates['lon']}"
        link = f"https://www.google.com/maps?{params}"
        location = f":round_pushpin: <{link}|Region {item['region']}, {item['plz']}>\n"
    else:
        location = f":round_pushpin: Region {item['region']}, {item['plz']}\n"

    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{item['link']}|{item['subject']}>*\n"
                    + location
                    + f"*:heavy_dollar_sign: {item['price']}*",
                },
                "accessory": {
                    "type": "image",
                    "image_url": item.get("thumbnail"),
                    "alt_text": "Offer",
                },
            },
        ]
    }

    requests.post(webhook, json=payload)
