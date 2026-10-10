from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.medicion import Medicion
from app.models.sensor_magnitud import SensorMagnitud


def get_medicion(db: Session, medicion_id: int) -> Medicion | None:
    consulta = (
        select(Medicion)
        .options(joinedload(Medicion.sensor_magnitud))
        .where(Medicion.id == medicion_id)
    )
    return db.scalar(consulta)


def get_mediciones(
    db: Session,
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = None,
) -> list[Medicion]:
    """Mediciones de un sensor, de la más reciente a la más antigua."""
    consulta = (
        select(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .options(joinedload(Medicion.sensor_magnitud))
        .where(SensorMagnitud.sensor_id == sensor_id)
    )
    if magnitud is not None:
        consulta = consulta.where(SensorMagnitud.magnitud == magnitud)
    if desde is not None:
        consulta = consulta.where(Medicion.timestamp_utc >= desde)
    if hasta is not None:
        consulta = consulta.where(Medicion.timestamp_utc <= hasta)

    consulta = consulta.order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc())
    if limit is not None:
        consulta = consulta.limit(limit)
    return list(db.scalars(consulta))


def get_ultima_medicion(db: Session, sensor_id: int) -> Medicion | None:
    resultado = get_mediciones(db, sensor_id, limit=1)
    return resultado[0] if resultado else None


def create_mediciones(
    db: Session,
    registros: list[tuple[int, Decimal]],
    timestamp_utc: datetime,
) -> list[Medicion]:
    """Guarda todas las magnitudes de un payload juntas (o ninguna)."""
    objetos = [
        Medicion(sensor_magnitud_id=sm_id, valor=valor, timestamp_utc=timestamp_utc)
        for sm_id, valor in registros
    ]
    try:
        db.add_all(objetos)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return objetos