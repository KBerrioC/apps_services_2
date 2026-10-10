from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class SensorMagnitud(Base):
    __tablename__ = "sensor_magnitudes"

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    magnitud: Mapped[str] = mapped_column(String(50), nullable=False)
    unidad: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valor_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    sensor: Mapped["Sensor"] = relationship(back_populates="magnitudes")
    mediciones: Mapped[list["Medicion"]] = relationship(
        back_populates="sensor_magnitud"
    )