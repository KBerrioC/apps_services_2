"""
Cliente HTTP para la API institucional.

Responsabilidad: enviar una medición (POST) con reintentos
controlados, interpretar la respuesta, y consultar (GET) lo
almacenado. Nunca deja que una excepción de red tumbe el programa.
"""
import requests

MAX_INTENTOS = 3
TIMEOUT_SEGUNDOS = 10


def _construir_body(medicion):
    """Solo los campos que exige el contrato, nada de trazabilidad interna."""
    return {
        "ciudad": medicion["ciudad"],
        "pais": medicion["pais"],
        "latitud": medicion["latitud"],
        "longitud": medicion["longitud"],
        "temperatura_c": medicion["temperatura_c"],
        "humedad": medicion["humedad"],
        "viento_kmh": medicion["viento_kmh"],
        "fecha_hora": medicion["fecha_hora"],
        "origen": medicion["origen"],
    }


def _parsear_respuesta(resp):
    """Intenta leer JSON; si no es JSON válido, devuelve el texto crudo."""
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}


def enviar_medicion(url_base, equipo, medicion, sesion=None):
    """
    Envía una medición con hasta MAX_INTENTOS intentos.
    Devuelve un dict:
      {"resultado": "aceptado"|"rechazado_api"|"error_comunicacion",
       "codigo_http": int|None, "intentos": int, "detalle": ...}
    """
    sesion = sesion or requests
    url = f"{url_base.rstrip('/')}/api/v1/mediciones"
    headers = {"Content-Type": "application/json", "X-Equipo": equipo}
    body = _construir_body(medicion)

    for intento in range(1, MAX_INTENTOS + 1):
        try:
            resp = sesion.post(url, json=body, headers=headers, timeout=TIMEOUT_SEGUNDOS)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if intento == MAX_INTENTOS:
                return {"resultado": "error_comunicacion", "codigo_http": None,
                        "intentos": intento, "detalle": f"{type(e).__name__}: {e}"}
            continue  # reintenta

        if resp.status_code == 201:
            return {"resultado": "aceptado", "codigo_http": 201,
                     "intentos": intento, "detalle": _parsear_respuesta(resp)}

        if resp.status_code in (400, 409, 422):
            # 4xx: no se reintenta
            return {"resultado": "rechazado_api", "codigo_http": resp.status_code,
                     "intentos": intento, "detalle": _parsear_respuesta(resp)}

        if 500 <= resp.status_code < 600:
            if intento == MAX_INTENTOS:
                return {"resultado": "error_comunicacion", "codigo_http": resp.status_code,
                        "intentos": intento, "detalle": _parsear_respuesta(resp)}
            continue  # reintenta

        # código HTTP no contemplado explícitamente por el contrato
        return {"resultado": "rechazado_api", "codigo_http": resp.status_code,
                "intentos": intento, "detalle": _parsear_respuesta(resp)}

    # no debería llegar aquí, pero por seguridad:
    return {"resultado": "error_comunicacion", "codigo_http": None,
            "intentos": MAX_INTENTOS, "detalle": "Agotados los intentos"}


def consultar_mediciones(url_base, equipo, sesion=None):
    """
    GET /api/v1/mediciones?equipo=<equipo>
    Devuelve el JSON de respuesta, o None si hubo error de comunicación.
    """
    sesion = sesion or requests
    url = f"{url_base.rstrip('/')}/api/v1/mediciones"
    try:
        resp = sesion.get(url, params={"equipo": equipo}, timeout=TIMEOUT_SEGUNDOS)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print(f"[cliente_api] Error de comunicación en consulta: {e}")
        return None

    if resp.status_code == 200:
        return _parsear_respuesta(resp)

    print(f"[cliente_api] Consulta no exitosa, código {resp.status_code}")
    return _parsear_respuesta(resp)
