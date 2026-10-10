from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.database.connection import get_db
from app.schemas.medicion import BOGOTA, MedicionOut

router = APIRouter(tags=["Mediciones"])


def _a_utc(valor: datetime | None) -> datetime | None:
    """Si el usuario no indica zona horaria, se interpreta como hora de Colombia."""
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=BOGOTA)
    return valor.astimezone(timezone.utc)


def _sensor_o_404(db: Session, sensor_id: int):
    sensor = crud_sensor.get_sensor(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} no encontrado")
    return sensor


@router.get("/mediciones/{medicion_id}", response_model=MedicionOut)
def obtener_medicion(medicion_id: int, db: Session = Depends(get_db)):
    medicion = crud_medicion.get_medicion(db, medicion_id)
    if medicion is None:
        raise HTTPException(
            status_code=404, detail=f"Medición {medicion_id} no encontrada"
        )
    return medicion


@router.get("/sensores/{sensor_id}/mediciones", response_model=list[MedicionOut])
def listar_mediciones(
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = Query(default=None, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _sensor_o_404(db, sensor_id)
    desde_utc, hasta_utc = _a_utc(desde), _a_utc(hasta)
    if desde_utc and hasta_utc and desde_utc > hasta_utc:
        raise HTTPException(
            status_code=400,
            detail="El parámetro 'desde' no puede ser posterior a 'hasta'",
        )
    return crud_medicion.get_mediciones(
        db, sensor_id, magnitud, desde_utc, hasta_utc, limit
    )


@router.get("/sensores/{sensor_id}/ultima-medicion", response_model=list[MedicionOut])
def ultima_medicion(sensor_id: int, db: Session = Depends(get_db)):
    """Devuelve todas las magnitudes del instante más reciente."""
    _sensor_o_404(db, sensor_id)
    ultima = crud_medicion.get_ultima_medicion(db, sensor_id)
    if ultima is None:
        raise HTTPException(
            status_code=404, detail=f"El sensor {sensor_id} aún no tiene mediciones"
        )
    return crud_medicion.get_mediciones(
        db, sensor_id, desde=ultima.timestamp_utc, hasta=ultima.timestamp_utc
    )