"""
Punto de entrada del integrador.

Flujo: lee -> normaliza -> valida -> guarda normalizadas.json ->
envía los válidos a la API -> consulta lo registrado -> guarda
reporte.json.

Ejecutar con: python integrador.py
"""
from lectura import leer_todos
from normalizacion import normalizar_lote
from validacion import validar_lote
from cliente_api import enviar_medicion, consultar_mediciones
from reporte import construir_normalizadas, construir_reporte, guardar_json

# --- Configuración: ajustar antes de la entrega final ---
URL_BASE = "https://appsweb.quantaiot.co"
EQUIPO = "EQUIPO-07-APPSWEB"  # <-- reemplazar por el identificador real

RUTA_PROVEEDOR_A = "datos/proveedor_a.json"
RUTA_PROVEEDOR_B = "datos/proveedor_b.csv"
RUTA_NORMALIZADAS = "salida/normalizadas.json"
RUTA_REPORTE = "salida/reporte.json"


def main():
    print("=== Integrador de mediciones meteorológicas ===")

    print("\n[1/5] Leyendo datasets...")
    registros = leer_todos(RUTA_PROVEEDOR_A, RUTA_PROVEEDOR_B)
    print(f"  Registros leídos: {len(registros)}")

    print("\n[2/5] Normalizando...")
    normalizados, errores_normalizacion = normalizar_lote(registros)
    print(f"  Normalizados: {len(normalizados)} | Errores de normalización: {len(errores_normalizacion)}")

    print("\n[3/5] Validando localmente...")
    validos, rechazados_local = validar_lote(normalizados)
    print(f"  Válidos: {len(validos)} | Rechazados localmente: {len(rechazados_local)}")

    normalizadas_salida = construir_normalizadas(validos, rechazados_local)
    guardar_json(RUTA_NORMALIZADAS, normalizadas_salida)
    print(f"  Guardado: {RUTA_NORMALIZADAS}")

    print(f"\n[4/5] Enviando {len(validos)} mediciones válidas a la API...")
    resultados_envio = []
    for i, medicion in enumerate(validos, start=1):
        try:
            resultado = enviar_medicion(URL_BASE, EQUIPO, medicion)
        except Exception as e:
            # red de seguridad final: nada debe tumbar el programa
            resultado = {"resultado": "error_comunicacion", "codigo_http": None,
                         "intentos": 0, "detalle": f"Excepción no controlada: {e}"}
        resultado["id_trazabilidad"] = medicion["id_trazabilidad"]
        resultados_envio.append(resultado)

        if i % 50 == 0 or i == len(validos):
            print(f"  Progreso: {i}/{len(validos)}")

    aceptados = sum(1 for r in resultados_envio if r["resultado"] == "aceptado")
    rechazados_api = sum(1 for r in resultados_envio if r["resultado"] == "rechazado_api")
    errores_com = sum(1 for r in resultados_envio if r["resultado"] == "error_comunicacion")
    print(f"  Aceptados: {aceptados} | Rechazados por API: {rechazados_api} | Errores de comunicación: {errores_com}")

    print("\n[5/5] Consultando resultados almacenados...")
    try:
        consulta = consultar_mediciones(URL_BASE, EQUIPO)
    except Exception as e:
        consulta = {"error": f"Excepción no controlada en consulta: {e}"}
    print(f"  Consulta: {consulta if consulta else 'sin respuesta'}")

    reporte = construir_reporte(len(registros), errores_normalizacion, validos,
                                 rechazados_local, resultados_envio, consulta)
    guardar_json(RUTA_REPORTE, reporte)
    print(f"\nGuardado: {RUTA_REPORTE}")
    print("\n=== Resumen final ===")
    for k, v in reporte["resumen"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
    