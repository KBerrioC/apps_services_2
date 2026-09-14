from normalizacion import normalizar_registro


def test_transformacion_correcta_proveedor_b():
    """Un registro bien formado de proveedor B se normaliza sin errores."""
    registro = {
        "fuente": "proveedor_b",
        "posicion": 0,
        "crudo": {
            "record_code": "B-9999",
            "municipality": "Medellin",
            "country": "CO",
            "latitude_deg": "6.25",
            "longitude_deg": "-75.58",
            "temp_celsius": "20.0",
            "humidity_pct": "50.0",
            "wind_kmh": "10.0",
            "measurement_time": "01/09/2026 08:00",
            "origin_code": "PB",
        },
    }
    normalizado, error = normalizar_registro(registro)
    assert error is None
    assert normalizado["ciudad"] == "Medellin"
    assert normalizado["origen"] == "proveedor_b"
    assert normalizado["fecha_hora"] == "2026-09-01T08:00:00-05:00"


def test_conversion_unidades_proveedor_a():
    """Fahrenheit->Celsius y m/s->km/h deben convertirse correctamente."""
    registro = {
        "fuente": "proveedor_a",
        "posicion": 0,
        "crudo": {
            "provider_record_id": "A-9999",
            "station": {"code": "STA-01", "city_name": "Cali", "country_code": "CO"},
            "location": {"lat": 3.45, "lon": -76.53},
            "measurements": {
                "temperature_f": 32.0,   # debe dar 0.0 C
                "relative_humidity": 50.0,
                "wind_speed_ms": 10.0,   # debe dar 36.0 km/h
            },
            "observed_at": "2026-09-01T08:00:00-05:00",
            "source": "weather_provider_a",
        },
    }
    normalizado, error = normalizar_registro(registro)
    assert error is None
    assert normalizado["temperatura_c"] == 0.0
    assert normalizado["viento_kmh"] == 36.0


def test_error_normalizacion_dato_no_convertible():
    """Un valor no numérico donde se espera número debe marcarse como
    error de normalización, sin lanzar una excepción sin controlar."""
    registro = {
        "fuente": "proveedor_a",
        "posicion": 0,
        "crudo": {
            "provider_record_id": "A-9998",
            "station": {"code": "STA-01", "city_name": "Cali", "country_code": "CO"},
            "location": {"lat": 3.45, "lon": -76.53},
            "measurements": {
                "temperature_f": "N/A",
                "relative_humidity": 50.0,
                "wind_speed_ms": 10.0,
            },
            "observed_at": "2026-09-01T08:00:00-05:00",
            "source": "weather_provider_a",
        },
    }
    normalizado, error = normalizar_registro(registro)
    assert normalizado is None
    assert error is not None