from __future__ import annotations

from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from balanceo import intentar_balanceo_por_conductancia
from clasificacion import AMARILLO, ROJO, VERDE, ClasificacionEspacio, clasificar_espacio
from datos_ejemplo import CRITERIOS_EJEMPLO, construir_edificio_ejemplo
from estructuras import construir_indice_por_temperatura
from evaluacion import ResultadoEvaluacion, evaluar_espacios, resumen_cumplimiento
from simulacion import ResultadoSimulacion, simular
from visualizacion import generar_svg_grafo


TEMPERATURA_EXTERIOR = 32.0
DURACION_SEGUNDOS = 2 * 60 * 60
PASO_SEGUNDOS = 60.0
ARCHIVO_XLSX = "historial_temperaturas.xlsx"
ARCHIVO_SVG = "grafo_habitabilidad.svg"


def mostrar_espacios_y_conexiones(edificio) -> None:
    print(f"\nEdificio: {edificio.nombre} ({edificio.id})")
    print("\nEspacios:")
    for espacio in edificio.espacios():
        print(
            f"- {espacio.id} | piso {espacio.piso} | {espacio.nombre} | "
            f"actividad={espacio.actividad} | T0={espacio.temperatura_inicial:.1f} C | "
            f"C={espacio.capacidad_termica:.0f} J/K | "
            f"G_ext={espacio.conductancia_exterior:.1f} W/K | "
            f"Q={espacio.fuente_interna:.1f} W"
        )

    print("\nConexiones termicas:")
    for conexion in edificio.conexiones:
        print(
            f"- {conexion.espacio_a} <-> {conexion.espacio_b} | "
            f"G={conexion.conductancia:.1f} W/K"
        )


def mostrar_historial_muestreado(resultado: ResultadoSimulacion, cada_n_pasos: int = 20) -> None:
    print("\nEvolucion de temperatura (muestra):")
    encabezado = ["tiempo_min"] + list(resultado.historial.keys())
    print(" | ".join(f"{col:>10}" for col in encabezado))
    print("-" * (13 * len(encabezado)))

    indices = list(range(0, len(resultado.tiempos), cada_n_pasos))
    if indices[-1] != len(resultado.tiempos) - 1:
        indices.append(len(resultado.tiempos) - 1)

    for indice in indices:
        fila = [f"{resultado.tiempos[indice] / 60:10.0f}"]
        for valores in resultado.historial.values():
            fila.append(f"{valores[indice]:10.2f}")
        print(" | ".join(fila))


def mostrar_evaluacion(resultados) -> None:
    print("\nEvaluacion termica final:")
    encabezado = [
        "id",
        "piso",
        "nombre",
        "actividad",
        "T inicial",
        "T final",
        "intervalo",
        "estado",
    ]
    print(" | ".join(encabezado))
    print("-" * 132)

    for resultado in resultados:
        intervalo = f"{resultado.minimo:.1f}-{resultado.maximo:.1f} C"
        print(
            f"{resultado.espacio_id} | {resultado.piso} | {resultado.nombre} | "
            f"{resultado.actividad} | {resultado.temperatura_inicial:.2f} C | "
            f"{resultado.temperatura_final:.2f} C | {intervalo} | {resultado.estado}"
        )

    cumplen, no_cumplen = resumen_cumplimiento(resultados)
    estado_edificio = "NO conforme" if no_cumplen else "conforme"
    print(
        f"\nResumen: {cumplen} espacios cumplen y {no_cumplen} no cumplen. "
        f"Resultado del edificio segun este criterio academico: {estado_edificio}."
    )


def clasificar_edificio(
    edificio,
    resultados: list[ResultadoEvaluacion],
) -> list[ClasificacionEspacio]:
    """Clasifica cada espacio en verde/amarillo/rojo.

    Para los espacios que no cumplen, primero intenta un balanceo del grafo
    (subir la conductancia hacia algun vecino) como alternativa pasiva y
    mas barata; si no alcanza, evalua una solucion activa de climatizacion.
    Se queda con la mas economica de las dos. Si ninguna es viable dentro
    de los limites configurados, el espacio queda en rojo: no habitable y
    sin solucion.
    """
    clasificaciones = []
    for resultado in resultados:
        solucion_balanceo = None
        if not resultado.cumple:
            propuesta = intentar_balanceo_por_conductancia(
                edificio,
                resultado.espacio_id,
                CRITERIOS_EJEMPLO,
                TEMPERATURA_EXTERIOR,
                DURACION_SEGUNDOS,
                PASO_SEGUNDOS,
            )
            solucion_balanceo = propuesta

        clasificaciones.append(
            clasificar_espacio(
                resultado,
                capacidad_termica=edificio.espacio(resultado.espacio_id).capacidad_termica,
                duracion_segundos=DURACION_SEGUNDOS,
                solucion_balanceo=solucion_balanceo,
            )
        )
    return clasificaciones


def mostrar_clasificacion(clasificaciones: list[ClasificacionEspacio]) -> None:
    print("\nClasificacion de habitabilidad por colores:")
    conteo = {VERDE: 0, AMARILLO: 0, ROJO: 0}

    for clasificacion in clasificaciones:
        conteo[clasificacion.color] += 1
        etiqueta = clasificacion.color.upper()
        print(f"\n- [{etiqueta}] {clasificacion.espacio_id} ({clasificacion.resultado.nombre})")
        if clasificacion.color == VERDE:
            print("   Habitable segun el criterio configurado.")
        elif clasificacion.color == AMARILLO:
            print(f"   Solucion: {clasificacion.solucion.descripcion()}")
        else:
            print("   No habitable y sin solucion viable dentro de los limites configurados.")

    print(
        f"\nResumen por color: {conteo[VERDE]} verde(s), "
        f"{conteo[AMARILLO]} amarillo(s), {conteo[ROJO]} rojo(s)."
    )


def mostrar_indice_arbol_b(clasificaciones: list[ClasificacionEspacio]) -> None:
    resultados = [c.resultado for c in clasificaciones]
    indice = construir_indice_por_temperatura(resultados)

    print(
        f"\nIndice (arbol B) de espacios por temperatura final "
        f"(altura={indice.altura()}):"
    )
    for temperatura, espacio_id in indice.recorrido_ordenado():
        print(f"- {temperatura:6.2f} C -> {espacio_id}")

    minimo = min(r.temperatura_final for r in resultados)
    maximo = max(r.temperatura_final for r in resultados)
    rango_bajo = minimo
    rango_alto = minimo + (maximo - minimo) / 2
    espacios_en_rango = indice.buscar_rango(rango_bajo, rango_alto)
    print(
        f"\nConsulta de ejemplo sobre el arbol B: espacios con temperatura "
        f"final entre {rango_bajo:.2f} C y {rango_alto:.2f} C:"
    )
    for temperatura, espacio_id in espacios_en_rango:
        print(f"- {espacio_id}: {temperatura:.2f} C")


def _celda_xlsx(valor, fila: int, columna: int) -> str:
    letras = ""
    numero_columna = columna
    while numero_columna:
        numero_columna, residuo = divmod(numero_columna - 1, 26)
        letras = chr(65 + residuo) + letras

    referencia = f"{letras}{fila}"
    if isinstance(valor, str):
        return (
            f'<c r="{referencia}" t="inlineStr">'
            f"<is><t>{escape(valor)}</t></is>"
            "</c>"
        )
    return f'<c r="{referencia}"><v>{valor}</v></c>'


def _filas_a_hoja_xml(filas: list[list], congelar_fila: bool = False) -> str:
    filas_xml = []
    for numero_fila, fila in enumerate(filas, start=1):
        celdas = [
            _celda_xlsx(valor, numero_fila, numero_columna)
            for numero_columna, valor in enumerate(fila, start=1)
        ]
        filas_xml.append(f'<row r="{numero_fila}">{"".join(celdas)}</row>')

    vista = ""
    if congelar_fila:
        vista = (
            '<sheetViews><sheetView workbookViewId="0">'
            '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
            "</sheetView></sheetViews>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{vista}"
        '<cols><col min="1" max="1" width="18" customWidth="1"/>'
        '<col min="2" max="2" width="18" customWidth="1"/>'
        '<col min="3" max="20" width="28" customWidth="1"/></cols>'
        f'<sheetData>{"".join(filas_xml)}</sheetData>'
        "</worksheet>"
    )


def exportar_historial_xlsx(
    resultado: ResultadoSimulacion,
    edificio,
    clasificaciones: list[ClasificacionEspacio],
    ruta: str,
) -> None:
    ids_espacios = list(resultado.historial.keys())
    encabezados_temperatura = [
        f"{espacio_id} - {edificio.espacio(espacio_id).nombre} "
        f"({edificio.espacio(espacio_id).actividad}) [C]"
        for espacio_id in ids_espacios
    ]
    filas_historial = [["tiempo_segundos", "tiempo_minutos", *encabezados_temperatura]]
    for indice, tiempo in enumerate(resultado.tiempos):
        filas_historial.append(
            [tiempo, round(tiempo / 60, 2)]
            + [
                round(resultado.historial[espacio_id][indice], 4)
                for espacio_id in ids_espacios
            ]
        )

    filas_leyenda = [
        ["Simulador inicial de habitabilidad termica"],
        [""],
        ["Que contiene este archivo"],
        ["Historial", "Temperatura simulada de cada espacio en cada paso de tiempo."],
        ["Leyenda", "Unidades, criterios configurados e instrucciones basicas."],
        [""],
        ["Parametros de simulacion"],
        ["Temperatura exterior [C]", TEMPERATURA_EXTERIOR],
        ["Duracion [segundos]", DURACION_SEGUNDOS],
        ["Duracion [horas]", round(DURACION_SEGUNDOS / 3600, 2)],
        ["Paso de tiempo [segundos]", PASO_SEGUNDOS],
        [""],
        ["Unidades"],
        ["Temperatura", "Grados Celsius [C]"],
        ["Tiempo", "Segundos y minutos"],
        ["Capacidad termica", "J/K"],
        ["Conductancia", "W/K"],
        ["Fuente interna", "W"],
        [""],
        ["Criterios termicos configurados"],
        ["Actividad", "Minimo [C]", "Maximo [C]"],
    ]
    for actividad, (minimo, maximo) in CRITERIOS_EJEMPLO.items():
        filas_leyenda.append([actividad, minimo, maximo])

    filas_leyenda.extend(
        [
            [""],
            ["Espacios del edificio"],
            [
                "ID",
                "Piso",
                "Nombre",
                "Actividad",
                "Temperatura inicial [C]",
                "Capacidad termica [J/K]",
                "Conductancia exterior [W/K]",
                "Fuente interna [W]",
            ],
        ]
    )
    for espacio in edificio.espacios():
        filas_leyenda.append(
            [
                espacio.id,
                espacio.piso,
                espacio.nombre,
                espacio.actividad,
                espacio.temperatura_inicial,
                espacio.capacidad_termica,
                espacio.conductancia_exterior,
                espacio.fuente_interna,
            ]
        )

    filas_leyenda.extend(
        [
            [""],
            ["Conexiones termicas"],
            ["Espacio A", "Espacio B", "Conductancia [W/K]"],
        ]
    )
    for conexion in edificio.conexiones:
        filas_leyenda.append(
            [conexion.espacio_a, conexion.espacio_b, conexion.conductancia]
        )

    filas_leyenda.extend(
        [
            [""],
            ["Mini instrucciones para cambiar el ejemplo"],
            ["Cambiar espacios", "Editar la lista de Espacio(...) en datos_ejemplo.py."],
            ["Cambiar actividades", "Modificar el campo actividad de cada Espacio y CRITERIOS_EJEMPLO."],
            ["Cambiar conexiones", "Editar la lista de ConexionTermica(...) en datos_ejemplo.py."],
            ["Cambiar tiempo exterior", "Modificar TEMPERATURA_EXTERIOR en main.py."],
            ["Cambiar duracion", "Modificar DURACION_SEGUNDOS en main.py."],
            ["Cambiar paso", "Modificar PASO_SEGUNDOS en main.py."],
            ["Cambiar costos de solucion", "Modificar las constantes en clasificacion.py (climatizacion) y balanceo.py (balanceo de conductancia)."],
            ["Regenerar Excel y grafo SVG", "Guardar cambios y ejecutar: python main.py"],
            ["Nota", "Los datos son ilustrativos, no mediciones reales ni certificacion legal."],
        ]
    )

    filas_clasificacion = [
        [
            "ID",
            "Nombre",
            "Color",
            "T final [C]",
            "Intervalo",
            "Solucion propuesta",
            "Costo estimado [COP]",
        ]
    ]
    for clasificacion in clasificaciones:
        resultado_espacio = clasificacion.resultado
        intervalo = f"{resultado_espacio.minimo:.1f}-{resultado_espacio.maximo:.1f} C"
        if clasificacion.color == VERDE:
            solucion_texto, costo_texto = "No aplica (habitable)", ""
        elif clasificacion.color == AMARILLO:
            solucion_texto = clasificacion.solucion.descripcion()
            costo_texto = round(clasificacion.solucion.costo_cop, 0)
        else:
            solucion_texto, costo_texto = "Sin solucion viable", ""

        filas_clasificacion.append(
            [
                clasificacion.espacio_id,
                resultado_espacio.nombre,
                clasificacion.color,
                round(resultado_espacio.temperatura_final, 2),
                intervalo,
                solucion_texto,
                costo_texto,
            ]
        )

    hoja_historial_xml = _filas_a_hoja_xml(filas_historial, congelar_fila=True)
    hoja_leyenda_xml = _filas_a_hoja_xml(filas_leyenda)
    hoja_clasificacion_xml = _filas_a_hoja_xml(filas_clasificacion, congelar_fila=True)

    with ZipFile(ruta, "w", ZIP_DEFLATED) as archivo:
        archivo.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/worksheets/sheet2.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/worksheets/sheet3.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>",
        )
        archivo.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        archivo.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Historial" sheetId="1" r:id="rId1"/>'
            '<sheet name="Leyenda" sheetId="2" r:id="rId2"/>'
            '<sheet name="Clasificacion" sheetId="3" r:id="rId3"/></sheets>'
            "</workbook>",
        )
        archivo.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet2.xml"/>'
            '<Relationship Id="rId3" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet3.xml"/>'
            "</Relationships>",
        )
        archivo.writestr("xl/worksheets/sheet1.xml", hoja_historial_xml)
        archivo.writestr("xl/worksheets/sheet2.xml", hoja_leyenda_xml)
        archivo.writestr("xl/worksheets/sheet3.xml", hoja_clasificacion_xml)


def main() -> None:
    edificio = construir_edificio_ejemplo()
    mostrar_espacios_y_conexiones(edificio)

    print(
        "\nDatos de simulacion: "
        f"T_ext={TEMPERATURA_EXTERIOR:.1f} C, "
        f"duracion={DURACION_SEGUNDOS / 3600:.1f} h, "
        f"paso={PASO_SEGUNDOS:.0f} s."
    )

    resultado = simular(
        edificio,
        temperatura_exterior=TEMPERATURA_EXTERIOR,
        duracion_segundos=DURACION_SEGUNDOS,
        paso_segundos=PASO_SEGUNDOS,
    )
    mostrar_historial_muestreado(resultado)

    evaluacion = evaluar_espacios(
        edificio,
        resultado.temperaturas_finales(),
        CRITERIOS_EJEMPLO,
    )
    mostrar_evaluacion(evaluacion)

    clasificaciones = clasificar_edificio(edificio, evaluacion)
    mostrar_clasificacion(clasificaciones)
    mostrar_indice_arbol_b(clasificaciones)

    exportar_historial_xlsx(resultado, edificio, clasificaciones, ARCHIVO_XLSX)
    print(f"\nHistorial exportado a: {ARCHIVO_XLSX}")

    generar_svg_grafo(edificio, clasificaciones, ARCHIVO_SVG)
    print(f"Grafo coloreado exportado a: {ARCHIVO_SVG}")

    print(
        "\nNota: este resultado no es una certificacion legal de habitabilidad. "
        "Solo evalua temperatura con un modelo simplificado e ilustrativo."
    )


if __name__ == "__main__":
    main()
