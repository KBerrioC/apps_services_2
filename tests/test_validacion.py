from validacion import validar_registro


def _medicion_base(**overrides):
    base = {
        "id_trazabilidad": "X-0001",
        "fuente": "proveedor_a",
        "ciudad": "Medellin",
        "pais": "CO",
        "latitud": 6.25,
        "longitud": -75.58,
        "temperatura_c": 20.0,
        "humedad": 50.0,
        "viento_kmh": 10.0,
        "fecha_hora": "2026-09-01T08:00:00-05:00",
        "origen": "proveedor_a",
    }
    base.update(overrides)
    return base


def test_registro_valido():
    """Un registro dentro de todos los rangos debe pasar la validación."""
    es_valido, motivos = validar_registro(_medicion_base())
    assert es_valido is True
    assert motivos == []


def test_registro_invalido_humedad_fuera_de_rango():
    """Humedad > 100 debe rechazarse localmente, con motivo explícito."""
    es_valido, motivos = validar_registro(_medicion_base(humedad=150.0))
    assert es_valido is False
    assert any("humedad" in m for m in motivos)


def test_caso_limite_valores_frontera_son_validos():
    """Los límites exactos del contrato (-90/90, -180/180, 0/100, viento=0)
    deben considerarse válidos, no rechazados (rango inclusivo)."""
    es_valido, motivos = validar_registro(_medicion_base(
        latitud=90.0, longitud=-180.0, humedad=0.0, viento_kmh=0.0,
    ))
    assert es_valido is True
    assert motivos == []