from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sm
from app.database.connection import SessionLocal

db = SessionLocal()

sensor = crud_sensor.get_sensor_por_codigo(db, "AQ-005")
print("sensor:", sensor.id, sensor.codigo)

print("total sensores:", len(crud_sensor.get_sensores(db)))

for m in crud_sm.get_magnitudes_por_sensor(db, sensor.id):
    print("magnitud:", m.id, m.magnitud, m.unidad)

print("mediciones de AQ-005:", len(crud_medicion.get_mediciones(db, sensor.id)))
print("última medición:", crud_medicion.get_ultima_medicion(db, sensor.id))

db.close()