from sqlalchemy import text

from app.database.connection import engine

with engine.connect() as conn:
    print("== Últimas 6 mediciones guardadas de AQ-005 ==")
    filas = conn.execute(text("""
        select m.id, s.codigo, sm.magnitud, m.valor, sm.unidad,
               m.timestamp_utc, m.fecha_recepcion
        from mediciones m
        join sensor_magnitudes sm on sm.id = m.sensor_magnitud_id
        join sensores s on s.id = sm.sensor_id
        where s.codigo = 'AQ-005'
        order by m.timestamp_utc desc, m.id desc
        limit 6
    """))
    for fila in filas:
        print(fila)

    total = conn.execute(text("""
        select count(*)
        from mediciones m
        join sensor_magnitudes sm on sm.id = m.sensor_magnitud_id
        where sm.sensor_id = 32
    """)).scalar()
    print(f"\n== Total de mediciones de AQ-005: {total} ==")

    print("\n== Claves foráneas ==")
    fks = conn.execute(text("""
        select tc.table_name, kcu.column_name,
               ccu.table_name as tabla_referenciada,
               ccu.column_name as columna_referenciada
        from information_schema.table_constraints tc
        join information_schema.key_column_usage kcu
          on tc.constraint_name = kcu.constraint_name
         and tc.table_schema = kcu.table_schema
        join information_schema.constraint_column_usage ccu
          on ccu.constraint_name = tc.constraint_name
         and ccu.table_schema = tc.table_schema
        where tc.constraint_type = 'FOREIGN KEY'
          and tc.table_name in ('sensor_magnitudes', 'mediciones')
        order by tc.table_name
    """))
    for fila in fks:
        print(fila)