import logging
from pathlib import Path

from app.mqtt.client import BROKER, KEEPALIVE, PORT, create_client

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("logs/mqtt_consumer.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def main():
    client = create_client()
    client.connect(BROKER, PORT, KEEPALIVE)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nConsumidor detenido por el usuario.")