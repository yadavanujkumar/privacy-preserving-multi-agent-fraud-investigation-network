import logging
import os
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import json
from agents.fraud_investigator import process_alert

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "py-agents", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9093")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "high-value-transactions")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "fraud-agents-group")
KAFKA_RETRY_ATTEMPTS = int(os.getenv("KAFKA_RETRY_ATTEMPTS", "10"))
KAFKA_RETRY_DELAY_S = float(os.getenv("KAFKA_RETRY_DELAY_S", "5"))

_messages_processed = 0
_messages_failed = 0
_consumer_task: asyncio.Task | None = None


def _create_consumer() -> KafkaConsumer:
    for attempt in range(1, KAFKA_RETRY_ATTEMPTS + 1):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            logger.info("Kafka consumer connected to %s", KAFKA_BROKER)
            return consumer
        except NoBrokersAvailable:
            logger.warning(
                "Kafka broker unavailable (attempt %d/%d), retrying in %.1fs",
                attempt, KAFKA_RETRY_ATTEMPTS, KAFKA_RETRY_DELAY_S,
            )
            time.sleep(KAFKA_RETRY_DELAY_S)
    raise RuntimeError(f"Could not connect to Kafka after {KAFKA_RETRY_ATTEMPTS} attempts")


async def consume_messages() -> None:
    global _messages_processed, _messages_failed
    loop = asyncio.get_event_loop()
    consumer = await loop.run_in_executor(None, _create_consumer)
    logger.info("Kafka consumer loop started, topic=%s", KAFKA_TOPIC)
    try:
        for message in consumer:
            tx_data = message.value
            try:
                result = process_alert(tx_data)
                _messages_processed += 1
                logger.info(
                    "transaction_investigated",
                    extra={
                        "transaction_id": tx_data.get("id"),
                        "risk_score": result.get("risk_score"),
                        "summary": result.get("summary"),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                _messages_failed += 1
                logger.error("investigation_failed: %s tx_data=%s", exc, tx_data)
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled – shutting down")
    finally:
        consumer.close()
        logger.info("Kafka consumer closed")


@asynccontextmanager
async def lifespan(application: FastAPI):  # type: ignore[type-arg]
    global _consumer_task
    _consumer_task = asyncio.create_task(consume_messages())
    yield
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


@app.get("/health/live")
def health_live() -> dict:
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready(response: Response) -> dict:
    if _consumer_task and not _consumer_task.done():
        return {"status": "ready"}
    response.status_code = 503
    return {"status": "not ready"}


@app.get("/metrics")
def metrics() -> dict:
    return {
        "messages_processed": _messages_processed,
        "messages_failed": _messages_failed,
    }
