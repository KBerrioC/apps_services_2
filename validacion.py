"""
Validación local de registros ya normalizados, según las reglas
de negocio del contrato institucional (CONTRATO_API.md).

Un registro normalizado puede seguir siendo inválido: por ejemplo,
una latitud de 95 es un número válido, pero viola la regla
"-90 a 90" del contrato.
"""

ORIGENES_PERMITIDOS = {"proveedor_a", "proveedor_b"}


def validar_registro(normalizado):
    """
    Devuelve (es_valido, motivos):
      es_valido: True si pasa todas las reglas
      motivos: lista de strings con cada regla incumplida (vacía si es válido)
    """
    motivos = []

    if not normalizado["ciudad"] or not normalizado["ciudad"].strip():
        motivos.append("ciudad vacía")

    if not normalizado["pais"] or not normalizado["pais"].strip():
        motivos.append("pais vacío")

    if not (-90 <= normalizado["latitud"] <= 90):
        motivos.append(f"latitud fuera de rango: {normalizado['latitud']}")

    if not (-180 <= normalizado["longitud"] <= 180):
        motivos.append(f"longitud fuera de rango: {normalizado['longitud']}")

    if not (0 <= normalizado["humedad"] <= 100):
        motivos.append(f"humedad fuera de rango: {normalizado['humedad']}")

    if normalizado["viento_kmh"] < 0:
        motivos.append(f"viento_kmh negativo: {normalizado['viento_kmh']}")

    if normalizado["origen"] not in ORIGENES_PERMITIDOS:
        motivos.append(f"origen no permitido: {normalizado['origen']}")

    return (len(motivos) == 0), motivos


def validar_lote(normalizados):
    """
    Separa los normalizados en válidos y rechazados localmente.
    Devuelve (validos, rechazados) donde rechazados es una lista
    de dicts {registro, motivos}.
    """
    validos = []
    rechazados = []
    for n in normalizados:
        es_valido, motivos = validar_registro(n)
        if es_valido:
            validos.append(n)
        else:
            rechazados.append({"registro": n, "motivos": motivos})
    return validos, rechazados
