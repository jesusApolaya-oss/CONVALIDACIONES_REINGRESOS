import json
import flet as ft

from app.config import APP_TITLE, APP_VERSION
from app.data.repositories import MasterRepository
from app.engine.rules import validate_header, default_today
from app.engine.recommendation_engine import recommend_mappings
from app.models import HeaderData, ProjectState, SourceCourse, CourseMapping
from app.services.export_service import export_excel, export_pdf
from app.services.project_service import save_project


class MainApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.repo = MasterRepository()
        self.state = ProjectState()

        self.current_view = "cabecera"
        self.header_controls = {}
        self.source_rows_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, spacing=6)
        self.mapping_rows_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, spacing=6)
        self.malla_rows_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, spacing=4)
        self.manual_table_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, spacing=4)
        self.summary_text = ft.Text("")
        self.status_text = ft.Text("", size=12)
        self.manual_table_summary = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_700)
        self.search_center_results = ft.Column(spacing=2)
        self.center_study_info = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_700)
        self.source_code_dd = None
        self.dest_code_dd = None
        self.manual_mapping_controls = {}

        self.content = ft.Container(expand=True, padding=20)
        self.nav = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label="Cabecera"),
                ft.NavigationRailDestination(icon=ft.Icons.TABLE_ROWS_OUTLINED, selected_icon=ft.Icons.TABLE_ROWS, label="Malla"),
                ft.NavigationRailDestination(icon=ft.Icons.ALT_ROUTE_OUTLINED, selected_icon=ft.Icons.ALT_ROUTE, label="Equivalencias"),
                ft.NavigationRailDestination(icon=ft.Icons.PICTURE_AS_PDF_OUTLINED, selected_icon=ft.Icons.PICTURE_AS_PDF, label="Reportes"),
            ],
        )
        self.nav.on_change = self.on_nav_change

    # ---------- lifecycle ----------
    def build(self):
        self.page.title = f"{APP_TITLE} v{APP_VERSION}"
        self.page.window_width = 1450
        self.page.window_height = 920
        self.page.scroll = ft.ScrollMode.ALWAYS
        self.page.theme_mode = ft.ThemeMode.LIGHT

        self.page.add(
            ft.Row(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(content=self.nav, expand=True),
                        ft.Text(
                            "Desarrollado por:\nIng. Jesus Apolaya",
                            size=11,
                            color=ft.Colors.BLUE_GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                height=self.page.window_height,
            ),
            ft.VerticalDivider(width=1),
            ft.Container(
                content=self.content,
                expand=True,
            ),
        ],
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
        )
        self.render()

    def on_nav_change(self, e):
        selected = self.nav.selected_index
        self.current_view = ["cabecera", "malla", "equivalencias", "reportes"][selected]
        self.render()

    # ---------- helpers ----------
    def show_message(self, text):
        self.status_text.value = text
        self.page.update()

    def card(self, title, body, width=None):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, weight=ft.FontWeight.BOLD, size=16),
                body,
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.BLACK12),
            border_radius=14,
            padding=16,
            width=width,
        )

    def extract_header_state(self):
        h = HeaderData()
        c = self.header_controls
        selected_center = self.repo.get_center_study_by_code(c["origen_nombre_procedencia"].value or "")
        h.formato = c["formato"].value or ""
        h.codigo_estudiante = c["codigo"].value or ""
        h.apellidos = c["apellidos"].value or ""
        h.nombres = c["nombres"].value or ""
        h.carrera_codigo = c["carrera"].value or ""
        h.carrera_nombre = self.repo.get_carrera_name(h.carrera_codigo)
        h.modalidad = c["modalidad"].value or ""
        h.sede = c["sede"].value or ""
        h.anio_validez = c["anio_validez"].value or ""
        h.origen_nombre_procedencia = (selected_center or {}).get("display_name", "")
        h.origen_carrera_procedencia = c["origen_carrera_procedencia"].value or ""
        h.origen_anio_validez = c["origen_anio_validez"].value or ""
        try:
            h.origen_nota_aprobatoria = float(c["origen_nota_aprobatoria"].value or 0)
        except Exception:
            h.origen_nota_aprobatoria = 0.0
        h.fecha = c["fecha"].value or ""
        h.cargo_revisor = c["cargo_revisor"].value or ""
        h.nivel_academico = c["nivel_academico"].value or ""
        h.observaciones = c["observaciones"].value or ""
        return h

    def refresh_validities(self):
        c = self.header_controls

        career_value = c["carrera"].value
        modality_value = c["modalidad"].value

        vals = []
        if career_value and modality_value:
            vals = self.repo.get_validities(career_value, modality_value)

        current_value = None
        if "anio_validez" in c and c["anio_validez"].value in vals:
            current_value = c["anio_validez"].value

        if vals:
            current_value = current_value or vals[0]
            self.status_text.value = f"Anios de validez encontrados: {', '.join(vals)}"
        elif career_value and modality_value:
            self.status_text.value = "No hay anios de validez para la carrera y modalidad seleccionadas."
        else:
            self.status_text.value = "Selecciona carrera y modalidad para cargar anios de validez."

        c["anio_validez"] = ft.Dropdown(
            label="Año validez",
            width=220,
            options=[ft.dropdown.Option(v) for v in vals],
            value=current_value,
            disabled=not bool(vals),
        )

        if self.current_view == "cabecera":
            self.render()
        else:
            self.page.update()

    def enforce_virtual_rule(self):
        c = self.header_controls
        if c["sede"].value == "VIRTUAL":
            c["modalidad"].value = "WV"
        elif c["modalidad"].value == "WV" and c["sede"].value != "VIRTUAL":
            c["sede"].value = "VIRTUAL"
        self.refresh_validities()

    def refresh_source_rows(self):
        self.source_rows_column.controls.clear()
        if not self.state.source_courses:
            self.source_rows_column.controls.append(ft.Text("No hay cursos origen registrados."))
        else:
            for idx, item in enumerate(self.state.source_courses, start=1):
                self.source_rows_column.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"{idx}.", width=28),
                            ft.Text(item.codigo, width=100),
                            ft.Text(item.nombre, expand=True),
                            ft.Text(f"Cred: {item.creditos}", width=90),
                            ft.Text(f"Nota: {item.nota}", width=90),
                            ft.Text(item.tipo, width=150),
                        ]),
                        padding=8,
                        border=ft.border.all(1, ft.Colors.BLACK12),
                        border_radius=10,
                    )
                )

        source_opts = [ft.dropdown.Option(x.codigo) for x in self.state.source_courses]
        if self.source_code_dd:
            self.source_code_dd.options = source_opts

    def refresh_mapping_rows(self):
        self.mapping_rows_column.controls.clear()
        if not self.state.mappings:
            self.mapping_rows_column.controls.append(ft.Text("No hay equivalencias registradas."))
        else:
            for idx, item in enumerate(self.state.mappings, start=1):
                self.mapping_rows_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"{idx}.", width=28),
                                ft.Text(item.origen_codigo, width=110, weight=ft.FontWeight.BOLD),
                                ft.Text("→", width=24),
                                ft.Text(item.destino_codigo, width=110, weight=ft.FontWeight.BOLD),
                                ft.Text(item.estado, width=120),
                                ft.Text(f"Score: {item.score}", width=100),
                            ]),
                            ft.Text(f"Origen: {item.origen_nombre}"),
                            ft.Text(f"Destino: {item.destino_nombre}"),
                            ft.Text(item.observacion, size=12, color=ft.Colors.BLUE_GREY_700),
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.BLACK12),
                        border_radius=10,
                    )
                )
        self.summary_text.value = f"Cursos origen: {len(self.state.source_courses)} | Mapeos: {len(self.state.mappings)}"

    def refresh_malla_rows(self):
        self.malla_rows_column.controls.clear()
        malla = self.state.selected_malla
        if not malla:
            self.malla_rows_column.controls.append(ft.Text("Aún no hay malla cargada."))
            if self.dest_code_dd:
                self.dest_code_dd.options = []
            return

        header = ft.Row([
            ft.Text("Ciclo", width=70, weight=ft.FontWeight.BOLD),
            ft.Text("Código", width=120, weight=ft.FontWeight.BOLD),
            ft.Text("Curso", expand=True, weight=ft.FontWeight.BOLD),
            ft.Text("Cred", width=70, weight=ft.FontWeight.BOLD),
            ft.Text("Req.", width=200, weight=ft.FontWeight.BOLD),
        ])
        self.malla_rows_column.controls.append(header)

        for c in malla.get("courses", []):
            self.malla_rows_column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(str(c.get("cycle")), width=70),
                        ft.Text(c.get("code"), width=120),
                        ft.Text(c.get("name"), expand=True),
                        ft.Text(str(c.get("credits")), width=70),
                        ft.Text(str(c.get("requirements") or ""), width=200),
                    ]),
                    padding=6,
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.BLACK12)),
                )
            )
        dest_opts = [ft.dropdown.Option(x["code"]) for x in malla.get("courses", [])]
        if self.dest_code_dd:
            self.dest_code_dd.options = dest_opts

    def refresh_manual_table_summary(self):
        conva_count = 0
        reco_count = 0

        for controls in self.manual_mapping_controls.values():
            if controls["conva"].value:
                conva_count += 1
            if controls["reco"].value:
                reco_count += 1

        self.manual_table_summary.value = (
            f"Total convalidados: {conva_count} | "
            f"Total recomendados: {reco_count} | "
            f"Cursos origen registrados: {len(self.state.source_courses)}"
        )

    def on_manual_flags_change(self, e):
        self.refresh_manual_table_summary()
        self.page.update()

    def on_manual_source_select(self, dest_code):
        def _handler(e):
            controls = self.manual_mapping_controls[dest_code]
            source_code = controls["source"].value or ""
            source = next((x for x in self.state.source_courses if x.codigo == source_code), None)

            if not source:
                controls["source_name"].value = ""
                controls["source_credits"].value = ""
                controls["source_nota"].value = ""
                controls["percent_diff"].value = "-"
            else:
                controls["source_name"].value = source.nombre
                controls["source_credits"].value = str(source.creditos)
                controls["source_nota"].value = str(source.nota)
                try:
                    course_credits = float(controls["course"].get("credits") or 0)
                    if course_credits > 0:
                        diff = ((course_credits - float(source.creditos or 0)) / course_credits) * 100
                        controls["percent_diff"].value = f"{round(diff)}%"
                    else:
                        controls["percent_diff"].value = "-"
                except Exception:
                    controls["percent_diff"].value = "-"
                if not controls["conva"].value and not controls["reco"].value:
                    controls["conva"].value = True

            self.refresh_manual_table_summary()
            self.page.update()

        return _handler

    def refresh_manual_equivalence_rows(self):
        self.manual_table_column.controls.clear()
        self.manual_mapping_controls = {}

        malla = self.state.selected_malla
        if not malla:
            self.manual_table_column.controls.append(ft.Text("Carga primero la malla destino para trabajar equivalencias manuales."))
            self.refresh_manual_table_summary()
            return

        source_options = [ft.dropdown.Option(x.codigo, text=x.codigo) for x in self.state.source_courses]
        mapping_by_dest = {item.destino_codigo: item for item in self.state.mappings}
        source_by_code = {item.codigo: item for item in self.state.source_courses}

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Ciclo", width=45, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Código UPN", width=95, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Curso UPN", width=290, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Cred", width=45, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Req.", width=180, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Código origen", width=130, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Nombre curso origen", width=230, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Cred. origen", width=80, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Nota", width=60, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Conva", width=58, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Reco", width=50, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("% Dif.", width=65, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.BLACK,
            padding=8,
            border_radius=8,
        )
        self.manual_table_column.controls.append(header)

        for course in malla.get("courses", []):
            dest_code = course.get("code")
            current_mapping = mapping_by_dest.get(dest_code)
            current_source = source_by_code.get(current_mapping.origen_codigo) if current_mapping else None

            source_dd = ft.Dropdown(
                width=130,
                options=source_options,
                value=current_mapping.origen_codigo if current_mapping else None,
                enable_filter=True,
                enable_search=True,
                editable=True,
                hint_text="Curso origen",
            )
            source_name = ft.TextField(
                width=230,
                value=current_source.nombre if current_source else "",
                read_only=True,
                bgcolor=ft.Colors.YELLOW_100,
            )
            source_credits = ft.TextField(
                width=80,
                value=str(current_source.creditos) if current_source else "",
                read_only=True,
                bgcolor=ft.Colors.YELLOW_100,
            )
            source_nota = ft.TextField(
                width=60,
                value=str(current_source.nota) if current_source else "",
                read_only=True,
                bgcolor=ft.Colors.YELLOW_100,
            )
            conva_chk = ft.Checkbox(
                value=bool(current_mapping and "CONVA" in current_mapping.estado.upper()),
            )
            reco_chk = ft.Checkbox(
                value=bool(current_mapping and "RECO" in current_mapping.estado.upper()),
            )

            percent_diff = "-"
            if current_source and course.get("credits") not in (None, ""):
                try:
                    percent_diff = f"{round(((float(course.get('credits')) - float(current_source.creditos)) / float(course.get('credits'))) * 100)}%"
                except Exception:
                    percent_diff = "-"

            self.manual_mapping_controls[dest_code] = {
                "source": source_dd,
                "source_name": source_name,
                "source_credits": source_credits,
                "source_nota": source_nota,
                "conva": conva_chk,
                "reco": reco_chk,
                "course": course,
                "percent_diff": ft.Text(percent_diff, width=65, color=ft.Colors.BLUE_700),
            }

            source_dd.on_select = self.on_manual_source_select(dest_code)
            conva_chk.on_change = self.on_manual_flags_change
            reco_chk.on_change = self.on_manual_flags_change

            percent_diff_text = self.manual_mapping_controls[dest_code]["percent_diff"]

            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(str(course.get("cycle") or ""), width=45),
                        ft.Text(dest_code or "", width=95),
                        ft.Text(course.get("name") or "", width=290),
                        ft.Text(str(course.get("credits") or ""), width=45),
                        ft.Text(str(course.get("requirements") or ""), width=180, size=11),
                        source_dd,
                        source_name,
                        source_credits,
                        source_nota,
                        ft.Container(content=conva_chk, width=58),
                        ft.Container(content=reco_chk, width=50),
                        percent_diff_text,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=6,
                bgcolor=ft.Colors.YELLOW_100,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.BLACK12)),
            )
            self.manual_table_column.controls.append(row)

        self.refresh_manual_table_summary()

    def save_manual_table_mappings(self, e):
        new_mappings = []

        for dest_code, controls in self.manual_mapping_controls.items():
            source_code = controls["source"].value or ""
            if not source_code:
                continue
            if not controls["conva"].value and not controls["reco"].value:
                continue

            source = next((x for x in self.state.source_courses if x.codigo == source_code), None)
            if not source:
                continue

            course = controls["course"]
            states = []
            if controls["conva"].value:
                states.append("CONVA")
            if controls["reco"].value:
                states.append("RECO")

            new_mappings.append(
                CourseMapping(
                    origen_codigo=source.codigo,
                    origen_nombre=source.nombre,
                    destino_codigo=dest_code,
                    destino_nombre=course.get("name") or "",
                    creditos_origen=float(source.creditos or 0),
                    creditos_destino=float(course.get("credits") or 0),
                    score=100.0,
                    estado="MANUAL " + "/".join(states),
                    observacion="Asignado desde la tabla manual de equivalencias.",
                )
            )

        self.state.mappings = new_mappings
        self.refresh_mapping_rows()
        self.refresh_manual_table_summary()
        self.page.update()
        self.show_message(f"Equivalencias manuales guardadas: {len(new_mappings)}")

    # ---------- actions ----------
    def on_formato_change(self, e):
        self.page.update()

    def on_carrera_change(self, e):
        self.refresh_validities()

    def on_modalidad_change(self, e):
        self.enforce_virtual_rule()
        self.page.update()

    def on_sede_change(self, e):
        self.enforce_virtual_rule()
        self.page.update()

    def save_header(self, e):
        self.state.header = self.extract_header_state()
        errors = validate_header(self.state.header)
        if errors:
            self.show_message("\n".join(errors))
            return
        self.show_message("Cabecera validada correctamente.")

    def search_center_study(self, e):
        term = self.header_controls["origen_nombre_procedencia"].value or ""
        results = self.repo.search_center_study(term)
        self.search_center_results.controls.clear()
        if not results:
            self.search_center_results.controls.append(ft.Text("Sin coincidencias."))
        else:
            for item in results[:10]:
                display = f"{item['display_name']} | Min nota: {item.get('min_grade') or 'N/D'}"
                btn = ft.TextButton(display)
                def _pick(ev, center=item):
                    self.header_controls["origen_nombre_procedencia"].value = center["display_name"] or ""
                    self.header_controls["origen_nota_aprobatoria"].value = str(center.get("min_grade") or "")
                    self.page.update()
                btn.on_click = _pick
                self.search_center_results.controls.append(btn)
        self.page.update()

    def on_center_study_select(self, e):
        center = self.repo.get_center_study_by_code(self.header_controls["origen_nombre_procedencia"].value)
        if not center:
            self.header_controls["origen_nota_aprobatoria"].value = ""
            self.center_study_info.value = ""
            self.page.update()
            return

        min_grade = self.repo.resolve_center_min_grade(center)
        self.header_controls["origen_nota_aprobatoria"].value = str(min_grade)

        center_type = center.get("institution_type") or "CENTRO"
        self.center_study_info.value = f"{center.get('display_name')} | {center_type} | Min nota: {min_grade}"
        self.page.update()

    def load_malla(self, e):
        self.state.header = self.extract_header_state()
        errors = validate_header(self.state.header)
        if errors:
            self.show_message("\n".join(errors))
            return

        malla = self.repo.get_malla(
            self.state.header.carrera_codigo,
            self.state.header.modalidad,
            self.state.header.anio_validez,
        )
        if not malla:
            self.show_message("No se encontró la malla para la combinación seleccionada.")
            return

        self.state.selected_malla = malla
        self.refresh_malla_rows()
        self.show_message(f"Malla cargada: {malla.get('sheet_name')} con {len(malla.get('courses', []))} cursos.")
        self.page.update()

    def add_source_course(self, e):
        codigo = self.source_input_codigo.value or ""
        nombre = self.source_input_nombre.value or ""
        if not codigo.strip() or not nombre.strip():
            self.show_message("Debes ingresar código y nombre del curso origen.")
            return

        try:
            creditos = float(self.source_input_creditos.value or 0)
        except Exception:
            creditos = 0.0

        try:
            nota = float(self.source_input_nota.value or 0)
        except Exception:
            nota = 0.0

        item = SourceCourse(
            codigo=codigo.strip(),
            nombre=nombre.strip(),
            creditos=creditos,
            nota=nota,
            aprobado=self.source_input_aprobado.value,
            tipo=self.source_input_tipo.value or "CONVALIDACION",
        )
        self.state.source_courses.append(item)
        self.source_input_codigo.value = ""
        self.source_input_nombre.value = ""
        self.source_input_creditos.value = ""
        self.source_input_nota.value = ""
        self.refresh_source_rows()
        if self.current_view == "equivalencias":
            self.refresh_manual_equivalence_rows()
        self.page.update()
        self.show_message("Curso origen agregado.")

    def auto_recommend(self, e):
        if not self.state.selected_malla:
            self.show_message("Primero debes cargar la malla destino.")
            return
        if not self.state.source_courses:
            self.show_message("No hay cursos origen cargados.")
            return

        self.state.mappings = recommend_mappings(
            self.state.source_courses,
            self.state.selected_malla.get("courses", []),
            max_credit_gap=2,
            min_score=58,
        )
        self.refresh_mapping_rows()
        if self.current_view == "equivalencias":
            self.refresh_manual_equivalence_rows()
        self.page.update()
        self.show_message(f"Se generaron {len(self.state.mappings)} recomendaciones.")

    def add_manual_mapping(self, e):
        if not self.state.selected_malla:
            self.show_message("Primero debes cargar la malla.")
            return
        source_code = self.source_code_dd.value or ""
        dest_code = self.dest_code_dd.value or ""
        if not source_code or not dest_code:
            self.show_message("Selecciona un curso origen y un curso destino.")
            return

        source = next((x for x in self.state.source_courses if x.codigo == source_code), None)
        dest = next((x for x in self.state.selected_malla.get("courses", []) if x["code"] == dest_code), None)

        if not source or not dest:
            self.show_message("No se pudo resolver el curso origen o destino.")
            return

        self.state.mappings.append(
            CourseMapping(
                origen_codigo=source.codigo,
                origen_nombre=source.nombre,
                destino_codigo=dest["code"],
                destino_nombre=dest["name"],
                creditos_origen=float(source.creditos or 0),
                creditos_destino=float(dest.get("credits") or 0),
                score=100.0,
                estado="MANUAL",
                observacion="Asignado manualmente por el usuario.",
            )
        )
        self.refresh_mapping_rows()
        self.page.update()
        self.show_message("Mapeo manual agregado.")

    def export_excel_action(self, e):
        path = export_excel(self.state)
        self.show_message(f"Excel generado: {path}")

    def export_pdf_action(self, e):
        path = export_pdf(self.state)
        self.show_message(f"PDF generado: {path}")

    def save_project_action(self, e):
        path = save_project(self.state)
        self.show_message(f"Proyecto guardado: {path}")

    # ---------- views ----------
    def build_cabecera(self):
        c = self.header_controls
        if not c:
            c["formato"] = ft.Dropdown(label="Formato", width=430, options=[ft.dropdown.Option(x) for x in self.repo.formatos])
            c["formato"].on_select = self.on_formato_change
            c["codigo"] = ft.TextField(label="Código estudiante", width=220)
            c["apellidos"] = ft.TextField(label="Apellidos", width=320)
            c["nombres"] = ft.TextField(label="Nombres", width=320)

            c["carrera"] = ft.Dropdown(
                label="Carrera",
                width=480,
                options=[
                    ft.dropdown.Option(
                        key=f"{item['code']} - {item['name']}",
                        text=f"{item['code']} - {item['name']}"
                    )
                    for item in self.repo.carreras
                ]
            )
            c["carrera"].on_select = self.on_carrera_change

            c["modalidad"] = ft.Dropdown(
                label="Modalidad",
                width=220,
                options=[ft.dropdown.Option(item["code"]) for item in self.repo.modalidades]
            )
            c["modalidad"].on_select = self.on_modalidad_change

            c["sede"] = ft.Dropdown(
                label="Sede",
                width=220,
                options=[ft.dropdown.Option(item["name"]) for item in self.repo.sedes]
            )
            c["sede"].on_select = self.on_sede_change

            c["anio_validez"] = ft.Dropdown(
            label="Año validez",
            width=220,
            options=[],
            value=None,
            disabled=True,
            )

            c["origen_nombre_procedencia"] = ft.Dropdown(
                label="Universidad / instituto de procedencia",
                width=620,
                options=[
                    ft.dropdown.Option(
                        key=item["origin_code"],
                        text=item["display_name"],
                    )
                    for item in self.repo.get_center_study_options()
                ],
                enable_filter=True,
                enable_search=True,
                editable=True,
                hint_text="Escribe para filtrar la institución",
            )
            c["origen_nombre_procedencia"].on_select = self.on_center_study_select
            c["origen_carrera_procedencia"] = ft.TextField(label="Carrera de procedencia", width=340)
            c["origen_anio_validez"] = ft.TextField(label="Año validez origen", width=220)
            c["origen_nota_aprobatoria"] = ft.TextField(label="Nota aprobatoria origen", width=220)

            c["fecha"] = ft.TextField(label="Fecha", width=220, value=default_today())
            c["cargo_revisor"] = ft.Dropdown(label="Cargo revisor", width=240, options=[ft.dropdown.Option(x) for x in self.repo.cargos])
            c["nivel_academico"] = ft.Dropdown(label="Nivel académico", width=240, options=[ft.dropdown.Option(x) for x in self.repo.niveles])
            c["observaciones"] = ft.TextField(label="Observaciones", multiline=True, min_lines=3, max_lines=4, width=700)

        return ft.Column([
            ft.Text("Cabecera de solicitud", size=24, weight=ft.FontWeight.BOLD),
            self.card("Datos generales", ft.Column([
                ft.Row([c["formato"]]),
                ft.Row([c["codigo"], c["apellidos"], c["nombres"]], wrap=True),
                ft.Row([c["carrera"], c["modalidad"], c["sede"], c["anio_validez"]], wrap=True),
            ])),
            self.card("Datos de procedencia", ft.Column([
                ft.Row([c["origen_nombre_procedencia"]], wrap=True),
                self.center_study_info,
                ft.Row([c["origen_carrera_procedencia"], c["origen_anio_validez"], c["origen_nota_aprobatoria"]], wrap=True),
            ])),
            self.card("Control interno", ft.Column([
                ft.Row([c["fecha"], c["cargo_revisor"], c["nivel_academico"]], wrap=True),
                c["observaciones"],
                ft.Row([
                    ft.ElevatedButton("Validar cabecera", on_click=self.save_header),
                    ft.OutlinedButton("Cargar malla destino", on_click=self.load_malla),
                ]),
            ])),
            self.status_text,
        ], spacing=14)

    def build_malla(self):
        info = []
        if self.state.selected_malla:
            info = [
                ft.Text(f"Hoja: {self.state.selected_malla.get('sheet_name')}"),
                ft.Text(f"Facultad: {self.state.selected_malla.get('faculty')}"),
                ft.Text(f"Carrera: {self.state.selected_malla.get('career_name')}"),
                ft.Text(f"Modalidad: {self.state.selected_malla.get('modality')}"),
                ft.Text(f"Año validez: {self.state.selected_malla.get('validity')}"),
                ft.Text(f"Cursos: {len(self.state.selected_malla.get('courses', []))}"),
            ]
        else:
            info = [ft.Text("No hay malla cargada todavía.")]

        self.refresh_malla_rows()
        return ft.Column([
            ft.Text("Malla destino", size=24, weight=ft.FontWeight.BOLD),
            self.card("Detalle", ft.Column(info, spacing=6)),
            self.card("Cursos", ft.Container(content=self.malla_rows_column, height=560)),
        ], spacing=14)

    def build_equivalencias(self):
        if not hasattr(self, "source_input_codigo"):
            self.source_input_codigo = ft.TextField(label="Código", width=150)
            self.source_input_nombre = ft.TextField(label="Nombre curso origen", width=420)
            self.source_input_creditos = ft.TextField(label="Créditos", width=100)
            self.source_input_nota = ft.TextField(label="Nota", width=100)
            self.source_input_aprobado = ft.Checkbox(label="Aprobado", value=True)
            self.source_input_tipo = ft.Dropdown(
                label="Tipo",
                width=180,
                options=[ft.dropdown.Option("CONVALIDACION"), ft.dropdown.Option("RECONVALIDACION"), ft.dropdown.Option("REINGRESO")],
                value="CONVALIDACION",
            )

        self.refresh_source_rows()
        self.refresh_mapping_rows()
        self.refresh_manual_equivalence_rows()

        return ft.Column([
            ft.Text("Tabla de equivalencias", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                self.card("Agregar curso origen", ft.Column([
                    ft.Row([self.source_input_codigo, self.source_input_nombre], wrap=True),
                    ft.Row([self.source_input_creditos, self.source_input_nota, self.source_input_tipo, self.source_input_aprobado], wrap=True),
                    ft.ElevatedButton("Agregar curso", on_click=self.add_source_course),
                ]), width=760),
                self.card("Resumen", ft.Column([
                    ft.Text(f"Carrera: {self.state.header.carrera_nombre or '-'}"),
                    ft.Text(f"Modalidad: {self.state.header.modalidad or '-'}"),
                    ft.Text(f"Año validez: {self.state.header.anio_validez or '-'}"),
                    self.manual_table_summary,
                    ft.ElevatedButton("Guardar equivalencias manuales", on_click=self.save_manual_table_mappings),
                    ft.OutlinedButton("Auto recomendar", on_click=self.auto_recommend),
                    ft.OutlinedButton("Guardar proyecto", on_click=self.save_project_action),
                ]), width=300),
            ], wrap=True),
            self.card(
                "Vista operativa tipo Excel",
                ft.Container(
                    content=self.manual_table_column,
                    height=520,
                ),
            ),
            ft.Row([
                self.card("Cursos origen registrados", ft.Container(content=self.source_rows_column, height=240), width=560),
                self.card("Equivalencias guardadas", ft.Container(content=self.mapping_rows_column, height=240), width=560),
            ], wrap=True),
            self.status_text,
        ], spacing=14)

    def build_reportes(self):
        return ft.Column([
            ft.Text("Reportes y exportación", size=24, weight=ft.FontWeight.BOLD),
            self.card("Exportar resultados", ft.Row([
                ft.ElevatedButton("Exportar Excel", on_click=self.export_excel_action),
                ft.ElevatedButton("Exportar PDF", on_click=self.export_pdf_action),
                ft.OutlinedButton("Guardar proyecto JSON", on_click=self.save_project_action),
            ], wrap=True)),
            self.card("Estado actual", ft.Column([
                self.summary_text,
                self.status_text,
                ft.Text(json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2)[:3000], selectable=True, size=12),
            ])),
        ], spacing=14)

    def render(self):
        if self.current_view == "cabecera":
            self.content.content = self.build_cabecera()
        elif self.current_view == "malla":
            self.content.content = self.build_malla()
        elif self.current_view == "equivalencias":
            self.content.content = self.build_equivalencias()
        else:
            self.content.content = self.build_reportes()
        self.page.update()


def main(page: ft.Page):
    app = MainApp(page)
    app.build()
