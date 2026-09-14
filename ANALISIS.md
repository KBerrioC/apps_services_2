# ANALISIS.md — Taller 1: Integración de datos entre aplicaciones

## 1. Diferencias entre los contratos de los proveedores

| Aspecto | Proveedor A (JSON) | Proveedor B (CSV) |
|---|---|---|
| Estructura | Anidada (`station.city_name`, `location.lat`, `measurements.temperature_f`, etc.) | Plana, un solo nivel por fila |
| Unidades | Temperatura en °F, viento en m/s, humedad en % | Temperatura en °C, viento en km/h, humedad en % |
| Fecha | ISO 8601 con zona horaria explícita (`-05:00`) | `DD/MM/YYYY HH:MM`, **sin zona horaria** |
| Campo de origen | `source: "weather_provider_a"` (no coincide con el valor que exige el contrato) | `origin_code: "PB"` (tampoco coincide) |
| Trazabilidad | `provider_record_id` | `record_code` |
| Tipos de dato | Ya tipados (número, string) | Todo llega como texto (propio de CSV) |
| Campos ausentes | Algunos registros no traen `observed_at` o `station.country_code` | Algunos registros traen columnas vacías (`;;`) |

Ningún proveedor manda directamente el campo `origen` como lo exige el contrato: siempre se asigna según el archivo de origen, nunca se copia del dato crudo.

## 2. Transformaciones necesarias

- **Renombrado de campos** en ambos proveedores para que coincidan con el contrato (`city_name`→`ciudad`, `municipality`→`ciudad`, etc.)
- **Conversión de unidades** en proveedor A: `temperatura_c = (temperature_f - 32) * 5/9`, `viento_kmh = wind_speed_ms * 3.6`. Proveedor B no requiere conversión de unidad, solo de tipo (texto → número).
- **Aplanado** de la estructura anidada de proveedor A.
- **Parseo de fecha** de proveedor B (`DD/MM/YYYY HH:MM` → ISO 8601).
- **Asignación de zona horaria** en proveedor B: sus fechas no traen offset, y como corresponde a las mismas ciudades colombianas que proveedor A (que sí trae `-05:00`), se asumió hora de Colombia (UTC-5) para completar el formato ISO 8601 que exige el contrato. Este supuesto se detectó justamente porque la API rechazó (422) los primeros envíos de B con el mensaje `"fecha_hora debe incluir zona horaria"`.
- **Asignación constante de `origen`** (`"proveedor_a"` / `"proveedor_b"`) en vez de usar los campos originales (`source`, `origin_code`), que no coinciden con los valores permitidos por el contrato.

## 3. Tipos de errores encontrados antes de enviar

**Errores de normalización** (9 en total — el dato no se pudo convertir al tipo exigido):
- Texto no numérico en un campo numérico (`temperature_f: "N/A"`, `temp_celsius: "error"`)
- Valor nulo (`temperature_f: null`)
- Fecha no parseable (`"09-XX-2026 25:61"`, `"31/13/2026 28:75"` — mes y hora inexistentes)
- Campos obligatorios ausentes por completo (`observed_at`, `country_code`, `humidity_pct` o `measurement_time` vacíos)

**Rechazos locales** (11 en total — el dato se normalizó bien, pero incumple una regla de negocio del contrato):
- Latitud/longitud fuera de rango (`95.245`, `-190.75`, `-94.22`, `188.45`)
- Humedad fuera de 0-100 (`108.4`, `117.5`)
- Viento negativo (`-2.4 km/h`, `-7.4 km/h`)
- Ciudad o país vacíos

## 4. Diferencias entre validación local y validación del servidor

La validación local (rangos, campos no vacíos) **no fue suficiente** para garantizar la aceptación por la API: el servidor aplicó una regla adicional que el contrato no detallaba explícitamente con ese nivel de precisión — exigir que `fecha_hora` incluya zona horaria, devolviendo `422` en los primeros envíos de proveedor B. Esto confirma lo que dice el contrato: *"una medición validada localmente puede ser rechazada por el servidor"*. También se observó `409 Conflicto` al reenviar mediciones que ya existían de una corrida anterior — una regla de negocio (no duplicar) que tampoco es verificable localmente sin consultar antes al servidor.

## 5. Decisión de implementación más importante

Separar cada responsabilidad en su propio módulo (`lectura`, `normalizacion`, `validacion`, `cliente_api`, `reporte`) permitió diagnosticar y corregir el problema de zona horaria de proveedor B **cambiando una sola función**, sin tocar el resto del pipeline ni tener que re-normalizar o re-leer nada. Igual de importante fue diseñar `cliente_api.py` para recibir una `sesion` HTTP inyectable: eso permitió probar toda la lógica de reintentos y códigos de error (201, 4xx, 5xx, timeouts) con pruebas automatizadas rápidas y confiables, sin depender de la disponibilidad de la API real ni gastar envíos en cada corrida de pruebas.

## Evidencia de ejecución real

**Resumen del reporte (`salida/reporte.json`):**

| Métrica | Valor |
|---|---:|
| Procesados | 400 |
| Normalizados | 391 |
| Errores de normalización | 9 |
| Válidos localmente | 380 |
| Rechazados localmente | 11 |
| Enviados | 380 |
| Aceptados por la API (acumulado en 2 corridas) | 380 |
| Rechazados por la API en 2da corrida (409, duplicados de la 1ra corrida) | 190 |
| Errores de comunicación | 0 |

**Caso de error de normalización** (proveedor A, `A-0082`):
```
temperature_f: "N/A"  →  ValueError: could not convert string to float: 'N/A'
```

**Caso de rechazo local** (proveedor A, `A-0031`):
```
latitud: 95.245  →  motivo: "latitud fuera de rango: 95.245"
```

**Respuesta real de la API — aceptación (201):**
```json
{
  "id": 3241,
  "estado": "aceptada",
  "mensaje": "Medición registrada correctamente"
}
```

**Respuesta real de la API — rechazo por regla de negocio (422, proveedor B antes de corregir zona horaria):**
```json
{
  "detail": [{"type": "value_error", "loc": ["body", "fecha_hora"],
              "msg": "Value error, fecha_hora debe incluir zona horaria, por ejemplo Z o -05:00"}]
}
```

**Consulta final vía GET (`/api/v1/mediciones?equipo=EQUIPO-07-APPSWEB`):**
```json
{
  "equipo": "EQUIPO-07-APPSWEB",
  "total": 381
}
```
(380 mediciones del pipeline + 1 medición de prueba manual usada para confirmar la autorización del equipo antes de la corrida completa.)