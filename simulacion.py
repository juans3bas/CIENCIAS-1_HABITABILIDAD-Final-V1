from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from modelos import Edificio


@dataclass(frozen=True)
class ResultadoSimulacion:
    tiempos: list[float]
    historial: dict[str, list[float]]

    def temperaturas_finales(self) -> dict[str, float]:
        return {
            espacio_id: valores[-1]
            for espacio_id, valores in self.historial.items()
        }


def validar_estabilidad(edificio: Edificio, paso_segundos: float) -> None:
    if paso_segundos <= 0:
        raise ValueError("El paso de tiempo debe ser positivo.")

    limites: list[float] = []
    for espacio in edificio.espacios():
        suma_conductancias = espacio.conductancia_exterior
        suma_conductancias += sum(
            conductancia
            for _, conductancia in edificio.vecinos(espacio.id)
        )
        if suma_conductancias > 0:
            limites.append(espacio.capacidad_termica / suma_conductancias)

    if limites and paso_segundos > min(limites):
        raise ValueError(
            "Paso de tiempo demasiado grande para la comprobacion conservadora "
            f"de estabilidad. Use un paso <= {min(limites):.2f} s."
        )


def calcular_siguiente_paso(
    edificio: Edificio,
    temperaturas_actuales: dict[str, float],
    temperatura_exterior: float,
    paso_segundos: float,
) -> dict[str, float]:
    nuevas_temperaturas: dict[str, float] = {}

    for espacio in edificio.espacios():
        temperatura_i = temperaturas_actuales[espacio.id]
        flujo_total = 0.0

        for vecino_id, conductancia in edificio.vecinos(espacio.id):
            temperatura_vecino = temperaturas_actuales[vecino_id]
            flujo_total += conductancia * (temperatura_vecino - temperatura_i)

        flujo_total += espacio.conductancia_exterior * (
            temperatura_exterior - temperatura_i
        )
        flujo_total += espacio.fuente_interna

        delta_t = paso_segundos * flujo_total / espacio.capacidad_termica
        nuevas_temperaturas[espacio.id] = temperatura_i + delta_t

    return nuevas_temperaturas


def simular(
    edificio: Edificio,
    temperatura_exterior: float,
    duracion_segundos: float,
    paso_segundos: float,
) -> ResultadoSimulacion:
    if duracion_segundos < 0:
        raise ValueError("La duracion de la simulacion no puede ser negativa.")

    validar_estabilidad(edificio, paso_segundos)

    pasos = ceil(duracion_segundos / paso_segundos) if duracion_segundos else 0
    temperaturas = edificio.temperaturas_iniciales()
    historial = {
        espacio_id: [temperatura]
        for espacio_id, temperatura in temperaturas.items()
    }
    tiempos = [0.0]

    for paso in range(1, pasos + 1):
        temperaturas = calcular_siguiente_paso(
            edificio,
            temperaturas,
            temperatura_exterior,
            paso_segundos,
        )
        tiempo = min(paso * paso_segundos, duracion_segundos)
        tiempos.append(tiempo)
        for espacio_id, temperatura in temperaturas.items():
            historial[espacio_id].append(temperatura)

    return ResultadoSimulacion(tiempos=tiempos, historial=historial)
