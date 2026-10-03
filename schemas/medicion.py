from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class MedicionBase(BaseModel):
    estudiante_id: int
    variable: str = Field(max_length=50)
    valor: Decimal
    unidad: str = Field(max_length=20)

class MedicionCreate(MedicionBase):
    # Si no se envía, el servidor usa la fecha y hora actual
    fecha_hora: datetime | None = None

class MedicionUpdate(BaseModel):
    estudiante_id: int | None = None
    variable: str | None = Field(default=None, max_length=50)
    valor: Decimal | None = None
    unidad: str | None = Field(default=None, max_length=20)
    fecha_hora: datetime | None = None

    @model_validator(mode="after")
    def no_permitir_nulos(self):
        # Todas las columnas son obligatorias: se puede omitir un campo, pero no enviarlo como null
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(f"El campo '{campo}' no puede ser null")
        return self

class MedicionResponse(MedicionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha_hora: datetime
