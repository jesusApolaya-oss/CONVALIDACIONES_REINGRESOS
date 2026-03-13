from datetime import datetime

def validate_header(header):
    errors = []
    if not header.formato:
        errors.append("Debes seleccionar el formato.")
    if not header.codigo_estudiante.strip():
        errors.append("Debes ingresar el código del estudiante.")
    if not header.apellidos.strip():
        errors.append("Debes ingresar los apellidos.")
    if not header.nombres.strip():
        errors.append("Debes ingresar los nombres.")
    if not header.carrera_codigo:
        errors.append("Debes seleccionar la carrera.")
    if not header.modalidad:
        errors.append("Debes seleccionar la modalidad.")
    if not header.sede:
        errors.append("Debes seleccionar la sede.")
    if not header.anio_validez:
        errors.append("Debes seleccionar el año de validez.")
    if header.sede == "VIRTUAL" and header.modalidad != "WV":
        errors.append("Si la sede es VIRTUAL, la modalidad debe ser WV.")
    if header.sede != "VIRTUAL" and header.modalidad == "WV":
        errors.append("Si la modalidad es WV, la sede debe ser VIRTUAL.")
    return errors

def default_today():
    return datetime.now().strftime("%Y-%m-%d")
