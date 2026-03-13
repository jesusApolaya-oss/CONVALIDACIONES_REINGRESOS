from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class HeaderData:
    formato: str = ""
    codigo_estudiante: str = ""
    apellidos: str = ""
    nombres: str = ""
    carrera_codigo: str = ""
    carrera_nombre: str = ""
    modalidad: str = ""
    sede: str = ""
    anio_validez: str = ""
    origen_nombre_procedencia: str = ""
    origen_carrera_procedencia: str = ""
    origen_anio_validez: str = ""
    origen_nota_aprobatoria: float = 0.0
    fecha: str = ""
    cargo_revisor: str = ""
    nivel_academico: str = ""
    observaciones: str = ""

@dataclass
class SourceCourse:
    codigo: str
    nombre: str
    creditos: float = 0.0
    nota: float = 0.0
    aprobado: bool = True
    tipo: str = "CONVALIDACION"

@dataclass
class CourseMapping:
    origen_codigo: str
    origen_nombre: str
    destino_codigo: str
    destino_nombre: str
    creditos_origen: float = 0.0
    creditos_destino: float = 0.0
    score: float = 0.0
    estado: str = "PROPUESTO"
    observacion: str = ""

@dataclass
class ProjectState:
    header: HeaderData = field(default_factory=HeaderData)
    source_courses: List[SourceCourse] = field(default_factory=list)
    mappings: List[CourseMapping] = field(default_factory=list)
    selected_malla: Optional[dict] = None

    def to_dict(self):
        return {
            "header": asdict(self.header),
            "source_courses": [asdict(x) for x in self.source_courses],
            "mappings": [asdict(x) for x in self.mappings],
            "selected_malla": self.selected_malla,
        }

    @staticmethod
    def from_dict(data: dict):
        state = ProjectState()
        state.header = HeaderData(**data.get("header", {}))
        state.source_courses = [SourceCourse(**x) for x in data.get("source_courses", [])]
        state.mappings = [CourseMapping(**x) for x in data.get("mappings", [])]
        state.selected_malla = data.get("selected_malla")
        return state
