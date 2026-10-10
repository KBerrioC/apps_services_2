from app.database.connection import SessionLocal
from app.models import Sensor

db = SessionLocal()
sensor = db.query(Sensor).filter(Sensor.codigo == "AQ-005").first()
print(sensor.id, sensor.codigo, sensor.nombre, sensor.categoria, sensor.activo)
for m in sensor.magnitudes:
    print(" ", m.magnitud, m.unidad, m.valor_minimo, m.valor_maximo)
db.close()