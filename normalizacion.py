"""
Normalización de registros crudos al contrato institucional.

Cada registro se intenta convertir a:
{ciudad, pais, latitud, longitud, temperatura_c, humedad,
 viento_kmh, fecha_hora, origen, id_trazabilidad}

Si algo no se puede convertir al tipo/formato exigido, es un
error de normalización (no se lanza excepción sin control:
se captura y se reporta).
"""
from datetime import datetime, timezone, timedelta


ZONA_COLOMBIA = timezone(timedelta(hours=-5))


def _f_a_c(temp_f):
    return (float(temp_f) - 32) * 5 / 9


def _ms_a_kmh(vel_ms):
    return float(vel_ms) * 3.6


def _normalizar_a(registro):
    crudo = registro["crudo"]
    id_trazabilidad = crudo.get("provider_record_id") or f"proveedor_a#{registro['posicion']}"

    ciudad = crudo["station"]["city_name"]
    pais = crudo["station"]["country_code"]
    latitud = float(crudo["location"]["lat"])
    longitud = float(crudo["location"]["lon"])
    temperatura_c = _f_a_c(crudo["measurements"]["temperature_f"])
    humedad = float(crudo["measurements"]["relative_humidity"])
    viento_kmh = _ms_a_kmh(crudo["measurements"]["wind_speed_ms"])

    fecha_raw = crudo["observed_at"]
    # valida que sea una fecha ISO 8601 real
    datetime.fromisoformat(fecha_raw)
    fecha_hora = fecha_raw

    return {
        "id_trazabilidad": id_trazabilidad,
        "fuente": "proveedor_a",
        "ciudad": ciudad,
        "pais": pais,
        "latitud": latitud,
        "longitud": longitud,
        "temperatura_c": round(temperatura_c, 2),
        "humedad": humedad,
        "viento_kmh": round(viento_kmh, 2),
        "fecha_hora": fecha_hora,
        "origen": "proveedor_a",
    }


def _normalizar_b(registro):
    crudo = registro["crudo"]
    id_trazabilidad = crudo.get("record_code") or f"proveedor_b#{registro['posicion']}"

    ciudad = crudo["municipality"]
    pais = crudo["country"]
    latitud = float(crudo["latitude_deg"])
    longitud = float(crudo["longitude_deg"])
    temperatura_c = float(crudo["temp_celsius"])
    humedad = float(crudo["humidity_pct"])
    viento_kmh = float(crudo["wind_kmh"])

    fecha_raw = crudo["measurement_time"]
    fecha_dt = datetime.strptime(fecha_raw, "%d/%m/%Y %H:%M").replace(tzinfo=ZONA_COLOMBIA)
    fecha_hora = fecha_dt.isoformat()

    return {
        "id_trazabilidad": id_trazabilidad,
        "fuente": "proveedor_b",
        "ciudad": ciudad,
        "pais": pais,
        "latitud": latitud,
        "longitud": longitud,
        "temperatura_c": round(temperatura_c, 2),
        "humedad": humedad,
        "viento_kmh": round(viento_kmh, 2),
        "fecha_hora": fecha_hora,
        "origen": "proveedor_b",
    }


def normalizar_registro(registro):
    """
    Devuelve (normalizado, None) si se pudo convertir,
    o (None, motivo_error) si hubo error de normalización.
    """
    try:
        if registro["fuente"] == "proveedor_a":
            return _normalizar_a(registro), None
        else:
            return _normalizar_b(registro), None
    except (KeyError, TypeError, ValueError) as e:
        motivo = f"{type(e).__name__}: {e}"
        return None, motivo


def normalizar_lote(registros):
    """
    Procesa una lista de registros crudos.
    Devuelve (normalizados, errores):
      normalizados: lista de dicts ya en formato contrato
      errores: lista de dicts {id, fuente, posicion, motivo}
    """
    normalizados = []
    errores = []
    for r in registros:
        resultado, motivo = normalizar_registro(r)
        if resultado is not None:
            normalizados.append(resultado)
        else:
            errores.append({
                "fuente": r["fuente"],
                "posicion": r["posicion"],
                "motivo": motivo,
            })
    return normalizados, errores