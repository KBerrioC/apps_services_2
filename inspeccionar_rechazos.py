import json
from collections import Counter

r = json.load(open('salida/reporte.json', encoding='utf-8'))
rechazados = [e for e in r['envios_detalle'] if e['resultado'] == 'rechazado_api']

print('Total rechazados por API:', len(rechazados))
print()
print('Distribución de códigos HTTP:', Counter(e['codigo_http'] for e in rechazados))
print()

# separar por proveedor (el id_trazabilidad empieza con A- o B-)
rechazados_a = [e for e in rechazados if e['id_trazabilidad'].startswith('A-')]
rechazados_b = [e for e in rechazados if e['id_trazabilidad'].startswith('B-')]
print(f'Rechazados de proveedor A: {len(rechazados_a)}')
print(f'Rechazados de proveedor B: {len(rechazados_b)}')
print()

print('--- 3 ejemplos de A rechazados ---')
for e in rechazados_a[:3]:
    print(e['id_trazabilidad'], '->', e['detalle'])
print()
print('--- 3 ejemplos de B rechazados ---')
for e in rechazados_b[:3]:
    print(e['id_trazabilidad'], '->', e['detalle'])