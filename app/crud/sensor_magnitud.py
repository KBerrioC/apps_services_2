from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor_magnitud import SensorMagnitud


def get_sensor_magnitud(db: Session, sensor_magnitud_id: int) -> SensorMagnitud | None:
    return db.get(SensorMagnitud, sensor_magnitud_id)


def get_magnitudes_por_sensor(db: Session, sensor_id: int) -> list[SensorMagnitud]:
    consulta = (
        select(SensorMagnitud)
        .where(SensorMagnitud.sensor_id == sensor_id)
        .order_by(SensorMagnitud.id)
    )
    return list(db.scalars(consulta))