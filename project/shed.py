import asyncio
import aiohttp
import schedule
from model import update_price, Base, engine, log_to_csv, Coins, session
from mail import send_email
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI, HTTPException
from sqlalchemy.future import select
from typing import Dict, Any, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from config import X_CMC_PRO_API_KEY, email_list


savings = 3
main_coin_from = 'BTC'
coins_to = ["USDT", "ETH", "XMR", "SOL", "RUB", "DOGE"]


dict_data = {'BTCUSDT': [],
             'BTCETH': [],
             'BTCXMR': [],
             'BTCSOL': [],
             'BTCRUB': [],
             'BTCDOGE': []}

# binance, coinmarket, bybit, gateio, kucoin парсим данные
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

async def  coinmarket(client:aiohttp.ClientSession, key:str):
    for coin in coins_to:
        url_rec = f"https://pro-api.coinmarketcap.com/v2/tools/price-conversion?amount=1&id=1&convert={coin}"
        headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': key,}
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

# call update_price and select data from table
async def update_currencies():
    async with session.begin():
        with open('log.txt', 'w') as f:
            for elem in coins_to:
                dict_data[f"BTC{elem}"] = max(dict_data[f"BTC{elem}"])
            for key in dict_data.keys():
                res = await session.execute(select(Coins).where(Coins.title == key))
                coins = res.scalars().first()
                data = await update_price(key, dict_data[key], dict_data[key] * 3, coins)
                if data:
                    log_to_csv(coins)
                    f.write(str(data))
            for elem in coins_to:
                dict_data[f"BTC{elem}"] = []
        try:
            with open('log.txt', 'r') as f:
                if len(f.read()) > 5:
                    for email in email_list:
                        send_email(email, 'log.txt')
        except FileNotFoundError:
            return 1



async def do_tasks():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
        tasks = [binance(client), coinmarket(client, X_CMC_PRO_API_KEY), bybit(client), gateio(client), kucoin(client)]
        return await asyncio.gather(*tasks)

async def do_tasks_update():
    tasks = [update_currencies()]
    return await asyncio.gather(*tasks)



def main_program():
    asyncio.run(do_tasks())
    asyncio.run(do_tasks_update())


# schedule to application
schedule.every(3).seconds.do(main_program)

app = FastAPI()

# schema for HTTP requests
class BaseView(BaseModel):
    title: Optional[str]
    price: Optional[float]
    max_price: Optional[float]
    min_price: Optional[float]
    difference: Optional[float]
    total_amount: Optional[float]

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    await session.close()
    await engine.dispose()


#GET-запрос для получения списка всех валютных пар
@app.get("/currency", response_model=List[BaseView])
async def get_currencies() -> List[BaseView]:
    async with session.begin():
        res = await session.execute(select(Coins))
    coins = res.scalars().all()
    base_views = [BaseView(**jsonable_encoder(coin)) for coin in coins]
    return base_views

#GET-запрос для получения данных конкретной валютной пары
@app.get("/currency/{title}", response_model=BaseView)
async def get_currency(title: str) ->BaseView:
    async with session.begin():
        res = await session.execute(select(Coins).where(Coins.title == title))
    coins = res.scalars().first()
    base_views = BaseView(**jsonable_encoder(coins))
    return base_views



# PATCH-запрос для обновления данных валютной пары
@app.patch("/currency/{title}", response_model=BaseView)
async def update_currency(title: str, coin: BaseView):
    # Получение данных о валютной паре с помощью GET-запроса
    async with session.begin():
        res = await session.execute(select(Coins).where(Coins.title == title))
        currency = res.scalars().first()
    if currency is None:
        raise HTTPException(status_code=404, detail="Валютная пара не найдена")
    # Изменение нужных полей в данных
    if coin.price:
        await update_price(title, BaseView.price, BaseView.price*3, coin)
    if coin.title:
        currency.title = BaseView.title

    # Сохранение изменений в базе данных
    session.commit()
    return {"message": "Данные успешно обновлены"}


@app.delete("/currency/{title}", response_model=BaseView)
async def delete_currency(title: str):
    # Получение данных о валютной паре с помощью GET-запроса
    async with session.begin():
        res = await session.execute(select(Coins).where(Coins.title == title))
        currency = res.scalars().first()
    if currency is None:
        raise HTTPException(status_code=404, detail="Валютная пара не найдена")

    # Удаление данных валютной пары
    async with session.begin():
        res = await session.delete(currency)
        await session.commit()

    return {"message": "Данные успешно удалены"}


if __name__ == '__main__':
    while True:
        schedule.run_pending()

