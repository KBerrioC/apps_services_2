from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor_magnitud as crud_sm
from app.database.connection import get_db
from app.schemas.sensor_magnitud import SensorMagnitudOut

router = APIRouter(prefix="/sensor-magnitudes", tags=["Sensor-magnitudes"])


@router.get("/{sensor_magnitud_id}", response_model=SensorMagnitudOut)
def obtener_sensor_magnitud(sensor_magnitud_id: int, db: Session = Depends(get_db)):
    sm = crud_sm.get_sensor_magnitud(db, sensor_magnitud_id)
    if sm is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sensor-magnitud {sensor_magnitud_id} no encontrada",
        )
    return sm