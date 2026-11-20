from __future__ import annotations

from dataclasses import dataclass

from modelos import Edificio


CriteriosTermicos = dict[str, tuple[float, float]]


@dataclass(frozen=True)
class ResultadoEvaluacion:
    espacio_id: str
    piso: int
    nombre: str
    actividad: str
    temperatura_inicial: float
    temperatura_final: float
    minimo: float
    maximo: float
    cumple: bool

    @property
    def estado(self) -> str:
        if self.cumple:
            return "Cumple el criterio termico configurado"
        return "No cumple el criterio termico configurado"


def evaluar_espacios(
    edificio: Edificio,
    temperaturas_finales: dict[str, float],
    criterios: CriteriosTermicos,
) -> list[ResultadoEvaluacion]:
    resultados: list[ResultadoEvaluacion] = []

    for espacio in edificio.espacios():
        if espacio.actividad not in criterios:
            raise ValueError(f"No hay criterio termico para: {espacio.actividad}")
        minimo, maximo = criterios[espacio.actividad]
        temperatura_final = temperaturas_finales[espacio.id]
        resultados.append(
            ResultadoEvaluacion(
                espacio_id=espacio.id,
                piso=espacio.piso,
                nombre=espacio.nombre,
                actividad=espacio.actividad,
                temperatura_inicial=espacio.temperatura_inicial,
                temperatura_final=temperatura_final,
                minimo=minimo,
                maximo=maximo,
                cumple=minimo <= temperatura_final <= maximo,
            )
        )

    return resultados


def resumen_cumplimiento(resultados: list[ResultadoEvaluacion]) -> tuple[int, int]:
    cumplen = sum(1 for resultado in resultados if resultado.cumple)
    no_cumplen = len(resultados) - cumplen
    return cumplen, no_cumplen
