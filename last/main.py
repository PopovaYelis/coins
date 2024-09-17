import asyncio
import aiohttp


savings = 3
main_coin_from = 'BTC'
coins_to = ["USDT", "ETH", "XMR", "SOL", "RUB", "DOGE"]


dict_data = {'BTCUSDT': [],
             'BTCETH': [],
             'BTCXMR': [],
             'BTCSOL': [],
             'BTCRUB': [],
             'BTCDOGE': []}

async def  binance(client:aiohttp.ClientSession):
    for coin in coins_to:
        url_rec = f"https://api.binance.com/api/v3/ticker/price?symbol={main_coin_from}{coin}"
        headers = {'Accepts': 'application/json', }
        async with client.get(url_rec, headers=headers) as res:
            text = await res.json()
            if 'price' in text:
                dict_data[f"BTC{coin}"].append(float((text["price"])))
            else:
                url_rec = f"https://api.binance.com/api/v3/ticker/price?symbol={coin}{main_coin_from}"
                async with client.get(url_rec, headers=headers) as res:
                    text = await res.json()
                    dict_data[f"BTC{coin}"].append(1/float((text["price"])))

async def  coinmarket(client:aiohttp.ClientSession):
    for coin in coins_to:
        url_rec = f"https://pro-api.coinmarketcap.com/v2/tools/price-conversion?amount=1&id=1&convert={coin}"
        headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': '503072fd-20f8-46f9-8b0c-427ad0b0e5b5',}
        async with client.get(url_rec, headers=headers) as res:
            text = await res.json()
            dict_data[f"BTC{coin}"].append(float(text['data']['quote'][coin]['price']))


async def  bybit(client:aiohttp.ClientSession):
    coins_to = ["ETHUSDT", "XMRUSDT", "SOLUSDT", "DOGEUSDT"]
    url_rec = f"https://api.bybit.com/v5/market/tickers?category=inverse&symbol=BTCUSDT"
    headers = {'Accepts': 'application/json'}
    async with client.get(url_rec, headers=headers) as res:
        text = await res.json()
        exchange_rate = float(text['result']['list'][0]['lastPrice'])
        dict_data[f"BTCUSDT"].append(exchange_rate)
    for coin in coins_to:
        url_rec = f"https://api.bybit.com/v5/market/tickers?category=inverse&symbol={coin}"
        async with client.get(url_rec, headers=headers) as res:
            text = await res.json()
            dict_data[f"BTC{coin[:-4]}"].append(1/float(text['result']['list'][0]['lastPrice'])*exchange_rate)

async def gateio(client:aiohttp.ClientSession):
    coins_to = ["ETH_USDT", "XMR_USDT", "SOL_USDT", "DOGE_USDT"]
    url_rec = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT"
    headers = {'Accepts': 'application/json'}
    async with client.get(url_rec, headers=headers) as res:
        text = await res.json()
        exchange_rate = float(text[0]['last'])
        dict_data[f"BTCUSDT"].append(exchange_rate)
    for coin in coins_to:
        url_rec = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={coin}"
        async with client.get(url_rec, headers=headers) as res:
            text = await res.json()
            dict_data[f"BTC{coin[:-5]}"].append(1/float(text[0]['last'])*exchange_rate)


async def kucoin(client:aiohttp.ClientSession):
    coins_to = ["ETH-USDT", "XMR-USDT", "SOL-USDT", "DOGE-USDT"]
    url_rec = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT"
    headers = {'Accepts': 'application/json'}
    async with client.get(url_rec, headers=headers) as res:
        text = await res.json()
        exchange_rate = float(text['data']['price'])
        dict_data[f"BTCUSDT"].append(exchange_rate)
    for coin in coins_to:
        url_rec = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={coin}"
        async with client.get(url_rec, headers=headers) as res:
            text = await res.json()
            dict_data[f"BTC{coin[:-5]}"].append(1/float(text['data']['price'])*exchange_rate)

async def do_tasks():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
        tasks = [binance(client), coinmarket(client), bybit(client), gateio(client), kucoin(client)]
        return await asyncio.gather(*tasks)

asyncio.run(do_tasks())
for elem in coins_to:
    dict_data[f"BTC{elem}"] = max(dict_data[f"BTC{elem}"] )
    dict_data[f"BTC{elem}"] = dict_data[f"BTC{elem}"] *3
print(dict_data)








# session = Session()
# session.headers.update(headers)
#
# try:
#     response = session.get(url, params=parameters)
#     data = json.loads(response.text)['data']['quote']['USDT']['price']
#     print(data)
# except (ConnectionError, Timeout, TooManyRedirects) as e:
#     print(e)

# def get_data(url, header, client: aiohttp.ClientSession):
#     session = Session()
#     session.headers.update(header)
#     try:
#         response = session.get(url)
#         return response
#     except (ConnectionError, Timeout, TooManyRedirects) as e:
#         return e


# def get_data(url, main_coin, coins, headers: Optional[List]):
#     res = {}
#     for elem in url:
#         for coin in coins:
#             url_rec = f"{elem}{main_coin}{coin}"
#             response = request.(url_rec)
#             if response.status_code == 200:
#                 res[f"{main_coin}: {coin}"] = [float((response.json()["price"]))]
#             else:
#                 url_rec = f"{elem}{coin}{main_coin}"
#                 response = requests.get(url_rec)
#                 res[f"{main_coin}: {coin}"] = [(1/float(response.json()["price"]))]
#     print(res)
# binance()
# coinmarket()