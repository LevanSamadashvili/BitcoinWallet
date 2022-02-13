import requests


def default_btc_usd_convertor(btc_amount: float) -> float:
    url = "https://blockchain.info/ticker"

    response = requests.get(url, params=None)
    data = response.json()
    btc_price = data["USD"]["last"]

    return btc_amount * float(btc_price)
