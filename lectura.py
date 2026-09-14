"""
Lectura de los datasets de los proveedores.

Responsabilidad única: leer los archivos y devolver los registros
"crudos" (sin transformar), cada uno etiquetado con su origen y
un índice de posición para trazabilidad.
"""
import json
import csv


def leer_proveedor_a(ruta):
    """Lee proveedor_a.json y devuelve una lista de registros crudos."""
    registros = []
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[lectura] Archivo no encontrado: {ruta}")
        return registros
    except json.JSONDecodeError as e:
        print(f"[lectura] JSON inválido en {ruta}: {e}")
        return registros

    for i, r in enumerate(data.get("records", [])):
        registros.append({
            "fuente": "proveedor_a",
            "posicion": i,
            "crudo": r,
        })
    return registros


def leer_proveedor_b(ruta):
    """Lee proveedor_b.csv y devuelve una lista de registros crudos."""
    registros = []
    try:
        with open(ruta, encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f, delimiter=";")
            for i, fila in enumerate(lector):
                registros.append({
                    "fuente": "proveedor_b",
                    "posicion": i,
                    "crudo": fila,
                })
    except FileNotFoundError:
        print(f"[lectura] Archivo no encontrado: {ruta}")
    except csv.Error as e:
        print(f"[lectura] Error leyendo CSV {ruta}: {e}")
    return registros


def leer_todos(ruta_json, ruta_csv):
    """Une los registros de ambos proveedores en una sola lista."""
    return leer_proveedor_a(ruta_json) + leer_proveedor_b(ruta_csv)