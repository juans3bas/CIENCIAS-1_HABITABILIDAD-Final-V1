from __future__ import annotations

from xml.sax.saxutils import escape

from clasificacion import AMARILLO, ROJO, VERDE, ClasificacionEspacio
from modelos import Edificio

_COLOR_HEX = {
    VERDE: "#2e7d32",
    AMARILLO: "#f9a825",
    ROJO: "#c62828",
}

_RADIO_NODO = 34
_ANCHO_COLUMNA = 210
_ALTO_FILA = 220
_MARGEN_X = 115
_MARGEN_Y = 90
_ALTO_LEYENDA = 150


def _posiciones_por_piso(edificio: Edificio) -> dict[str, tuple[float, float]]:
    posiciones: dict[str, tuple[float, float]] = {}
    pisos_ordenados = sorted({espacio.piso for espacio in edificio.espacios()})
    indice_piso = {piso: indice for indice, piso in enumerate(pisos_ordenados)}

    espacios_por_piso: dict[int, list[str]] = {}
    for espacio in edificio.espacios():
        espacios_por_piso.setdefault(espacio.piso, []).append(espacio.id)

    for piso, ids in espacios_por_piso.items():
        fila = indice_piso[piso]
        for columna, espacio_id in enumerate(sorted(ids)):
            x = _MARGEN_X + columna * _ANCHO_COLUMNA
            y = _MARGEN_Y + fila * _ALTO_FILA
            posiciones[espacio_id] = (x, y)

    return posiciones


def generar_svg_grafo(
    edificio: Edificio,
    clasificaciones: list[ClasificacionEspacio],
    ruta: str,
) -> None:
    posiciones = _posiciones_por_piso(edificio)
    clasificacion_por_id = {c.espacio_id: c for c in clasificaciones}

    max_x = max((x for x, _ in posiciones.values()), default=0) + _MARGEN_X
    max_y = max((y for _, y in posiciones.values()), default=0) + _MARGEN_Y + _ALTO_LEYENDA

    partes: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x:.0f}" '
        f'height="{max_y:.0f}" viewBox="0 0 {max_x:.0f} {max_y:.0f}" '
        f'font-family="Arial, sans-serif">',
        f'<rect x="0" y="0" width="{max_x:.0f}" height="{max_y:.0f}" fill="#ffffff"/>',
        '<text x="20" y="30" font-size="20" font-weight="bold">'
        "Grafo de habitabilidad termica</text>",
    ]

    for conexion in edificio.conexiones:
        x1, y1 = posiciones[conexion.espacio_a]
        x2, y2 = posiciones[conexion.espacio_b]
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        partes.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            'stroke="#90a4ae" stroke-width="2"/>'
        )
        partes.append(
            f'<rect x="{xm - 24:.0f}" y="{ym - 10:.0f}" width="48" height="16" '
            'fill="#ffffff" opacity="0.85"/>'
        )
        partes.append(
            f'<text x="{xm:.0f}" y="{ym + 2:.0f}" font-size="11" '
            'text-anchor="middle" fill="#455a64">'
            f"{conexion.conductancia:.1f} W/K</text>"
        )

    for espacio in edificio.espacios():
        x, y = posiciones[espacio.id]
        clasificacion = clasificacion_por_id.get(espacio.id)
        color = _COLOR_HEX.get(clasificacion.color, "#9e9e9e") if clasificacion else "#9e9e9e"

        partes.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{_RADIO_NODO}" '
            f'fill="{color}" stroke="#263238" stroke-width="1.5"/>'
        )
        partes.append(
            f'<text x="{x:.0f}" y="{y - 2:.0f}" font-size="13" font-weight="bold" '
            'text-anchor="middle" fill="#ffffff">'
            f"{escape(espacio.id)}</text>"
        )
        if clasificacion:
            temperatura = clasificacion.resultado.temperatura_final
            partes.append(
                f'<text x="{x:.0f}" y="{y + 13:.0f}" font-size="11" '
                'text-anchor="middle" fill="#ffffff">'
                f"{temperatura:.1f} C</text>"
            )
        partes.append(
            f'<text x="{x:.0f}" y="{y + _RADIO_NODO + 16:.0f}" font-size="11" '
            'text-anchor="middle" fill="#263238">'
            f"{escape(espacio.nombre)}</text>"
        )

        if clasificacion and clasificacion.color == AMARILLO:
            solucion = clasificacion.solucion
            etiqueta_y = y + _RADIO_NODO + 35
            costo_y = y + _RADIO_NODO + 50
            partes.append(
                f'<rect x="{x - 95:.0f}" y="{etiqueta_y - 13:.0f}" width="190" '
                'height="38" rx="4" fill="#fff8e1" stroke="#f9a825"/>'
            )
            partes.append(
                f'<text x="{x:.0f}" y="{etiqueta_y:.0f}" font-size="11" '
                'font-weight="bold" text-anchor="middle" fill="#8d6e00">'
                f"{escape(solucion.resumen_corto())}</text>"
            )
            partes.append(
                f'<text x="{x:.0f}" y="{costo_y:.0f}" font-size="11" '
                'text-anchor="middle" fill="#8d6e00">'
                f"${solucion.costo_cop:,.0f} COP</text>"
            )
        elif clasificacion and clasificacion.color == ROJO:
            etiqueta_y = y + _RADIO_NODO + 35
            partes.append(
                f'<rect x="{x - 95:.0f}" y="{etiqueta_y - 13:.0f}" width="190" '
                'height="20" rx="4" fill="#ffebee" stroke="#c62828"/>'
            )
            partes.append(
                f'<text x="{x:.0f}" y="{etiqueta_y:.0f}" font-size="11" '
                'font-weight="bold" text-anchor="middle" fill="#8e0000">'
                "Sin solucion viable</text>"
            )

    leyenda_y = max_y - _ALTO_LEYENDA + 30
    partes.append(
        f'<text x="20" y="{leyenda_y - 10:.0f}" font-size="14" font-weight="bold">'
        "Leyenda</text>"
    )
    items_leyenda = [
        (VERDE, "Habitable"),
        (AMARILLO, "No habitable, con solucion (se muestra cual y su costo)"),
        (ROJO, "No habitable, sin solucion viable"),
    ]
    for indice, (color, texto) in enumerate(items_leyenda):
        y_item = leyenda_y + indice * 26
        partes.append(
            f'<circle cx="35" cy="{y_item:.0f}" r="10" fill="{_COLOR_HEX[color]}" '
            'stroke="#263238"/>'
        )
        partes.append(
            f'<text x="55" y="{y_item + 4:.0f}" font-size="13" fill="#263238">'
            f"{escape(texto)}</text>"
        )

    partes.append("</svg>")

    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("".join(partes))
