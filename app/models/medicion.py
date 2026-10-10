from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Medicion(Base):
    __tablename__ = "mediciones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sensor_magnitud_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_recepcion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sensor_magnitud: Mapped["SensorMagnitud"] = relationship(
        back_populates="mediciones"
    )
    @property
    def magnitud(self) -> str:
        return self.sensor_magnitud.magnitud

    @property
    def unidad(self) -> str:
        return self.sensor_magnitud.unidad
    