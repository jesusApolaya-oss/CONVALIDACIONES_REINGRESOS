import json
from pathlib import Path
from app.config import OUTPUT_DIR
from app.models import ProjectState

def save_project(state: ProjectState, file_name: str = "proyecto_convalidacion.json") -> Path:
    path = OUTPUT_DIR / file_name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    return path

def load_project(path: str) -> ProjectState:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ProjectState.from_dict(data)
