from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class SensorMagnitudOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    magnitud: str
    unidad: str
    valor_minimo: Decimal
    valor_maximo: Decimal

    @field_serializer("valor_minimo", "valor_maximo")
    def como_numero(self, v: Decimal) -> float:
        return float(v)