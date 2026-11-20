from __future__ import annotations

from dataclasses import dataclass

from evaluacion import ResultadoEvaluacion

# Valores ilustrativos (igual que el resto del proyecto, no son cotizaciones
# reales). Sirven para poder comparar alternativas de solucion entre si.
COSTO_FIJO_INSTALACION_COP = 180_000.0
COSTO_POR_WATT_COP = 2_500.0
POTENCIA_MAXIMA_INSTALABLE_W = 900.0

VERDE = "verde"
AMARILLO = "amarillo"
ROJO = "rojo"


@dataclass(frozen=True)
class SolucionActiva:
    """Agregar/quitar potencia de climatizacion (calefaccion o enfriamiento)."""

    tipo: str = "climatizacion"
    potencia_watts: float = 0.0
    costo_cop: float = 0.0

    def descripcion(self) -> str:
        accion = "calefaccion" if self.potencia_watts > 0 else "enfriamiento"
        return (
            f"Instalar {accion} de {abs(self.potencia_watts):.0f} W "
            f"(costo estimado ${self.costo_cop:,.0f} COP)"
        )

    def resumen_corto(self) -> str:
        accion = "Calentar" if self.potencia_watts > 0 else "Enfriar"
        return f"{accion} {abs(self.potencia_watts):.0f} W"


@dataclass(frozen=True)
class ClasificacionEspacio:
    espacio_id: str
    color: str
    resultado: ResultadoEvaluacion
    solucion: object | None  # SolucionActiva o BalanceoPropuesto, ambos con .costo_cop, .descripcion() y .resumen_corto()


def potencia_requerida_cop(
    resultado: ResultadoEvaluacion, duracion_segundos: float, capacidad_termica: float
) -> float:
    """Potencia constante adicional (W) para llevar la temperatura final

    al punto medio del intervalo de la actividad, usando la misma relacion
    C * dT = Q * dt del modelo de simulacion (ver README).
    """
    objetivo = (resultado.minimo + resultado.maximo) / 2
    delta_objetivo = objetivo - resultado.temperatura_final
    if duracion_segundos <= 0:
        return 0.0
    return capacidad_termica * delta_objetivo / duracion_segundos


def evaluar_solucion_activa(
    resultado: ResultadoEvaluacion, duracion_segundos: float, capacidad_termica: float
) -> SolucionActiva | None:
    potencia = potencia_requerida_cop(resultado, duracion_segundos, capacidad_termica)
    if abs(potencia) > POTENCIA_MAXIMA_INSTALABLE_W:
        return None
    costo = COSTO_FIJO_INSTALACION_COP + COSTO_POR_WATT_COP * abs(potencia)
    return SolucionActiva(potencia_watts=potencia, costo_cop=costo)


def clasificar_espacio(
    resultado: ResultadoEvaluacion,
    capacidad_termica: float,
    duracion_segundos: float,
    solucion_balanceo: object | None = None,
) -> ClasificacionEspacio:
    if resultado.cumple:
        return ClasificacionEspacio(
            espacio_id=resultado.espacio_id,
            color=VERDE,
            resultado=resultado,
            solucion=None,
        )

    solucion_activa = evaluar_solucion_activa(resultado, duracion_segundos, capacidad_termica)

    candidatas = [s for s in (solucion_activa, solucion_balanceo) if s is not None]
    if candidatas:
        mejor = min(candidatas, key=lambda s: s.costo_cop)
        return ClasificacionEspacio(
            espacio_id=resultado.espacio_id,
            color=AMARILLO,
            resultado=resultado,
            solucion=mejor,
        )

    return ClasificacionEspacio(
        espacio_id=resultado.espacio_id,
        color=ROJO,
        resultado=resultado,
        solucion=None,
    )
