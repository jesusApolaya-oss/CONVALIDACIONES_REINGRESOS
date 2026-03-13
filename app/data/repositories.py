import json
from app.config import DATA_DIR


def _read_json(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


class MasterRepository:
    def __init__(self):
        self.analysis = _read_json("analysis.json")
        self.formatos = _read_json("formatos.json")
        self.sedes = _read_json("sedes.json")
        self.carreras = _read_json("carreras.json")
        self.modalidades = _read_json("modalidades.json")
        self.mallas_index = _read_json("mallas_index.json")
        self.mallas_full = _read_json("mallas_full.json")
        self.center_studies = _read_json("center_studies.json")
        self.cargos = _read_json("cargos.json")
        self.niveles = _read_json("niveles.json")

    def normalize(self, value):
        return str(value or "").strip().upper()

    def extract_career_code(self, career_value: str) -> str:
        """
        Soporta:
        - 'ANI'
        - 'ANI - ADMINISTRACIÓN Y NEGOCIOS INTERNACIONAL'
        """
        value = self.normalize(career_value)

        if " - " in value:
            return value.split(" - ")[0].strip()

        return value

    def get_carrera_name(self, career_code: str) -> str:
        career_code = self.extract_career_code(career_code)
        for item in self.carreras:
            if self.normalize(item["code"]) == career_code:
                return item["name"]
        return ""

    def get_validities(self, career_code: str, modality: str):
        values = []

        career_code = self.extract_career_code(career_code)
        modality = self.normalize(modality)

        for item in self.mallas_index:
            item_career = self.normalize(item.get("career_code"))
            item_modality = self.normalize(item.get("modality"))
            item_validity = item.get("validity")

            if item_career == career_code and item_modality == modality:
                if item_validity not in (None, ""):
                    values.append(str(item_validity))

        return sorted(set(values), reverse=True)

    def get_malla(self, career_code: str, modality: str, validity: str):
        career_code = self.extract_career_code(career_code)
        modality = self.normalize(modality)
        validity = str(validity or "").strip()

        for item in self.mallas_index:
            item_career = self.normalize(item.get("career_code"))
            item_modality = self.normalize(item.get("modality"))
            item_validity = str(item.get("validity") or "").strip()

            if (
                item_career == career_code
                and item_modality == modality
                and item_validity == validity
            ):
                sheet_name = item["sheet_name"]
                return self.mallas_full.get(sheet_name)

        return None

    def search_center_study(self, term: str):
        term_n = self.normalize(term)
        if not term_n:
            return []

        results = []
        for item in self.center_studies:
            display_name = self.normalize(item.get("display_name", ""))
            origin_name = self.normalize(item.get("origin_name", ""))
            siglas = self.normalize(item.get("siglas", ""))

            hay = " ".join([display_name, origin_name, siglas])

            if term_n in hay and item.get("status") != "Denegada":
                results.append(item)

        return results[:20]

    def get_center_study_options(self):
        results = []
        for item in self.center_studies:
            if item.get("status") == "Denegada":
                continue
            code = str(item.get("origin_code") or "").strip()
            name = str(item.get("display_name") or "").strip()
            if not code or not name:
                continue
            results.append(item)

        return sorted(results, key=lambda x: self.normalize(x.get("display_name")))

    def get_center_study_by_code(self, origin_code: str):
        origin_code = str(origin_code or "").strip().upper()
        if not origin_code:
            return None

        for item in self.center_studies:
            item_code = str(item.get("origin_code") or "").strip().upper()
            if item_code == origin_code and item.get("status") != "Denegada":
                return item
        return None

    def resolve_center_min_grade(self, center_item, default_grade=13):
        if not center_item:
            return default_grade

        value = center_item.get("min_grade")
        if value in (None, ""):
            return default_grade
        return value

    def debug_mallas(self, career_code: str):
        career_code = self.extract_career_code(career_code)
        resultados = []

        for item in self.mallas_index:
            item_career = self.normalize(item.get("career_code"))
            if item_career == career_code:
                resultados.append(
                    {
                        "career_code": item.get("career_code"),
                        "modality": item.get("modality"),
                        "validity": item.get("validity"),
                        "sheet_name": item.get("sheet_name"),
                    }
                )

        return resultados
