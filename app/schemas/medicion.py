from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

BOGOTA = ZoneInfo("America/Bogota")

# float estricto: rechaza textos como "abc" o "24.5" y también NaN / infinito
Valor = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class MagnitudPayload(BaseModel):
    value: Valor
    unit: str = Field(min_length=1)


class MensajeMQTT(BaseModel):
    """Estructura del mensaje JSON que publica el sensor."""

    sensor_id: str = Field(min_length=1)
    timestamp: datetime
    measurements: dict[str, MagnitudPayload] = Field(min_length=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validar_timestamp(cls, v):
        if not isinstance(v, str):
            raise ValueError("el timestamp debe ser un texto ISO 8601")
        try:
            dt = datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("el timestamp tiene un formato inválido")
        if dt.tzinfo is None:
            raise ValueError("el timestamp debe incluir zona horaria (UTC)")
        return dt.astimezone(timezone.utc)


class MedicionOut(BaseModel):
    """Respuesta de la API: la hora UTC guardada se muestra en hora de Colombia."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_magnitud_id: int
    magnitud: str | None = None
    unidad: str | None = None
    valor: Decimal
    timestamp_colombia: datetime = Field(validation_alias="timestamp_utc")

    @field_serializer("timestamp_colombia")
    def a_hora_colombia(self, v: datetime) -> str:
        return v.astimezone(BOGOTA).strftime("%Y-%m-%d %H:%M:%S")

    @field_serializer("valor")
    def valor_como_numero(self, v: Decimal) -> float:
        return float(v)