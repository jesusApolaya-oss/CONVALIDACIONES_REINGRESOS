from difflib import SequenceMatcher
from app.models import CourseMapping
from app.utils.text_utils import normalize_text, tokenize

def similarity(a: str, b: str) -> float:
    a_n = normalize_text(a)
    b_n = normalize_text(b)
    ratio = SequenceMatcher(None, a_n, b_n).ratio()
    ta = set(tokenize(a_n))
    tb = set(tokenize(b_n))
    overlap = len(ta & tb) / max(1, len(ta | tb))
    return round((ratio * 0.65 + overlap * 0.35) * 100, 2)

def recommend_mappings(source_courses, malla_courses, max_credit_gap=2, min_score=58):
    results = []
    used_dest = set()

    for source in source_courses:
        best = None
        best_score = -1
        best_gap = 10**9

        for dest in malla_courses:
            if dest["code"] in used_dest:
                continue
            credit_gap = abs(float(source.creditos or 0) - float(dest.get("credits") or 0))
            score = similarity(source.nombre, dest.get("name", ""))

            if credit_gap <= max_credit_gap and score >= min_score:
                if score > best_score or (score == best_score and credit_gap < best_gap):
                    best = dest
                    best_score = score
                    best_gap = credit_gap

        if best:
            used_dest.add(best["code"])
            results.append(
                CourseMapping(
                    origen_codigo=source.codigo,
                    origen_nombre=source.nombre,
                    destino_codigo=best["code"],
                    destino_nombre=best["name"],
                    creditos_origen=float(source.creditos or 0),
                    creditos_destino=float(best.get("credits") or 0),
                    score=float(best_score),
                    estado="PROPUESTO",
                    observacion=f"Auto sugerido por similitud={best_score}% y diferencia créditos={best_gap}"
                )
            )
    return results
