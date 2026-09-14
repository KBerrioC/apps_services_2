from unittest.mock import Mock
import requests
from cliente_api import enviar_medicion


def _medicion():
    return {
        "ciudad": "Medellin", "pais": "CO", "latitud": 6.25, "longitud": -75.58,
        "temperatura_c": 20.0, "humedad": 50.0, "viento_kmh": 10.0,
        "fecha_hora": "2026-09-01T08:00:00-05:00", "origen": "proveedor_a",
    }


def test_4xx_no_reintenta():
    sesion = Mock()
    sesion.post.return_value = Mock(status_code=422, json=lambda: {"error": "malo"})
    resultado = enviar_medicion("https://fake", "equipo_test", _medicion(), sesion=sesion)
    assert resultado["resultado"] == "rechazado_api"
    assert sesion.post.call_count == 1  # no debe reintentar en 4xx


def test_5xx_reintenta_hasta_exito():
    sesion = Mock()
    sesion.post.side_effect = [
        Mock(status_code=500, json=lambda: {}),
        Mock(status_code=201, json=lambda: {"id": "ok"}),
    ]
    resultado = enviar_medicion("https://fake", "equipo_test", _medicion(), sesion=sesion)
    assert resultado["resultado"] == "aceptado"
    assert sesion.post.call_count == 2


def test_error_comunicacion_agota_tres_intentos():
    sesion = Mock()
    sesion.post.side_effect = requests.exceptions.ConnectionError("sin conexión")
    resultado = enviar_medicion("https://fake", "equipo_test", _medicion(), sesion=sesion)
    assert resultado["resultado"] == "error_comunicacion"
    assert sesion.post.call_count == 3