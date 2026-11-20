from __future__ import annotations

from dataclasses import dataclass, replace

from evaluacion import CriteriosTermicos, evaluar_espacios
from modelos import ConexionTermica, Edificio
from simulacion import simular

# Valores ilustrativos, igual que en clasificacion.py.
COSTO_FIJO_DUCTO_COP = 90_000.0
COSTO_POR_WATT_K_CONDUCTANCIA_COP = 4_000.0
FACTORES_DE_PRUEBA = (1.5, 2.0, 3.0, 4.0, 6.0, 9.0)


@dataclass(frozen=True)
class BalanceoPropuesto:
    espacio_id: str
    vecino_id: str
    conductancia_original: float
    conductancia_nueva: float
    costo_cop: float

    def descripcion(self) -> str:
        return (
            f"Balancear el grafo termico: aumentar la conductancia entre "
            f"{self.espacio_id} y {self.vecino_id} de "
            f"{self.conductancia_original:.1f} a {self.conductancia_nueva:.1f} W/K "
            f"(costo estimado ${self.costo_cop:,.0f} COP)"
        )

    def resumen_corto(self) -> str:
        return f"Balanceo con {self.vecino_id}"


def _edificio_con_conductancia_modificada(
    edificio: Edificio, espacio_id: str, vecino_id: str, nueva_conductancia: float
) -> Edificio:
    nuevas_conexiones = []
    for conexion in edificio.conexiones:
        coincide = {conexion.espacio_a, conexion.espacio_b} == {espacio_id, vecino_id}
        if coincide:
            nuevas_conexiones.append(replace(conexion, conductancia=nueva_conductancia))
        else:
            nuevas_conexiones.append(conexion)

    return Edificio(
        id=edificio.id,
        nombre=edificio.nombre,
        niveles=edificio.niveles,
        conexiones=nuevas_conexiones,
    )


def intentar_balanceo_por_conductancia(
    edificio: Edificio,
    espacio_id: str,
    criterios: CriteriosTermicos,
    temperatura_exterior: float,
    duracion_segundos: float,
    paso_segundos: float,
) -> BalanceoPropuesto | None:
    """Prueba redistribuir el calor del grafo subiendo la conductancia hacia

    cada vecino, re-simulando el edificio completo. Si alguna combinacion
    logra que el espacio cumpla su criterio, se devuelve la mas barata.
    """
    mejor: BalanceoPropuesto | None = None

    for vecino_id, conductancia_actual in edificio.vecinos(espacio_id):
        for factor in FACTORES_DE_PRUEBA:
            nueva_conductancia = conductancia_actual * factor
            edificio_modificado = _edificio_con_conductancia_modificada(
                edificio, espacio_id, vecino_id, nueva_conductancia
            )
            resultado = simular(
                edificio_modificado,
                temperatura_exterior=temperatura_exterior,
                duracion_segundos=duracion_segundos,
                paso_segundos=paso_segundos,
            )
            evaluaciones = evaluar_espacios(
                edificio_modificado, resultado.temperaturas_finales(), criterios
            )
            evaluacion_espacio = next(
                evaluacion for evaluacion in evaluaciones if evaluacion.espacio_id == espacio_id
            )
            if not evaluacion_espacio.cumple:
                continue

            incremento = nueva_conductancia - conductancia_actual
            costo = COSTO_FIJO_DUCTO_COP + COSTO_POR_WATT_K_CONDUCTANCIA_COP * incremento
            if mejor is None or costo < mejor.costo_cop:
                mejor = BalanceoPropuesto(
                    espacio_id=espacio_id,
                    vecino_id=vecino_id,
                    conductancia_original=conductancia_actual,
                    conductancia_nueva=nueva_conductancia,
                    costo_cop=costo,
                )
            break  # El factor mas pequeno que funciona ya es el mas barato para este vecino.

    return mejor
