import os
import asyncio
from fastapi import FastAPI
from kafka import KafkaConsumer
import json
from agents.fraud_investigator import process_alert

app = FastAPI()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9093")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_messages())

async def consume_messages():
    consumer = KafkaConsumer(
        'high-value-transactions',
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    for message in consumer:
        tx_data = message.value
        result = process_alert(tx_data)
        print(f"Agent Investigation Result: {result}")

@app.get("/health")
def health():
    return {"status": "ok"}