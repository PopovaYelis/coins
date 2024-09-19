FROM python:3.9-slim

WORKDIR /project

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD (uvicorn shed:app --host 0.0.0.0 --port 5050 &) && python shed.py

