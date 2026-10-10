from fastapi import FastAPI

from app.api import medicion, sensor, sensor_magnitud

app = FastAPI(
    title="API IoT - Taller 2",
    description="Consulta de sensores, magnitudes y mediciones recibidas por MQTT",
)

app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)


@app.get("/", tags=["Estado"])
def raiz():
    return {"mensaje": "API IoT funcionando", "documentacion": "/docs"}