from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor import Sensor


def get_sensores(db: Session) -> list[Sensor]:
    return list(db.scalars(select(Sensor).order_by(Sensor.id)))


def get_sensor(db: Session, sensor_id: int) -> Sensor | None:
    return db.get(Sensor, sensor_id)


def get_sensor_por_codigo(db: Session, codigo: str) -> Sensor | None:
    return db.scalar(select(Sensor).where(Sensor.codigo == codigo))