from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, \
    create_engine, Identity, DateTime, Float
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Dict, Any
import csv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


engine = create_async_engine('postgresql+asyncpg://admin:admin@database:5432/admin', echo=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
session = async_session()
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Coins(Base):
    __tablename__ = 'currency_data'

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.now())
    difference = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)


    def __repr__(self):
        return f"Пользователь {self.title}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in
                self.__table__.columns}

async def log_to_csv(title: str):
    async with async_session() as session:
        stmt = select(Coins).where(Coins.title == title)
        data = await session.execute(stmt).first()
    if data:
        with open('currency_data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                data.title,
                float(data.price),
                float(data.max_price),
                float(data.min_price),
                data.date.isoformat(),
                float(data.difference),
                float(data.total_amount)
            ])
def get_currency_data_json(title: str):
    data =  session.query(Coins).filter(Coins.title == title).one_or_none()

    if data:
        response = {
            "title": data.title,
            "kash": [{
                "price": float(data.price),
                "minmax": [{
                    "max price": float(data.max_price),
                    "min price": float(data.min_price)
                }]
            }],
            "difference": float(data.difference),
            "total amount": float(data.total_amount),
            "coins": [
                {"BTC": f"{title[3:]}"}
            ],
            "date": data.date.isoformat()
        }
        return json.dumps(response, indent=4)
    else:
        return json.dumps({"error": "No data found"}, indent=4)

def update_price(title: str, new_price: float, total_amount: float):
    # Ищем запись с таким же заголовком (названием валютной пары)
    with engine.begin() as conn:
        stmt = select([Coins]).order_by(Coins.timestamp.desc()).limit(1)
        result = conn.execute(stmt)
        data = result.fetchone()
    res = ''
    if data:
        difference = new_price - data.price
        if new_price >= data.min_price + data.min_price * 0.00003:
            data.price = new_price
            res = get_currency_data_json(data.title)
            data.min_price = new_price
        # Обновляем максимальную и минимальную цены, если нужно
        if new_price > data.max_price:
            data.max_price = new_price
        if new_price < data.min_price:
            data.min_price = new_price

        #Обновляем текущую цену и другие поля
        data.difference = difference
        data.total_amount = total_amount
        data.date = datetime.now()

        session.commit()
    else:
        # Если записи не существует, создаем новую запись


        objects = [
            Coins(
                title=title,
                price=new_price,
                max_price=new_price,
                min_price=new_price,
                difference=0.0,
                total_amount=total_amount,
                date=datetime.now()
            )

        ]
        session.bulk_save_objects(objects)
        session.commit()
    if len(res) > 1:
        return f"{json.loads(res.encode())}"

# from tortoise import Tortoise, fields, models, run_async
# from typing import Dict, Any
# from datetime import datetime
# from tortoise.contrib.pydantic import pydantic_model_creator
#
#
# class Coins(models.Model):
#     id = fields.IntField(pk=True)
#     title = fields.CharField(max_length=50)
#     price = fields.FloatField()
#     max_price = fields.FloatField()
#     min_price = fields.FloatField()
#     date = fields.DatetimeField(auto_now_add=True)
#     difference = fields.FloatField()
#     total_amount = fields.FloatField()
#     class Meta:
#         table = "currency_data"
#
#     def __repr__(self):
#         return {c.name: getattr(self, c.name) for c in
#                 self.__table__.columns}
#
#
# async def main():
#     await Tortoise.init(
#         db_url="postgres://admin:admin@localhost:5432/test",
#         # Модулем для моделей указываем __main__,
#         # т.к. все модели для показа будем прописывать
#         # именно тут
#         modules={'models': ['__main__']},
#     )
#     await Tortoise.generate_schemas()
#
# async def update_price(title: str, new_price: float, total_amount: float):
#     # Ищем запись с таким же заголовком (названием валютной пары)
#     data = await Coins.filter(title=title).first()
#     with open('file.txt', 'a') as f:
#         f.write(data.price)
#
#     if data:
#         # Обновляем максимальную и минимальную цены, если нужно
#         if new_price > data.max_price:
#             data.max_price = new_price
#         if new_price < data.min_price:
#             data.min_price = new_price
#
#         # Рассчитываем разницу между новой ценой и текущей
#         difference = new_price - data.price
#
#         # Обновляем текущую цену и другие поля
#         data.price = new_price
#         data.difference = difference
#         data.total_amount = total_amount
#         data.date = datetime.now()
#
#         await data.save()
#     else:
#         # Если записи не существует, создаем новую запись
#         await Coins.create(
#             title=title,
#             price=new_price,
#             max_price=new_price,  # Устанавливаем текущую цену как max/min при первой записи
#             min_price=new_price,
#             difference=0.0,  # Нет разницы, так как это первая запись
#             total_amount=total_amount,
#             date=datetime.now()
#         )
#
