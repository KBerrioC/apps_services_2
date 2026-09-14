"""
Genera los archivos de evidencia en salida/:
- normalizadas.json: todos los registros normalizados (válidos y
  rechazados localmente), con su estado.
- reporte.json: conteos y trazabilidad de todo el proceso.
"""
import json
import os


def construir_normalizadas(validos, rechazados):
    """
    Une válidos y rechazados en una sola lista, cada uno con su
    estado de validación local. Este es el contenido de normalizadas.json.
    """
    salida = []
    for v in validos:
        item = dict(v)
        item["validacion_local"] = "valido"
        item["motivos_rechazo_local"] = []
        salida.append(item)
    for r in rechazados:
        item = dict(r["registro"])
        item["validacion_local"] = "rechazado_localmente"
        item["motivos_rechazo_local"] = r["motivos"]
        salida.append(item)
    return salida


def guardar_json(ruta, data):
    """Crea la carpeta si no existe y guarda el JSON con formato legible."""
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def construir_reporte(total_procesados, errores_normalizacion, validos,
                       rechazados_local, resultados_envio, consulta_api):
    """
    Arma el reporte final con los conteos mínimos exigidos por el
    taller (punto 10) y trazabilidad por registro.
    """
    aceptados_api = [r for r in resultados_envio if r["resultado"] == "aceptado"]
    rechazados_api = [r for r in resultados_envio if r["resultado"] == "rechazado_api"]
    errores_comunicacion = [r for r in resultados_envio if r["resultado"] == "error_comunicacion"]

    return {
        "resumen": {
            "procesados": total_procesados,
            "normalizados": len(validos) + len(rechazados_local),
            "errores_normalizacion": len(errores_normalizacion),
            "validos_localmente": len(validos),
            "rechazados_localmente": len(rechazados_local),
            "enviados": len(resultados_envio),
            "aceptados_por_api": len(aceptados_api),
            "rechazados_por_api": len(rechazados_api),
            "errores_comunicacion": len(errores_comunicacion),
        },
        "errores_normalizacion_detalle": errores_normalizacion,
        "rechazados_localmente_detalle": [
            {"id_trazabilidad": r["registro"]["id_trazabilidad"], "motivos": r["motivos"]}
            for r in rechazados_local
        ],
        "envios_detalle": resultados_envio,
        "consulta_api_final": consulta_api,
    }