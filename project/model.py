from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, \
    create_engine, Identity, DateTime, Float
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Dict, Any
import csv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

#создаем асинхронное подключение database
engine = create_async_engine('postgresql+asyncpg://admin:admin@database:5432/admin', echo=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
session = async_session()
Base = declarative_base()
Session = sessionmaker(bind=engine)

# описываем таблицу currency_data
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

def log_to_csv(data):
    #записываем данные в файл csv
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
def get_currency_data_json(data):
    #преобразуем данные в json
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
                {"BTC": f"{data.title[3:]}"}
            ],
            "date": data.date.isoformat()
        }
        return json.dumps(response, indent=4)
    else:
        return json.dumps({"error": "No data found"}, indent=4)

async def update_price(title: str, new_price: float, total_amount: float, data):
    # обновляем данные в таблице + вызываем функции для записи в csv и преобразования в json
    res = ''
    if data:
        difference = new_price - data.price
        if new_price >= data.min_price + data.min_price * 0.00003:
            data.price = new_price
            res = get_currency_data_json(data)
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
        session.add_all(objects)
        await session.commit()
    if len(res) > 1:
        return f"{json.loads(res.encode())}"

