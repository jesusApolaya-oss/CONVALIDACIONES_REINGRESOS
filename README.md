# Convalidaciones App v2

Aplicación moderna en Python + Flet construida a partir del Excel y módulos VBA entregados.
Esta versión es standalone: en tiempo de ejecución no pide el Excel original.

## Qué incluye
- Cabecera de solicitud
- Carga de maestros embebidos en JSON
- Selección automática de malla por carrera + modalidad + año validez
- Visualización de cursos destino
- Registro de cursos origen
- Auto recomendación por similitud de nombre y tolerancia de créditos
- Mapeo manual origen → destino
- Exportación a Excel y PDF
- Guardado y carga de proyecto en JSON

## Ejecución
```bash
pip install -r requirements.txt
python main.py
```

## Nota honesta
Esta app reemplaza la dependencia operativa del Excel, pero la paridad total con el VBA
original todavía requerirá iteraciones adicionales sobre reglas muy específicas del módulo
EquivalenciaModule.bas.
