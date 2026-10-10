# API IoT - Taller 2

API para adquisición, validación y consulta de datos IoT con FastAPI, MQTT y PostgreSQL.

## 1. Información General

| Campo | Valor |
|---|---|
| Nombre del proyecto | API IoT - Taller 2 |
| Integrantes |Kevin Berrio Carmona (GitHub: `KBerrioC`) |
| Asignatura | Aplicaciones y Servicios Web |
| Programa | Tecnología en Desarrollo de Software |
| Fecha | 10 de octubre de 2026 |
| Sensor asignado | `AQ-005` (id 32 en la base de datos) - "Partículas en laboratorio", categoría AIRE, ubicación "Laboratorio de materiales" |
| Tópico MQTT utilizado | `iot/sensors/AQ-005/data` |
| Broker MQTT | `emqx.coriotlab.co:1883` |
| Repositorio | https://github.com/KBerrioC/apps_services_2/tree/taller-2 |

## 2. Descripción del Sistema

### Problema resuelto

Un sensor de calidad del aire publica mediciones periódicas por MQTT. La aplicación se suscribe a su tópico, valida cada mensaje, guarda en PostgreSQL únicamente los mensajes válidos y expone endpoints REST para consultar sensores, magnitudes y mediciones.

### Arquitectura implementada

```
Sensor AQ-005 --MQTT--> Broker EMQX --> app/mqtt/client.py (suscriptor)
                                              |
                       Pydantic (estructura, tipos, timestamp)
                                              |
                       SQLAlchemy ORM (sensor, estado, magnitud, unidad, rango)
                                              |
                                        PostgreSQL (appdb)
                                              |
                       FastAPI (app/main.py) <-- endpoints GET --> Cliente HTTP
```

Hay dos procesos independientes:

- `run_mqtt.py`: consumidor MQTT que valida y guarda los datos.
- `uvicorn app.main:app`: API REST que consulta los datos guardados.

El consumidor MQTT procesa cada mensaje en este orden y lo rechaza en el primer fallo, sin guardar nada:

1. JSON válido.
2. Estructura, tipos y timestamp (Pydantic).
3. Sensor existente, igual al asignado y activo (ORM).
4. Magnitud existente para el sensor, unidad correcta y valor dentro del rango (ORM y lógica de negocio).
5. Si todas las magnitudes del payload son válidas, se guardan como registros independientes con el mismo `timestamp_utc`. Si alguna falla, no se guarda ninguna.

Los errores del procesamiento MQTT se manejan internamente y quedan en el log de ejecución (`logs/mqtt_consumer.log`). Los códigos HTTP se evalúan solo en los endpoints FastAPI.

### Magnitudes y unidades recibidas

Catálogo del sensor AQ-005 consultado en PostgreSQL:

| sensor_magnitud_id | Magnitud | Unidad | Valor mínimo | Valor máximo |
|---|---|---|---|---|
| 84 | `pm10` | ug/m3 | 0 | 300 |
| 85 | `pm2_5` | ug/m3 | 0 | 200 |
| 86 | `pm1_0` | ug/m3 | 0 | 100 |

Tipos de datos: `sensor_id` texto, `timestamp` texto ISO 8601 en UTC (formato `AAAA-MM-DDTHH:MM:SSZ`), `value` decimal, `unit` texto. El sensor publica un mensaje cada 5 segundos.

### Payload real del sensor

```json
{
  "sensor_id": "AQ-005",
  "timestamp": "2026-10-10T00:01:05Z",
  "measurements": {
    "pm1_0":  { "value": 26.34, "unit": "ug/m3" },
    "pm2_5":  { "value": 14.67, "unit": "ug/m3" },
    "pm10":   { "value": 74.71, "unit": "ug/m3" }
  }
}
```

El campo `sensor_id` del mensaje corresponde a la columna `codigo` de la tabla `sensores`, no a su clave primaria `id`.

### Recolección de datos

Se recolectaron datos durante aproximadamente 27 minutos (de las 19:55 a las 20:22, hora de Colombia, el 9 de octubre de 2026), por encima del mínimo de 20 minutos. Resultado: **900 mediciones guardadas** (300 mensajes válidos con 3 magnitudes cada uno). Durante la recolección el servicio publicó además mensajes inválidos de forma intencional (valores fuera de rango, timestamp inválido, magnitud inexistente y unidad incorrecta). Todos fueron rechazados y no se guardaron.

## 3. Configuración del Entorno

Requisitos: Python 3.10 o superior (se usó Python 3.14), Git y acceso al broker y a PostgreSQL.

```powershell
git clone https://github.com/KBerrioC/apps_services_2.git
cd apps_services_2
git checkout taller-2
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` incluye `paho-mqtt`, `python-dotenv`, `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `pydantic` y `tzdata` (zona horaria de Colombia en Windows).

### Variables de entorno

Se definen en un archivo `.env` en la raíz (copiar de `.env.example`). El archivo `.env` está en `.gitignore` y no se sube al repositorio. Los valores se obtienen de la tarea de Teams.

| Variable | Descripción |
|---|---|
| `MQTT_BROKER` | Host del broker MQTT |
| `MQTT_PORT` | Puerto del broker |
| `MQTT_TOPIC` | Tópico del sensor asignado (`iot/sensors/AQ-005/data`) |
| `MQTT_USERNAME` | Usuario MQTT (vacío si el broker no lo exige) |
| `MQTT_PASSWORD` | Contraseña MQTT (vacía si el broker no la exige) |
| `MQTT_KEEPALIVE` | Keepalive en segundos |
| `DB_HOST` | Host de PostgreSQL |
| `DB_PORT` | Puerto de PostgreSQL |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de PostgreSQL |
| `DB_PASSWORD` | Contraseña de PostgreSQL |

### Ejecución

```powershell
python run_mqtt.py                  # consumidor MQTT (terminal 1)
uvicorn app.main:app --reload       # API REST (terminal 2)
```

Documentación interactiva de la API: http://127.0.0.1:8000/docs

## 4. Base de Datos

### Conexión

La conexión se crea en `app/database/connection.py` con SQLAlchemy y el driver `psycopg2`. Los parámetros se leen de variables de entorno. La función `get_db` entrega una sesión por petición y la cierra al terminar.

### Tablas utilizadas

El catálogo (`sensores`, `sensor_magnitudes`) lo suministra el docente. La aplicación solo lo consulta: no crea, modifica ni elimina sensores ni magnitudes, y no se usa `create_all`. La única tabla en la que la aplicación escribe es `mediciones`.

| Tabla | Descripción | Uso en la app |
|---|---|---|
| `sensores` | Sensores registrados (`id`, `codigo`, `nombre`, `categoria`, `ubicacion`, `activo`, `fecha_registro`) | Solo lectura |
| `sensor_magnitudes` | Magnitudes de cada sensor con su unidad y rango (`id`, `sensor_id`, `magnitud`, `unidad`, `valor_minimo`, `valor_maximo`) | Solo lectura |
| `mediciones` | Mediciones válidas (`id`, `sensor_magnitud_id`, `valor`, `timestamp_utc`, `fecha_recepcion`) | Lectura y escritura |

### Relaciones implementadas (claves foráneas)

Verificadas con `information_schema` en `evidencias/registro_postgresql.txt`:

- `sensor_magnitudes.sensor_id` -> `sensores.id`
- `mediciones.sensor_magnitud_id` -> `sensor_magnitudes.id`

En los modelos ORM se implementan con `ForeignKey` y `relationship` (`Sensor.magnitudes`, `SensorMagnitud.sensor`, `SensorMagnitud.mediciones`, `Medicion.sensor_magnitud`).

### Correspondencia con `data-model.md`

Cada tabla descrita en `data-model.md` tiene su clase ORM en `app/models/`, con los mismos nombres de columnas, tipos y relaciones: `sensor.py` (`sensores`), `sensor_magnitud.py` (`sensor_magnitudes`) y `medicion.py` (`mediciones`).

El timestamp recibido por MQTT está en UTC y se guarda en `mediciones.timestamp_utc` conservando la referencia UTC. En las respuestas GET se convierte a hora de Colombia (`America/Bogota`) con formato `AAAA-MM-DD HH:MM:SS`.

## 5. Organización del Código

```
app/
├── main.py                 # aplicación FastAPI y registro de routers
├── schemas/                # esquemas Pydantic
│   ├── sensor.py
│   ├── sensor_magnitud.py
│   └── medicion.py
├── models/                 # modelos SQLAlchemy ORM
│   ├── sensor.py
│   ├── sensor_magnitud.py
│   └── medicion.py
├── crud/                   # consultas y escritura en la base
│   ├── sensor.py
│   ├── sensor_magnitud.py
│   └── medicion.py
├── api/                    # endpoints HTTP
│   ├── sensor.py
│   ├── sensor_magnitud.py
│   └── medicion.py
├── mqtt/
│   └── client.py           # suscriptor MQTT y validación de mensajes
└── database/
    └── connection.py       # engine, sesión y Base
run_mqtt.py                 # arranca el consumidor y escribe logs/mqtt_consumer.log
```

| Carpeta | Función |
|---|---|
| `schemas/` | Validan con Pydantic la estructura del mensaje MQTT (campos obligatorios, tipos y formato del timestamp) y definen la forma de las respuestas de la API, incluida la conversión a hora de Colombia. |
| `models/` | Clases SQLAlchemy que representan las tablas de PostgreSQL, con claves primarias, foráneas y relaciones. |
| `crud/` | Operaciones sobre la base de datos. Cada módulo implementa solo las operaciones autorizadas: lectura para el catálogo y lectura más creación para las mediciones. |
| `api/` | Endpoints FastAPI, manejo de códigos HTTP (200, 400, 404, 422) y parámetros de consulta. |
| `mqtt/` | Cliente MQTT: conexión, suscripción y proceso de validación (`procesar_mensaje`). |
| `database/` | Conexión a PostgreSQL, sesión (`get_db`) y clase base declarativa. |

## 6. Endpoints Implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Estado de la API |
| GET | `/sensores` | Lista todos los sensores |
| GET | `/sensores/{id}` | Consulta un sensor por su id (404 si no existe) |
| GET | `/sensores/por-codigo/{codigo}` | Consulta un sensor por su código (por ejemplo `AQ-005`) |
| GET | `/sensores/{id}/magnitudes` | Lista las magnitudes de un sensor |
| GET | `/sensor-magnitudes/{id}` | Consulta una relación sensor-magnitud |
| GET | `/mediciones/{id}` | Consulta una medición por su id (404 si no existe) |
| GET | `/sensores/{id}/mediciones` | Histórico de un sensor. Filtros combinables: `magnitud`, `desde`, `hasta`, `limit`. Devuelve 400 si `desde` > `hasta` |
| GET | `/sensores/{id}/ultima-medicion` | Todas las magnitudes del instante más reciente |

Los parámetros `desde` y `hasta` se interpretan en hora de Colombia cuando no incluyen zona horaria. El parámetro `limit` devuelve las últimas N mediciones (1 a 1000).

## 7. Evidencias de Funcionamiento

Todas las evidencias están en la carpeta [`evidencias/`](evidencias/). Para cada una se indica la entrada, el resultado, el código HTTP cuando aplica, si el registro se almacenó o se rechazó, el archivo y la función donde está la lógica relacionada y una breve explicación.

Archivos de evidencia: `01_recepcion_mqtt.png`, `02_registro_postgresql.png`, `08_consulta_por_id.png`, `09_id_inexistente.png`, `10_historico.png`, `11_rango_fechas.png`, `12_rango_400.png`, `13_validacion_422.png`, `14_ultima_medicion.png`, `15_1_ultimas_n.png`, `15_2_ultimas_n.png`, `16_filtro_magnitud.png`, `aceptados_mqtt.txt`, `rechazos_mqtt.txt`, `rechazos_test.txt` y `registro_postgresql.txt`.

### Pruebas del procesamiento MQTT

Los errores MQTT no devuelven códigos HTTP: se rechazan internamente, se registran en el log y no se guardan en la base.

#### Prueba 1: Recepción MQTT
- **Datos de entrada:** suscripción a `iot/sensors/AQ-005/data` ejecutando `mqtt_example.py`.
- **Resultado obtenido:** mensajes JSON recibidos cada 5 segundos con las tres magnitudes.
- **Código HTTP:** no aplica.
- **Registro:** no se guarda nada; solo se leen mensajes del tópico.
- **Evidencia:** `evidencias/01_recepcion_mqtt.png`
- **Archivo y función:** `mqtt_example.py`; `app/mqtt/client.py` (`create_client`, `on_connect`, `on_message`).
- **Explicación:** el broker entrega al suscriptor cada mensaje que publica el sensor. Esto confirma que la conexión funciona y que el sensor asignado está publicando.

#### Prueba 2: Medición válida
- **Datos de entrada:** mensaje válido de AQ-005 con `pm1_0`, `pm2_5` y `pm10`.
- **Resultado obtenido:** 3 registros guardados en `mediciones` (uno por magnitud) con el mismo `timestamp_utc`. Total acumulado: 900 mediciones.
- **Código HTTP:** no aplica.
- **Registro:** almacenado.
- **Evidencia:** `evidencias/02_registro_postgresql.png`, `evidencias/registro_postgresql.txt`, `evidencias/aceptados_mqtt.txt`.
- **Archivo y función:** `app/mqtt/client.py` (`procesar_mensaje`); `app/crud/medicion.py` (`create_mediciones`).
- **Explicación:** cuando el mensaje supera todas las validaciones, `create_mediciones` inserta una fila por magnitud en una sola transacción. Si algo falla, se hace rollback y no se guarda ninguna.

#### Prueba 3: Sensor inexistente
- **Datos de entrada:** `sensor_id` = `ZZ-999`. También se probó con un sensor de otro grupo.
- **Resultado obtenido:** `sensor inexistente: ZZ-999`.
- **Código HTTP:** no aplica.
- **Registro:** rechazado, no se guardó.
- **Evidencia:** `evidencias/rechazos_test.txt`
- **Archivo y función:** `app/mqtt/client.py` (`procesar_mensaje`); `app/crud/sensor.py` (`get_sensor_por_codigo`).
- **Explicación:** el código recibido se busca en la tabla `sensores`. Si no existe, o si no es el sensor asignado al grupo, el mensaje se descarta.

#### Prueba 4: Unidad incorrecta
- **Datos de entrada:** `unit` = `mg/m3` (prueba) e `INVALID_UNIT` (mensajes reales del sensor).
- **Resultado obtenido:** `unidad incorrecta en 'pm10': recibida 'mg/m3', esperada 'ug/m3'`.
- **Código HTTP:** no aplica.
- **Registro:** rechazado, no se guardó.
- **Evidencia:** `evidencias/rechazos_test.txt`, `evidencias/rechazos_mqtt.txt`.
- **Archivo y función:** `app/mqtt/client.py` (`procesar_mensaje`).
- **Explicación:** la unidad recibida se compara con la unidad registrada en `sensor_magnitudes`. Si no coincide, se rechaza el mensaje completo.

#### Prueba 5: Tipo de dato incorrecto
- **Datos de entrada:** `value` = `"abc"` en la magnitud `pm10`.
- **Resultado obtenido:** `measurements.pm10.value: Input should be a valid number`.
- **Código HTTP:** no aplica.
- **Registro:** rechazado, no se guardó.
- **Evidencia:** `evidencias/rechazos_test.txt`
- **Archivo y función:** `app/schemas/medicion.py` (`MensajeMQTT`, `MagnitudPayload`).
- **Explicación:** Pydantic valida que `value` sea numérico (decimal estricto, sin texto, NaN ni infinito) antes de consultar la base de datos.

#### Prueba 6: Magnitud incorrecta
- **Datos de entrada:** magnitud `temperature`, que no existe para AQ-005.
- **Resultado obtenido:** `magnitud 'temperature' no existe para el sensor AQ-005`. También ocurrió en mensajes reales del sensor.
- **Código HTTP:** no aplica.
- **Registro:** rechazado, no se guardó.
- **Evidencia:** `evidencias/rechazos_test.txt`, `evidencias/rechazos_mqtt.txt`.
- **Archivo y función:** `app/mqtt/client.py` (`procesar_mensaje`); `app/crud/sensor_magnitud.py` (`get_magnitudes_por_sensor`).
- **Explicación:** las magnitudes recibidas se contrastan con el catálogo de magnitudes del sensor. Una magnitud que no esté en el catálogo invalida todo el mensaje.

#### Prueba 7: Timestamp inválido
- **Datos de entrada:** `timestamp` = `ayer` (prueba) y `not-a-timestamp` (mensaje real del sensor).
- **Resultado obtenido:** `el timestamp tiene un formato inválido`.
- **Código HTTP:** no aplica.
- **Registro:** rechazado, no se guardó.
- **Evidencia:** `evidencias/rechazos_test.txt`, `evidencias/rechazos_mqtt.txt`.
- **Archivo y función:** `app/schemas/medicion.py` (`MensajeMQTT.validar_timestamp`).
- **Explicación:** el timestamp debe ser un texto ISO 8601 con zona horaria. Se convierte a UTC y, si no se puede interpretar o no trae zona, se rechaza el mensaje.

Además se probaron valores fuera de rango (por ejemplo `999999.0` en `pm2_5` y `500.0` en `pm1_0`, cuyo máximo es 100) y un payload con una magnitud válida y otra con unidad incorrecta. En ambos casos se rechazó el mensaje completo, sin guardar ninguna de sus magnitudes. En la prueba `test_rechazos.py` el conteo de mediciones fue idéntico antes y después, lo que demuestra que no se guardó ningún dato inválido.

### Pruebas de la API HTTP

#### Prueba 8: Consulta por ID existente
- **Datos de entrada:** `GET /sensores/32`
- **Resultado obtenido:** datos del sensor `AQ-005` (activo, categoría AIRE).
- **Código HTTP:** 200
- **Evidencia:** `evidencias/08_consulta_por_id.png`
- **Archivo y función:** `app/api/sensor.py` (`obtener_sensor`).
- **Explicación:** el endpoint busca el sensor por su clave primaria y devuelve el objeto serializado con el esquema `SensorOut`.

#### Prueba 9: Consulta por ID inexistente
- **Datos de entrada:** `GET /sensores/9999`
- **Resultado obtenido:** `{"detail": "Sensor 9999 no encontrado"}`
- **Código HTTP:** 404
- **Evidencia:** `evidencias/09_id_inexistente.png`
- **Archivo y función:** `app/api/sensor.py` (`obtener_sensor`).
- **Explicación:** si el CRUD no encuentra el sensor, el endpoint lanza `HTTPException` con código 404.

#### Prueba 10: Consulta histórica
- **Datos de entrada:** `GET /sensores/32/mediciones?limit=50`
- **Resultado obtenido:** 50 registros, del más reciente (`2026-10-09 20:22:25`) al más antiguo, con las tres magnitudes mezcladas.
- **Código HTTP:** 200
- **Evidencia:** `evidencias/10_historico.png`
- **Archivo y función:** `app/api/medicion.py` (`listar_mediciones`); `app/crud/medicion.py` (`get_mediciones`).
- **Explicación:** la consulta une `mediciones` con `sensor_magnitudes`, filtra por sensor y ordena por `timestamp_utc` descendente.

#### Prueba 11: Consulta por rango de fechas
- **Datos de entrada:** `GET /sensores/32/mediciones?desde=2026-10-09T20:20:00&hasta=2026-10-09T20:22:00`
- **Resultado obtenido:** solo registros entre las 20:20:00 y las 20:22:00 (hora de Colombia).
- **Código HTTP:** 200
- **Evidencia:** `evidencias/11_rango_fechas.png`
- **Archivo y función:** `app/api/medicion.py` (`listar_mediciones`, `_a_utc`); `app/crud/medicion.py` (`get_mediciones`).
- **Explicación:** las fechas sin zona se interpretan como hora de Colombia y se convierten a UTC para filtrar `timestamp_utc`, que se guarda en UTC.

#### Prueba 12: Rango con `desde` posterior a `hasta`
- **Datos de entrada:** `GET /sensores/32/mediciones?desde=2026-10-10T12:00:00&hasta=2026-10-09T12:00:00`
- **Resultado obtenido:** `El parámetro 'desde' no puede ser posterior a 'hasta'`.
- **Código HTTP:** 400
- **Evidencia:** `evidencias/12_rango_400.png`
- **Archivo y función:** `app/api/medicion.py` (`listar_mediciones`).
- **Explicación:** antes de consultar la base se comparan ambas fechas en UTC. Si el rango es incoherente, se responde 400 (error del cliente).

#### Prueba 13: Validación HTTP incorrecta
- **Datos de entrada:** `GET /sensores/abc`
- **Resultado obtenido:** error `int_parsing`: el valor de `sensor_id` no es un entero.
- **Código HTTP:** 422
- **Evidencia:** `evidencias/13_validacion_422.png`
- **Archivo y función:** `app/api/sensor.py` (`obtener_sensor`, parámetro tipado `sensor_id: int`).
- **Explicación:** FastAPI valida automáticamente el tipo del parámetro de ruta y responde 422 sin ejecutar la función. La petición se hizo con `curl.exe -i`, porque Swagger UI no deja enviar texto en un campo entero.

#### Prueba 14: Última medición
- **Datos de entrada:** `GET /sensores/32/ultima-medicion`
- **Resultado obtenido:** las 3 magnitudes del instante más reciente, `2026-10-09 20:22:25` (ids 45241, 45240 y 45239).
- **Código HTTP:** 200
- **Evidencia:** `evidencias/14_ultima_medicion.png`
- **Archivo y función:** `app/api/medicion.py` (`ultima_medicion`); `app/crud/medicion.py` (`get_ultima_medicion`).
- **Explicación:** se obtiene la medición con el `timestamp_utc` más reciente y luego todas las filas de ese mismo instante, para devolver las tres magnitudes. Si el sensor no tiene datos, responde 404.

#### Prueba 15: Últimas N mediciones
- **Datos de entrada:** `GET /sensores/32/mediciones?limit=5`
- **Resultado obtenido:** exactamente 5 registros, los más recientes.
- **Código HTTP:** 200
- **Evidencia:** `evidencias/15_1_ultimas_n.png`, `evidencias/15_2_ultimas_n.png`.
- **Archivo y función:** `app/api/medicion.py` (`listar_mediciones`, parámetro `limit`); `app/crud/medicion.py` (`get_mediciones`).
- **Explicación:** con el orden descendente por fecha, `limit` recorta la consulta a las últimas N filas. Está validado entre 1 y 1000.

#### Prueba 16: Filtro por magnitud
- **Datos de entrada:** `GET /sensores/32/mediciones?magnitud=pm10&limit=5`
- **Resultado obtenido:** 5 registros, todos `pm10` (ids 45241, 45232, 45223, 45214 y 45205).
- **Código HTTP:** 200
- **Evidencia:** `evidencias/16_filtro_magnitud.png`
- **Archivo y función:** `app/crud/medicion.py` (`get_mediciones`, filtro por `SensorMagnitud.magnitud`).
- **Explicación:** el parámetro `magnitud` agrega una condición sobre la tabla `sensor_magnitudes`, y se puede combinar con `desde`, `hasta` y `limit`.

### Pruebas de estructura

#### Prueba 17: Claves foráneas
- **Resultado obtenido:** `mediciones.sensor_magnitud_id` apunta a `sensor_magnitudes.id`, y `sensor_magnitudes.sensor_id` apunta a `sensores.id`.
- **Evidencia:** `evidencias/02_registro_postgresql.png`, `evidencias/registro_postgresql.txt`.
- **Archivo y función:** `app/models/medicion.py`, `app/models/sensor_magnitud.py` (`ForeignKey` y `relationship`).
- **Explicación:** las relaciones se consultaron en `information_schema` y se reflejan en los modelos ORM. Así cada medición queda ligada a una magnitud de un sensor concreto.

#### Prueba 18: Separación de responsabilidades
- **Resultado obtenido:** cada tabla tiene su archivo en `schemas/`, `models/`, `crud/` y `api/`; el cliente MQTT está en `mqtt/` y la conexión en `database/`.
- **Evidencia:** estructura del repositorio (sección 5).
- **Archivo y función:** carpeta `app/`.
- **Explicación:** la API no accede a la base directamente, sino a través de `crud/`. Los modelos, los esquemas de validación y los endpoints están en capas separadas, y el consumidor MQTT reutiliza las mismas capas.

## 8. Control de Versiones

- Repositorio: https://github.com/KBerrioC/apps_services_2/tree/taller-2
- Rama de trabajo: `taller-2`
- Evidencia de commits: https://github.com/KBerrioC/apps_services_2/commits/taller-2

### Aporte de cada integrante

| Integrante | Usuario de GitHub | Aporte |
|---|---|---|
|Kevin Berrio Carmona | `KBerrioC` | Desarrollo completo del taller: configuración del entorno, modelos ORM, esquemas Pydantic, capa CRUD, cliente MQTT con validaciones, endpoints FastAPI, pruebas, evidencias y documentación |

## 9. Conclusiones

### Principales aprendizajes

- Se integró un suscriptor MQTT con una API FastAPI sobre una misma base de datos PostgreSQL.
- La validación en dos etapas (estructura con Pydantic y reglas de negocio con el ORM) permite rechazar mensajes inválidos antes de guardarlos.
- Guardar las magnitudes de un mismo payload en una sola transacción garantiza que un mensaje se guarda completo o no se guarda.
- Se guarda la hora en UTC y se convierte a hora de Colombia solo al responder, lo que evita ambigüedades.

### Dificultades encontradas y soluciones aplicadas

| Dificultad | Solución |
|---|---|
| El fork del repositorio del curso no tenía la rama `taller-2`. | Se clonó el repositorio original, se agregó el fork como `origin` y se subió la rama con `git push`. |
| `app/models/__init__.py` quedó vacío y la importación de los modelos fallaba. | Se escribió el archivo desde la terminal y se activó el autoguardado del editor. |
| Zona horaria `America/Bogota` no disponible en Windows. | Se instaló el paquete `tzdata`. |
| Swagger UI no permite enviar un valor no numérico en un parámetro entero, por lo que no se podía mostrar el 422 desde `/docs`. | Se hizo la petición directamente con `curl.exe -i`. |
| El servicio publica mensajes inválidos a propósito. | El procesamiento los rechaza y los registra en `logs/mqtt_consumer.log`. Las líneas relevantes se guardaron en `evidencias/`. |
