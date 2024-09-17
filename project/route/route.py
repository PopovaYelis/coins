from pydantic import BaseModel
from typing import List
from fastapi import FastAPI, HTTPException
from sqlalchemy.future import select
from project.model import engine, session, Coins, update_price
from typing import Dict, Any, Optional

app = FastAPI()

class BaseView(BaseModel):
    title: Optional[str]
    price: Optional[str]

@app.on_event("shutdown")
async def shutdown():
    await session.close()
    await engine.dispose()


#GET-запрос для получения списка всех валютных пар
@app.get("/currency", response_model=List[BaseView])
async def get_currencies() -> Coins:
    async with session.begin():
        res = await session.execute(select(Coins))
    return res.scalars().all()

#GET-запрос для получения данных конкретной валютной пары
@app.get("/currency/{title}", response_model=BaseView)
async def get_currency(title: str) -> Coins:
    async with session.begin():
        res = await session.execute(select(Coins)).where(Coins.title == title)
    return res.scalars().all()


# PATCH-запрос для обновления данных валютной пары
@app.patch("/currency/{title}", response_model=BaseView)
async def update_currency(title: str, coin: BaseView):
    # Получение данных о валютной паре с помощью GET-запроса
    currency = session.query(Coins).filter(Coins.title == title).first()
    if currency is None:
        raise HTTPException(status_code=404, detail="Валютная пара не найдена")
    # Изменение нужных полей в данных
    if coin.price:
        update_price(title, BaseView.price, BaseView.price*3)
    if coin.title:
        currency.title = BaseView.title

    # Сохранение изменений в базе данных
    session.commit()
    return {"message": "Данные успешно обновлены"}


