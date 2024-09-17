from pydantic import BaseModel
from tortoise.contrib.fastapi import register_tortoise

from flask import Flask, jsonify
from typing import Dict, Any

app = Flask(__name__)


# Pydantic модель для обновления данных
class CurrencyUpdateModel(BaseModel):
    price: float = None
    total_amount: float = None


# GET-запрос для получения списка всех валютных пар
@app.route("/currency")
def get_currencies():
    currencies =  Coins.all()
    return  CurrencyData_Pydantic.from_queryset(currencies)


# GET-запрос для получения данных конкретной валютной пары
@app.route("/currency/{title}")
def get_currency(title: str):
    currency =  Coins.filter(title=title).first()

    return  CurrencyData_Pydantic.from_tortoise_orm(currency)


# PATCH-запрос для обновления данных валютной пары
@app.route("/currency/{title}")
def patch_currency(title: str, update_data: CurrencyUpdateModel):
    # Поиск записи по заголовку
    currency =  Coins.filter(title=title).first()


    # Обновляем цену, если она передана
    if update_data.price is not None:
        if update_data.price > currency.max_price:
            currency.max_price = update_data.price
        if update_data.price < currency.min_price:
            currency.min_price = update_data.price
        currency.difference = update_data.price - currency.price
        currency.price = update_data.price

    # Обновляем общий объем, если передан
    if update_data.total_amount is not None:
        currency.total_amount = update_data.total_amount


    # Возвращаем обновленную запись
    return CurrencyData_Pydantic.from_tortoise_orm(currency)



if __name__ == '__main__':
    app.run()
