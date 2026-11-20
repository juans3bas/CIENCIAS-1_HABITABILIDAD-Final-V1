from __future__ import annotations

from evaluacion import CriteriosTermicos
from modelos import ConexionTermica, Edificio, Espacio, Nivel


CRITERIOS_EJEMPLO: CriteriosTermicos = {
    "salon": (20.0, 28.0),
    "oficina": (21.0, 24.0),
    "laboratorio": (20.0, 23.0),
    "pasillo": (18.0, 30.0),
    "auditorio": (19.0, 27.0),
    "sala_tecnica": (18.0, 24.0),
}


def construir_edificio_ejemplo() -> Edificio:
    """Crea datos ilustrativos para una simulacion academica.

    El edificio tiene 3 pisos para poder mostrar, en la clasificacion por
    colores, un caso de cada tipo: espacios habitables (verde), espacios no
    habitables pero corregibles con climatizacion o balanceo del grafo
    (amarillo) y al menos un espacio sin solucion viable dentro de los
    limites configurados (rojo), tipico de un cuarto tecnico con una fuente
    de calor interna muy alta y poco aislamiento.
    """
    nivel_1 = Nivel(
        id="N1",
        numero=1,
        espacios=[
            Espacio("S101", "Salon 101", 1, "salon", 27.0, 180_000.0, 11.0, 0.0),
            Espacio("O101", "Oficina 101", 1, "oficina", 24.0, 130_000.0, 8.0, 150.0),
            Espacio("P101", "Pasillo 101", 1, "pasillo", 23.0, 160_000.0, 5.0, 0.0),
        ],
    )
    nivel_2 = Nivel(
        id="N2",
        numero=2,
        espacios=[
            Espacio("L201", "Laboratorio 201", 2, "laboratorio", 29.0, 220_000.0, 13.0, 300.0),
            Espacio("S201", "Salon 201", 2, "salon", 26.0, 175_000.0, 10.0, 0.0),
            Espacio("P201", "Pasillo 201", 2, "pasillo", 24.0, 150_000.0, 6.0, 0.0),
        ],
    )
    nivel_3 = Nivel(
        id="N3",
        numero=3,
        espacios=[
            Espacio("AUD301", "Auditorio 301", 3, "auditorio", 25.0, 320_000.0, 9.0, 0.0),
            Espacio("CT301", "Cuarto Tecnico 301", 3, "sala_tecnica", 30.0, 90_000.0, 16.0, 2200.0),
            Espacio("P301", "Pasillo 301", 3, "pasillo", 24.0, 150_000.0, 6.0, 0.0),
        ],
    )

    conexiones = [
        ConexionTermica("S101", "P101", 18.0),
        ConexionTermica("O101", "P101", 12.0),
        ConexionTermica("L201", "P201", 16.0),
        ConexionTermica("S201", "P201", 14.0),
        ConexionTermica("P101", "P201", 9.0),
        ConexionTermica("S101", "S201", 4.0),
        ConexionTermica("AUD301", "P301", 15.0),
        ConexionTermica("CT301", "P301", 15.0),
        ConexionTermica("P201", "P301", 8.0),
    ]

    return Edificio(
        id="EDU-01",
        nombre="Edificio academico de demostracion",
        niveles=[nivel_1, nivel_2, nivel_3],
        conexiones=conexiones,
    )
