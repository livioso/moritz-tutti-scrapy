import requests


def post_to_slack(item, webhook):
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{item['link']}|{item['subject']}>*\n\n"
                    + f":round_pushpin: Region {item['region']}, {item['plz']}\n"
                    + f"*:heavy_dollar_sign: Price {item['price']}*",
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
