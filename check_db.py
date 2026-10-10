import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

url = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(url)

with engine.connect() as conn:
    print(conn.execute(text("select version()")).scalar())
    filas = conn.execute(text("""
        select s.id, s.codigo, s.activo,
               m.id, m.magnitud, m.unidad, m.valor_minimo, m.valor_maximo
        from sensores s
        join sensor_magnitudes m on m.sensor_id = s.id
        where s.codigo = 'AQ-005'
        order by m.id
    """))
    for fila in filas:
        print(fila)