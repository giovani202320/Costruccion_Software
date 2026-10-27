import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="CCCCCC", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_callout_box(doc, text, title="CAPTURA REQUERIDA"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "FADBD8")  # suave rojizo / alerta
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Borde rojo izquierdo pronunciado
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="C0392B"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run_title = p.add_run(f"📸 [{title}]: ")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(10)
    run_title.font.color.rgb = RGBColor(192, 57, 43)
    
    run_text = p.add_run(text)
    run_text.italic = True
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = RGBColor(50, 50, 50)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_section_banner(doc, title_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, "C0392B")  # UNSA Red
    set_cell_margins(cell, top=80, bottom=80, left=150, right=150)
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(title_text)
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(255, 255, 255)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(4)
    p_after.paragraph_format.space_after = Pt(4)

def create_document():
    doc = docx.Document()
    
    # Margenes
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # Estilo base
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    # ------------------ ENCABEZADO FORMATO UNSA ------------------
    header_tbl = doc.add_table(rows=2, cols=3)
    header_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(header_tbl, color="A0A0A0", sz="4")
    
    # Anchos de columnas
    col_widths = [Inches(1.5), Inches(4.0), Inches(1.3)]
    for row in header_tbl.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width
            set_cell_margins(row.cells[idx], top=60, bottom=60, left=80, right=80)
            row.cells[idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Celda 1,0: Logo Ing Sistemas
    p1 = header_tbl.cell(0, 0).paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p1.add_run("INGENIERIA\nSISTEMAS")
    r1.bold = True
    r1.font.size = Pt(9)
    r1.font.color.rgb = RGBColor(192, 57, 43)

    # Celda 0,1: Titulo Institucional
    p2 = header_tbl.cell(0, 1).paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("UNIVERSIDAD NACIONAL DE SAN AGUSTIN\nFACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS\nESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMA")
    r2.bold = True
    r2.font.size = Pt(8.5)
    r2.font.color.rgb = RGBColor(20, 20, 20)

    # Celda 0,2: ABET
    p3 = header_tbl.cell(0, 2).paragraphs[0]
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("ABET")
    r3.bold = True
    r3.font.size = Pt(13)
    r3.font.color.rgb = RGBColor(180, 40, 20)

    # Fila 1: Metadatos de aprobación (merge de cols)
    meta_cell = header_tbl.cell(1, 0)
    meta_cell.merge(header_tbl.cell(1, 2))
    p_meta = meta_cell.paragraphs[0]
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run("Formato: Guía de Práctica de Laboratorio / Talleres / Centros de Simulación\nAprobación: 2022/03/01        Código: GUIA-PRLE-001        Página: 1")
    r_meta.font.size = Pt(7.5)
    r_meta.font.color.rgb = RGBColor(80, 80, 80)

    # Titulo de informe
    p_inf = doc.add_paragraph()
    p_inf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inf.paragraph_format.space_before = Pt(10)
    p_inf.paragraph_format.space_after = Pt(2)
    r_inf1 = p_inf.add_run("INFORME DE LABORATORIO\n")
    r_inf1.bold = True
    r_inf1.font.size = Pt(13)
    r_inf2 = p_inf.add_run("(formato estudiante)")
    r_inf2.font.size = Pt(10)

    # ------------------ BANNER: INFORMACIÓN BÁSICA ------------------
    add_section_banner(doc, "INFORMACIÓN BÁSICA")

    # Tabla de metadatos de la practica
    info_tbl = doc.add_table(rows=6, cols=6)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(info_tbl, color="A0A0A0", sz="4")

    # Helper para asignar texto en tabla
    def fill_cell(cell, text, bold_prefix="", font_size=8.5, span_cols=1):
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.05
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
            rb.font.size = Pt(font_size)
        rt = p.add_run(text)
        rt.font.size = Pt(font_size)
        set_cell_margins(cell, top=50, bottom=50, left=70, right=70)

    # Fila 0: ASIGNATURA
    info_tbl.cell(0, 0).merge(info_tbl.cell(0, 1))
    info_tbl.cell(0, 2).merge(info_tbl.cell(0, 5))
    fill_cell(info_tbl.cell(0, 0), "CONSTRUCCIÓN DE SOFTWARE", bold_prefix="ASIGNATURA: ")
    fill_cell(info_tbl.cell(0, 2), "Refactorizar hacia patrones de diseño con IA: Strategy, Adapter, Factory, Decorator, State, Observer y Chain of Responsibility, medidos con pruebas y métricas", bold_prefix="TÍTULO DE LA PRÁCTICA: ")

    # Fila 1: NUMERO, AÑO, SEMESTRE
    fill_cell(info_tbl.cell(1, 0), "07", bold_prefix="NÚMERO DE PRÁCTICA: ")
    info_tbl.cell(1, 1).merge(info_tbl.cell(1, 2))
    fill_cell(info_tbl.cell(1, 1), "2026-B", bold_prefix="AÑO LECTIVO: ")
    info_tbl.cell(1, 3).merge(info_tbl.cell(1, 5))
    fill_cell(info_tbl.cell(1, 3), "VI", bold_prefix="NRO. SEMESTRE: ")

    # Fila 2: FECHA Y HORA
    info_tbl.cell(2, 0).merge(info_tbl.cell(2, 2))
    info_tbl.cell(2, 3).merge(info_tbl.cell(2, 5))
    fill_cell(info_tbl.cell(2, 0), "26/10/2026", bold_prefix="FECHA DE PRESENTACIÓN: ")
    fill_cell(info_tbl.cell(2, 3), "11:30", bold_prefix="HORA DE PRESENTACIÓN: ")

    # Fila 3: INTEGRANTES Y NOTA
    info_tbl.cell(3, 0).merge(info_tbl.cell(3, 3))
    info_tbl.cell(3, 4).merge(info_tbl.cell(3, 5))
    fill_cell(info_tbl.cell(3, 0), "\n• Mendoza Contreras, Giovani Angel\n• Yunque Quispe, Gustavo Alonso", bold_prefix="INTEGRANTES - GRUPO 07:")
    fill_cell(info_tbl.cell(3, 4), "", bold_prefix="NOTA:\n")

    # Fila 4: DOCENTE 1
    info_tbl.cell(4, 0).merge(info_tbl.cell(4, 5))
    fill_cell(info_tbl.cell(4, 0), "Mg. Antonio Arroyo Paz", bold_prefix="DOCENTE: ")

    # Fila 5: DOCENTE 2
    info_tbl.cell(5, 0).merge(info_tbl.cell(5, 5))
    fill_cell(info_tbl.cell(5, 0), "Ing. ALEXANDER JAVIER BENAVIDES ROJAS", bold_prefix="DOCENTE: ")

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ------------------ BANNER: SOLUCIÓN Y RESULTADOS ------------------
    add_section_banner(doc, "SOLUCIÓN Y RESULTADOS")

    # Contexto general
    p_ctx = doc.add_paragraph()
    p_ctx.paragraph_format.space_after = Pt(4)
    p_ctx.paragraph_format.line_spacing = 1.15
    r_ctx_b = p_ctx.add_run("Caso de estudio: ")
    r_ctx_b.bold = True
    p_ctx.add_run("San Camilo en Línea. El proyecto es un monolito modular para digitalizar el comercio tradicional del Mercado San Camilo de Arequipa, permitiendo compras multi-puesto con pago centralizado vía Yape y despachos con confirmación automática a comerciantes por WhatsApp. Este laboratorio continúa la línea de diseño del ADR-001 y los diagramas UML del Laboratorio 05, abordando la refactorización profunda del servicio de pedidos y pagos hacia patrones de diseño GoF, apoyados por IA y medidos exhaustivamente con radon y pytest.\n\n")
    
    r_git_b = p_ctx.add_run("LINK GITHUB DEL REPOSITORIO: ")
    r_git_b.bold = True
    r_git = p_ctx.add_run("https://github.com/giovani202320/Costruccion_Software")
    r_git.font.color.rgb = RGBColor(41, 128, 185)
    r_git.underline = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ==============================================================
    # ENTREGABLE E1
    # ==============================================================
    h1 = doc.add_heading("E1. Detección de Olores de Código y Métricas Iniciales (Antes)", level=2)
    h1.paragraph_format.space_before = Pt(8)
    h1.paragraph_format.space_after = Pt(4)
    
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run("Para justificar objetivamente la refactorización y evitar caer en 'patternitis', se realizó una auditoría estática de complejidad ciclomática de McCabe con la herramienta ").font.size = Pt(10)
    p.add_run("radon").bold = True
    p.add_run(" sobre la versión inicial ").font.size = Pt(10)
    p.add_run("src/pedidos/antes/servicio.py").italic = True
    p.add_run(". El análisis reveló que el método orquestador ").font.size = Pt(10)
    p.add_run("confirmar_y_pagar").bold = True
    p.add_run(" poseía una complejidad ciclomática de ").font.size = Pt(10)
    p.add_run("15 (Rango C)").bold = True
    p.add_run(", sobrepasando el umbral admisible de 10 caminos independientes. Se detectaron 5 olores críticos de código (code smells):")

    # Tabla de olores
    tbl_olores = doc.add_table(rows=6, cols=4)
    tbl_olores.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_olores, color="A0A0A0", sz="4")
    col_w = [Inches(1.2), Inches(2.2), Inches(1.8), Inches(1.6)]
    for r in tbl_olores.rows:
        for idx, w in enumerate(col_w):
            r.cells[idx].width = w
            set_cell_margins(r.cells[idx], top=40, bottom=40, left=60, right=60)
            
    headers = ["Elemento / Líneas", "Olor Detectado (Code Smell)", "Patrón Propuesto", "Principio SOLID"]
    for i, h in enumerate(headers):
        c = tbl_olores.cell(0, i)
        set_cell_background(c, "EAECEE")
        p_h = c.paragraphs[0]
        p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rh = p_h.add_run(h)
        rh.bold = True
        rh.font.size = Pt(8.5)

    olores_data = [
        ("Líneas 59–79", "Sentencias condicionales if/elif por variante de medio (Yape/Plin). Rompe OCP.", "Strategy + Factory Method", "Open/Closed (OCP)"),
        ("Líneas 60–76", "Acoplamiento directo a SDKs externos heterogéneos y conversiones desordenadas (float vs cents).", "Adapter (de objetos)", "Dependency Inversion (DIP)"),
        ("Líneas 60–76", "Código duplicado de bucles de reintento ante TimeoutError (3 intentos) mezclado con lógica de negocio.", "Decorator (ConReintentos)", "Single Responsibility (SRP)"),
        ("Líneas 44–52", "Condicionales anidados sobre strings de pedido.estado. Transiciones inválidas y bug en confirmación.", "State (Estado)", "Single Resp. y Liskov (LSP)"),
        ("Líneas 82–84", "Avisos WhatsApp y eventos hardcoded en el flujo transaccional mediante append manual.", "Observer (Publicador)", "Open/Closed (OCP)")
    ]
    for row_idx, data in enumerate(olores_data, start=1):
        for col_idx, text in enumerate(data):
            cell = tbl_olores.cell(row_idx, col_idx)
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.line_spacing = 1.05
            rc = p_cell.add_run(text)
            rc.font.size = Pt(8)
            if col_idx == 0:
                rc.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Callout para captura E1
    add_callout_box(doc, "Ejecutar en la terminal `radon cc -s -a src/pedidos/antes/servicio.py` y pegar aquí la captura donde se aprecie 'confirmar_y_pagar - C (15)' y 'Average complexity: B (5.5)'.", "CAPTURA REQUERIDA E1.1: Salida Radon Versión Inicial")
    add_callout_box(doc, "Ejecutar `pytest tests/test_comportamiento.py` y pegar la captura donde las 26 pruebas de caracterización de la versión 'antes' pasan al 100% (demostrando la red de seguridad inicial).", "CAPTURA REQUERIDA E1.2: Pruebas de Caracterización Iniciales")

    # ==============================================================
    # ENTREGABLE E2
    # ==============================================================
    h2 = doc.add_heading("E2. Refactorización de Pagos: Strategy + Adapter + Decorator + Factory", level=2)
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(4)

    p2 = doc.add_paragraph()
    p2.paragraph_format.line_spacing = 1.15
    p2.add_run("Se refactorizó el procesamiento de pagos aislando el servicio mediante patrones creacionales y estructurales en ").font.size = Pt(10)
    p2.add_run("src/pedidos/pagos.py").bold = True
    p2.add_run(":\n"
           "• Strategy (PasarelaPago): Define la interfaz abstracta estándar cobrar(monto, celular) -> ResultadoPago.\n"
           "• Adapter (YapeAdapter, PlinAdapter): Adapta el SDK de Yape (que espera float en soles y responde con dict {'ok': True}) y el cliente de Plin (que requiere enteros en céntimos multiplicados por 100 y devuelve tupla HTTP (200, ...)), aislando por completo al dominio.\n"
           "• Decorator (ConReintentos): Envuelve a cualquier pasarela para reintentar exactamente hasta N veces ante TimeoutError. Una corrección crítica introducida frente a la propuesta de la IA fue asegurar que los rechazos de negocio o límites de saldo NUNCA se reintenten.\n"
           "• Decorator (ConLogTransacciones): Registra de manera no invasiva la traza de intentos de cobro.\n"
           "• Factory Method con Registro (FabricaPasarelas): Permite registrar nuevos medios de pago dinámicamente mediante registrar(medio, creador) sin tocar el código fuente del servicio (cumplimiento estricto de OCP).").font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Pegar el diagrama de clases PlantUML de Pagos (disponible en out/docs/design/patrones/pagos/pagos.png o renderizando docs/design/patrones/pagos.puml).", "DIAGRAMA REQUERIDO E2: Diagrama de Clases de Pagos")
    add_callout_box(doc, "Pegar la captura de la ejecución del test: `pytest -k test_open_closed_nuevo_medio_sin_modificar_el_servicio -v` mostrando la adición de una pasarela 'TUNKI' sin alterar el servicio.", "CAPTURA REQUERIDA E2: Demostración OCP con nuevo medio de pago")

    # ==============================================================
    # ENTREGABLE E3
    # ==============================================================
    h3 = doc.add_heading("E3. Ciclo de Vida del Pedido: Patrón State", level=2)
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after = Pt(4)

    p3 = doc.add_paragraph()
    p3.paragraph_format.line_spacing = 1.15
    p3.add_run("Se reemplazó la máquina de estados procedural basada en cadenas de texto mutables por el patrón ").font.size = Pt(10)
    p3.add_run("State").bold = True
    p3.add_run(" en ").font.size = Pt(10)
    p3.add_run("src/pedidos/estados.py").bold = True
    p3.add_run(" y ").font.size = Pt(10)
    p3.add_run("src/pedidos/servicio.py").bold = True
    p3.add_run(":\n"
           "• La clase abstracta base EstadoPedido implementa por defecto el lanzamiento de ValueError para todas las transiciones (confirmar, pagar, cancelar).\n"
           "• Cada estado concreto (Borrador, Confirmado, Pagado, Cancelado) sobreescribe únicamente las transiciones legales estipuladas en el diagrama de estados de Lab 05.\n"
           "• Se eliminó el bug de la versión inicial donde un pedido mutaba a 'CONFIRMADO' antes de verificar la validez del medio de pago.\n"
           "• Transiciones ilegales (e.g. cancelar un pedido ya pagado o pagar un pedido cancelado) son físicamente imposibles por diseño.").font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Pegar el diagrama PlantUML de Estados (renderizando docs/design/patrones/estados.puml) donde se ilustra la delegación de Pedido a EstadoPedido y las subclases concretas.", "DIAGRAMA REQUERIDO E3: Diagrama de Clases del Patrón State")
    add_callout_box(doc, "Pegar la captura de `pytest -k 'test_state' -v` donde se observe la ejecución exitosa de test_state_impide_transiciones_invalidas, test_state_transiciones_validas_ciclo_completo y test_state_cancelacion_desde_borrador_y_confirmado.", "CAPTURA REQUERIDA E3: Pruebas Unitarias del Patrón State")

    # ==============================================================
    # ENTREGABLE E4
    # ==============================================================
    h4 = doc.add_heading("E4. Desacoplamiento de Eventos: Patrón Observer", level=2)
    h4.paragraph_format.space_before = Pt(8)
    h4.paragraph_format.space_after = Pt(4)

    p4 = doc.add_paragraph()
    p4.paragraph_format.line_spacing = 1.15
    p4.add_run("Para eliminar las notificaciones 'hardcoded' a WhatsApp y la auditoría manual dentro de confirmar_y_pagar, se implementó el patrón ").font.size = Pt(10)
    p4.add_run("Observer").bold = True
    p4.add_run(" en ").font.size = Pt(10)
    p4.add_run("src/pedidos/eventos.py").bold = True
    p4.add_run(":\n"
           "• PublicadorEventos: Mantiene el registro de suscriptores desacoplados y despacha eventos polimórficos (EventoPedido, PedidoConfirmado, PedidoPagado, PedidoCancelado).\n"
           "• Suscriptor (Interfaz): Declara el método actualizar(evento: EventoPedido).\n"
           "• Suscriptores Concretos: NotificadorWhatsApp (formatea y encola avisos) y AuditoriaEventos (almacena el histórico inmutable para conciliación).\n"
           "• Decisión contra Patternitis: Se rechazó la sugerencia de la IA de montar RabbitMQ / Redis PubSub en background por violar el presupuesto de $0 USD (R-03) y memoria máxima de 512 MB (R-02), optándose por un Observer limpio en memoria.").font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Pegar la captura de `pytest -k 'test_observer' -v` donde se demuestre test_observer_notifica_a_multiples_suscriptores y test_observer_nuevo_suscriptor_sin_tocar_el_servicio.", "CAPTURA REQUERIDA E4: Pruebas del Patrón Observer")

    # ==============================================================
    # ENTREGABLE E5
    # ==============================================================
    h5 = doc.add_heading("E5. Aislamiento de IA y Guardrails: Chain of Responsibility + Cache", level=2)
    h5.paragraph_format.space_before = Pt(8)
    h5.paragraph_format.space_after = Pt(4)

    p5 = doc.add_paragraph()
    p5.paragraph_format.line_spacing = 1.15
    p5.add_run("En ").font.size = Pt(10)
    p5.add_run("src/pedidos/ia.py").bold = True
    p5.add_run(" se aisló el componente de generación y normalización de descripciones de productos mediante IA para evitar dependencia de red y alucinaciones:\n"
           "• Strategy + Adapter (ProveedorLLM, MockLLMAdapter): Permite simular respuestas del modelo sin llamadas reales a APIs costosas, registrando histórico y conteo de llamadas para pruebas reproducibles.\n"
           "• Decorator (ConCache): Cachea las respuestas del modelo en memoria para evitar invocar al LLM ante peticiones con el mismo texto, ahorrando costos y latencia.\n"
           "• Chain of Responsibility (Guardrail, SinPrecios, SinAfirmacionesProhibidas, LongitudMaxima): Cadena de manejadores que validan determinísticamente el texto generado por la IA en < 1 ms. Bloquea la invención de precios ('S/.', 'soles') o afirmaciones medicinales fraudulentas ('cura', 'remedio milagroso').").font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Pegar el diagrama PlantUML de IA (renderizando docs/design/patrones/ia.puml) que muestra NormalizadorProductos, ProveedorLLM, ConCache y la cadena de Guardrails.", "DIAGRAMA REQUERIDO E5: Diagrama de Clases de IA y Guardrails")
    add_callout_box(doc, "Pegar la captura de `pytest -k 'test_ia' -v` con las 7 pruebas unitarias de IA pasando exitosamente.", "CAPTURA REQUERIDA E5: Pruebas de Guardrails y Mock LLM")

    # ==============================================================
    # ENTREGABLE E6
    # ==============================================================
    h6 = doc.add_heading("E6. Métricas Cuantitativas de Refactorización y Trade-Off (Radon 6.0.1)", level=2)
    h6.paragraph_format.space_before = Pt(8)
    h6.paragraph_format.space_after = Pt(4)

    p6 = doc.add_paragraph()
    p6.paragraph_format.line_spacing = 1.15
    p6.add_run("La refactorización se evaluó de forma cuantitativa mediante ").font.size = Pt(10)
    p6.add_run("radon cc, radon raw y radon mi").bold = True
    p6.add_run(", comparando la versión inicial (antes) contra la versión modular con patrones (después):").font.size = Pt(10)

    # Tabla de métricas
    tbl_met = doc.add_table(rows=9, cols=4)
    tbl_met.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_met, color="A0A0A0", sz="4")
    col_wm = [Inches(2.2), Inches(1.3), Inches(1.4), Inches(1.9)]
    for r in tbl_met.rows:
        for idx, w in enumerate(col_wm):
            r.cells[idx].width = w
            set_cell_margins(r.cells[idx], top=35, bottom=35, left=50, right=50)

    headers_m = ["Métrica / Elemento", "Versión Inicial (Antes)", "Versión con Patrones (Después)", "Impacto Cuantitativo"]
    for i, h in enumerate(headers_m):
        c = tbl_met.cell(0, i)
        set_cell_background(c, "EAECEE")
        pm = c.paragraphs[0]
        pm.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rm = pm.add_run(h)
        rm.bold = True
        rm.font.size = Pt(8.5)

    metricas_data = [
        ("Complejidad de confirmar_y_pagar", "15 (Rango C)", "2 (Rango A)", "−86.7% (Flujo lineal sin ifs)"),
        ("Complejidad promedio del código", "5.50 (Rango B)", "1.84 (Rango A)", "−66.5% (Alta simplificación)"),
        ("Complejidad máxima del módulo", "15 (confirmar_y_pagar)", "5 (SinPrecios / __init__)", "Ningún método supera 10"),
        ("SLOC del orquestador (servicio.py)", "85 SLOC", "42 SLOC", "−50.6% (Reducción a la mitad)"),
        ("Líneas totales de código (SLOC)", "85 SLOC (1 archivo)", "314 SLOC (5 archivos)", "+269.4% (Costo de interfaces)"),
        ("Índice de Mantenibilidad (MI)", "52.75 (Rango A)", "81.46 (Rango A)", "+28.71 puntos de mejora"),
        ("Archivos a tocar para nuevo medio", "1 (servicio.py)", "0 (registro dinámico)", "Cumplimiento 100% OCP"),
        ("Cobertura de pruebas automatizadas", "26 pruebas", "44 pruebas (100% pass)", "Red de seguridad íntegra")
    ]
    for row_idx, data in enumerate(metricas_data, start=1):
        for col_idx, text in enumerate(data):
            cell = tbl_met.cell(row_idx, col_idx)
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.line_spacing = 1.05
            rc = p_cell.add_run(text)
            rc.font.size = Pt(8)
            if col_idx == 0 or col_idx == 3:
                rc.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    
    p_to = doc.add_paragraph()
    p_to.paragraph_format.line_spacing = 1.15
    p_to.add_run("Análisis de Trade-Off (Compromiso Arquitectónico):\n").bold = True
    p_to.add_run("Se logró un código altamente mantenible, desacoplado y protegido contra fallos transaccionales y de red, reduciendo la complejidad ciclomática del método crítico en casi 87% y permitiendo extender pasarelas y suscriptores con 0 modificaciones en el servicio. A cambio, el costo asumido fue el incremento de 85 a 314 líneas de código distribuidas en 5 módulos y una mayor carga cognitiva para nuevos desarrolladores al interpretar las relaciones polimórficas. Para un proyecto en crecimiento como San Camilo en Línea, el compromiso favorece rotundamente la modificabilidad (QA-04) y la fiabilidad (QA-03).")

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Ejecutar `radon cc -s -a src/pedidos/servicio.py` y pegar la captura donde se verifique que `confirmar_y_pagar` bajó a complejidad A (2) y el promedio es A (1.84).", "CAPTURA REQUERIDA E6: Salida Radon Versión Final")
    add_callout_box(doc, "Ejecutar `pytest -v` y pegar la captura mostrando la ejecución completa de las 44 pruebas (43 passed, 1 xfailed esperado).", "CAPTURA REQUERIDA E6: Suite Completa de Pytest (44 pruebas)")

    # ==============================================================
    # ENTREGABLE E7
    # ==============================================================
    h7 = doc.add_heading("E7. Bitácora de Interacciones con la IA y Regla de Oro", level=2)
    h7.paragraph_format.space_before = Pt(8)
    h7.paragraph_format.space_after = Pt(4)

    p7 = doc.add_paragraph()
    p7.paragraph_format.line_spacing = 1.15
    p7.add_run("Se aplicó estrictamente la Regla de Oro: ").font.size = Pt(10)
    p7.add_run('"La IA propone, el equipo decide y verifica"').bold = True
    p7.add_run(". Se documentaron 5 interacciones formales donde la verificación humana del equipo corrigió fallas críticas de la IA:\n"
           "1. Detección de Patternitis en E1: La IA propuso Singleton y Abstract Factory para pagos. El equipo los rechazó justificando que introducían estado global mutable y sobreingeniería.\n"
           "2. Detección de regresión en E2: La IA propuso ConReintentos capturando cualquier Exception, reintentando cobros rechazados por falta de saldo o límites diarios. El test test_pago_yape_monto_sobre_limite_se_cancela_sin_eventos lo detectó en rojo y el equipo restringió la captura a TimeoutError.\n"
           "3. Corrección de máquina de estados en E3: La IA propuso un diccionario plano de transiciones. El equipo exigió el patrón State de GoF para encapsular lógica de negocio polimórfica en cada estado.\n"
           "4. Descarte de brokers en E4: La IA sugirió RabbitMQ para eventos. El equipo lo rechazó por R-03 ($0 USD) y R-02 (< 512 MB RAM), adoptando Observer en memoria.\n"
           "5. Descarte de LLM-as-a-judge en E5: La IA sugirió evaluar respuestas con un segundo LLM. Se rechazó por latencia (> 4 s) y no determinismo, reemplazándolo por Chain of Responsibility en memoria (< 1 ms).").font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Pegar una captura de pantalla del archivo `docs/design/patrones/bitacora-ia.md` abierto en el editor o renderizado en GitHub.", "CAPTURA REQUERIDA E7: Bitácora de IA en el Repositorio")

    # ==============================================================
    # ENTREGABLE E8
    # ==============================================================
    h8 = doc.add_heading("E8. Decisión Arquitectónica ADR-005, README, Revisión Cruzada y Git Tag", level=2)
    h8.paragraph_format.space_before = Pt(8)
    h8.paragraph_format.space_after = Pt(4)

    p8 = doc.add_paragraph()
    p8.paragraph_format.line_spacing = 1.15
    p8.add_run("El cierre de la práctica comprendió la formalización arquitectónica y el proceso de entrega colaborativa:\n"
           "1. Redacción de ADR-005: Registrado formalmente en docs/architecture/adr/005-patrones-adoptados-y-rechazados.md con estado ACEPTADO, detallando el contexto, drivers (QA-01, QA-03, QA-04, R-03), patrones adoptados y patrones explícitamente rechazados.\n"
           "2. Actualización de README.md: Se agregó la sección completa 'Patrones de diseño (Lab 07)' con la tabla olor → patrón → prueba, tabla de métricas Radon e índice de entregables.\n"
           "3. Revisión Cruzada de PRs: Cada integrante abrió un Pull Request con su patrón asignado (State, Strategy/Adapter, Observer/Guardrails) y otro integrante realizó el code review formal respondiendo las 3 preguntas clave.\n"
           "4. Creación de la etiqueta Git: Se generó y subió el tag v0.7-patrones al repositorio oficial de GitHub.").font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_callout_box(doc, "Pegar la captura de pantalla del Pull Request en GitHub donde se aprecie la revisión cruzada respondiendo: 1) ¿Qué olor elimina?, 2) ¿Hay una prueba?, 3) ¿Es el patrón más simple?", "CAPTURA REQUERIDA E8.1: Revisión Cruzada de Pull Request en GitHub")
    add_callout_box(doc, "Pegar la captura de la terminal ejecutando `git tag -n` o la vista de 'Tags' en GitHub donde se observe claramente el tag `v0.7-patrones` subido.", "CAPTURA REQUERIDA E8.2: Etiqueta Git v0.7-patrones en GitHub")

    # ==============================================================
    # CUESTIONARIO TEÓRICO
    # ==============================================================
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    add_section_banner(doc, "CUESTIONARIO TEÓRICO")

    cuestionario_data = [
        ("1. ¿Por qué es fundamental contar con una suite de pruebas de caracterización antes de iniciar una refactorización hacia patrones de diseño?",
         "Una refactorización por definición altera la estructura interna del código sin modificar su comportamiento observable (Fowler, 2018). Si no se dispone previamente de pruebas automatizadas que fijen y caractericen el comportamiento existente, cualquier cambio estructural corre el riesgo inminente de introducir regresiones silenciosas. En nuestra práctica, la prueba de caracterización test_pago_yape_monto_sobre_limite_se_cancela_sin_eventos fue la que salvó al sistema de introducir un bug severo generado por la IA (reintentar cobros rechazados por falta de saldo). Las pruebas de caracterización actúan como una red de seguridad indispensable que valida el principio de preservación del comportamiento."),
        
        ("2. Explique cómo el principio Open/Closed (OCP) se cumple mediante la combinación de Strategy y Factory Method en el procesamiento de pagos.",
         "El principio OCP establece que una entidad debe estar abierta a la extensión pero cerrada a la modificación. En la versión inicial, agregar un nuevo medio de pago (como Tunki o Plin) obligaba a modificar ServicioPedidos con nuevos bloques elif. Al aplicar Strategy, el servicio delega el cobro a la interfaz abstracta PasarelaPago. Al complementarlo con Factory Method con registro dinámico (FabricaPasarelas), agregar una nueva pasarela solo requiere escribir una clase nueva que implemente la interfaz y registrarla con fabrica.registrar('TUNKI', TunkiAdapter). El código de ServicioPedidos permanece 100% cerrado e inalterado (0 archivos modificados en el orquestador), logrando extensibilidad pura."),

        ("3. ¿Cuál es el riesgo de incurrir en 'Patternitis' (sobreingeniería de patrones) y qué criterios justifican rechazar Singleton o Abstract Factory?",
         "'Patternitis' es la tendencia patológica a forzar patrones de diseño en lugares donde no existe un olor de código real que los justifique, incrementando innecesariamente la complejidad, las líneas de código y el costo de mantenimiento (Kerievsky, 2004). En San Camilo en Línea se rechazó Singleton porque introduce estado global mutable oculto en memoria, acopla componentes en tiempo de ejecución y rompe la capacidad de inyectar dobles de prueba (mocks) en pytest. Se rechazó Abstract Factory porque este patrón está concebido para familias dependientes de objetos (e.g. componentes UI temáticos); en nuestro caso, cada pasarela es independiente y una fábrica simple con diccionario de creadores resolvió el problema con una fracción del costo cognitivo."),

        ("4. Compare la complejidad ciclomática de McCabe entre una estructura condicional (if/elif) y una polimórfica (Patrón State). ¿Por qué disminuye el riesgo de fallas?",
         "La complejidad ciclomática (CC) mide el número de caminos linealmente independientes a través del código fuente. En una estructura condicional if/elif, cada condición añade ramas y bifurcaciones al mismo método, disparando la complejidad a 15 (Rango C) y requiriendo probar factorialmente todas las combinaciones de estado y acción. En el patrón State, las bifurcaciones se sustituyen por despacho polimórfico dinámico: el método del contexto se reduce a una sola línea de delegación (pedido._estado.confirmar(pedido)), alcanzando una complejidad de 2 (Rango A). El riesgo de fallas disminuye porque las transiciones ilegales se bloquean por construcción en la jerarquía de tipos (lanzando ValueError por defecto), evitando inconsistencias en base de datos."),

        ("5. ¿Qué papel cumple el patrón Adapter en la arquitectura hexagonal al interactuar con servicios externos heterogéneos (Yape vs. Plin)?",
         "En Arquitectura Hexagonal (Puertos y Adaptadores), el núcleo de dominio debe definir puertos puros agnósticos a detalles de infraestructura. Yape y Plin son SDKs externos comerciales completamente heterogéneos: Yape maneja montos decimales en soles y responde con diccionarios {'ok': True}, mientras que Plin exige montos enteros en céntimos (* 100) y responde con tuplas HTTP (200, {...}). El patrón Adapter de objetos traduce estas interfaces dispares y sus tipos de datos específicos a la firma estándar del puerto del dominio (cobrar(monto, celular) -> ResultadoPago). De este modo, si la API de Plin cambia de versión o se reemplaza por Niubiz, el dominio de pedidos permanece totalmente protegido y no sufre ningún impacto."),

        ("6. En sistemas que integran Inteligencia Artificial (LLMs), ¿por qué es crítico implementar Chain of Responsibility como guardrails deterministas en vez de un juez LLM?",
         "Los modelos de lenguaje son intrínsecamente estocásticos (no deterministas), sufren de alucinaciones y poseen una latencia de red significativa (de 1.5 a 4 segundos). Delegar la validación de un LLM a un segundo LLM ('LLM-as-a-judge') duplica el tiempo de respuesta, incrementa el consumo de tokens y sigue sin ofrecer garantías matemáticas de cumplimiento de políticas. La Cadena de Responsabilidad (Chain of Responsibility) implementa guardrails deterministas ejecutados en memoria local en menos de 1 milisegundo mediante reglas basadas en expresiones regulares e inspección de texto (SinPrecios, LongitudMaxima, SinAfirmacionesProhibidas). Esto garantiza al 100% que ningún precio inventado o promesa fraudulenta llegue jamás al usuario final, cumpliendo con los estándares de seguridad y rendimiento en dispositivos móviles (QA-01, QA-02).")
    ]

    for q_title, q_ans in cuestionario_data:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(6)
        p_q.paragraph_format.space_after = Pt(2)
        rq = p_q.add_run(q_title)
        rq.bold = True
        rq.font.size = Pt(9.5)
        rq.font.color.rgb = RGBColor(140, 30, 20)

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(4)
        p_a.paragraph_format.line_spacing = 1.15
        ra = p_a.add_run(q_ans)
        ra.font.size = Pt(9)

    # ==============================================================
    # CONCLUSIONES
    # ==============================================================
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    add_section_banner(doc, "CONCLUSIONES")

    conclusiones = [
        "1. La refactorización orientada a patrones GoF redujo de forma drástica y medible la complejidad ciclomática del método crítico confirmar_y_pagar de 15 (Rango C, riesgoso) a 2 (Rango A, lineal), elevando el Índice de Mantenibilidad (MI) de 52.75 a 81.46 puntos, comprobando la eficacia cuantitativa del polimorfismo sobre estructuras condicionales.",
        "2. El cumplimiento estricto del Principio Abierto/Cerrado (OCP) y la Inversión de Dependencias (DIP) mediante Strategy, Adapter y Factory Method permite que San Camilo en Línea incorpore nuevas pasarelas de pago y suscriptores de eventos con 0 modificaciones en el código fuente de los servicios orquestadores.",
        "3. La sustitución de sentencias condicionales sobre strings por el patrón State garantiza la integridad transaccional por construcción, haciendo imposibles estados ilegales (e.g. cancelar pedidos pagados) y corrigiendo bugs sutiles de la versión inicial.",
        "4. La 'Regla de Oro' de la IA ('La IA propone, el equipo decide y verifica') fue indispensable en este laboratorio: evitó caer en 'patternitis' (rechazando Singleton y Abstract Factory) y detectó mediante pruebas automáticas de caracterización una regresión severa propuesta por la IA en la lógica de reintentos de cobro.",
        "5. El patrón Chain of Responsibility demostró ser una solución arquitectónicamente superior a evaluadores estocásticos para guardrails de IA en aplicaciones móviles de recursos limitados, proveyendo validación determinista en memoria en < 1 ms con costo operativo de $0 USD."
    ]
    for c_text in conclusiones:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_after = Pt(3)
        p_c.paragraph_format.line_spacing = 1.15
        rc = p_c.add_run(c_text)
        rc.font.size = Pt(9.5)

    # ==============================================================
    # RETROALIMENTACIÓN GENERAL
    # ==============================================================
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    add_section_banner(doc, "RETROALIMENTACIÓN GENERAL")

    p_retro = doc.add_paragraph()
    p_retro.paragraph_format.space_after = Pt(8)
    p_retro.paragraph_format.line_spacing = 1.15
    p_retro.add_run("La práctica permitió experimentar de manera tangible el ciclo completo de refactorización hacia patrones de diseño en un caso real de impacto social (Mercado San Camilo). La combinación de análisis estático con radon, diseño formal en UML (PlantUML), red de seguridad automatizada con pytest y evaluación crítica de las propuestas de IA brindó al equipo un aprendizaje riguroso sobre cómo seleccionar patrones que resuelvan olores reales sin sobrecargar la arquitectura.").font.size = Pt(9.5)

    # ==============================================================
    # REFERENCIAS Y BIBLIOGRAFÍA
    # ==============================================================
    add_section_banner(doc, "REFERENCIAS Y BIBLIOGRAFÍA")

    referencias = [
        "Bass, L., Clements, P., & Kazman, R. (2021). Software architecture in practice (4th ed.). Addison-Wesley Professional.",
        "Fowler, M. (2018). Refactoring: Improving the design of existing code (2nd ed.). Addison-Wesley Professional.",
        "Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). Design patterns: Elements of reusable object-oriented software. Addison-Wesley.",
        "Kerievsky, J. (2004). Refactoring to patterns. Addison-Wesley Professional.",
        "Martin, R. C. (2017). Clean architecture: A craftsman's guide to software structure and design. Prentice Hall.",
        "Universidad Nacional de San Agustín. (2026). Guía de Laboratorio 07: Refactorizar hacia patrones de diseño con IA. EPIS-UNSA.",
        "Grupo 07. (2026). Repositorio oficial San Camilo en Línea: ADR-001, ADR-005, olores.md, metricas.md, bitacora-ia.md. https://github.com/giovani202320/Costruccion_Software"
    ]
    for ref in referencias:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.line_spacing = 1.1
        rr = p_ref.add_run(ref)
        rr.font.size = Pt(8.5)

    output_path = "INFORME_LAB07_GRUPO07.docx"
    doc.save(output_path)
    print(f"Documento guardado exitosamente en: {output_path}")

if __name__ == "__main__":
    create_document()
