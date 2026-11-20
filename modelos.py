from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Espacio:
    id: str
    nombre: str
    piso: int
    actividad: str
    temperatura_inicial: float
    capacidad_termica: float
    conductancia_exterior: float = 0.0
    fuente_interna: float = 0.0


@dataclass(frozen=True)
class ConexionTermica:
    espacio_a: str
    espacio_b: str
    conductancia: float


@dataclass
class Nivel:
    id: str
    numero: int
    espacios: list[Espacio] = field(default_factory=list)


class Edificio:
    def __init__(
        self,
        id: str,
        nombre: str,
        niveles: list[Nivel],
        conexiones: list[ConexionTermica],
    ) -> None:
        self.id = id
        self.nombre = nombre
        self.niveles = niveles
        self.conexiones = conexiones
        self._espacios_por_id = self._indexar_espacios()
        self._validar()
        self.adyacencia = self._construir_adyacencia()

    def espacios(self) -> list[Espacio]:
        return list(self._espacios_por_id.values())

    def espacio(self, espacio_id: str) -> Espacio:
        return self._espacios_por_id[espacio_id]

    def vecinos(self, espacio_id: str) -> list[tuple[str, float]]:
        return list(self.adyacencia[espacio_id])

    def temperaturas_iniciales(self) -> dict[str, float]:
        return {
            espacio.id: espacio.temperatura_inicial
            for espacio in self.espacios()
        }

    def _indexar_espacios(self) -> dict[str, Espacio]:
        espacios_por_id: dict[str, Espacio] = {}
        for nivel in self.niveles:
            for espacio in nivel.espacios:
                if espacio.id in espacios_por_id:
                    raise ValueError(f"Identificador de espacio duplicado: {espacio.id}")
                espacios_por_id[espacio.id] = espacio
        return espacios_por_id

    def _validar(self) -> None:
        if not self._espacios_por_id:
            raise ValueError("El edificio debe tener al menos un espacio.")

        for espacio in self.espacios():
            if espacio.capacidad_termica <= 0:
                raise ValueError(
                    f"La capacidad termica de {espacio.id} debe ser positiva."
                )
            if espacio.conductancia_exterior < 0:
                raise ValueError(
                    f"La conductancia exterior de {espacio.id} no puede ser negativa."
                )

        for conexion in self.conexiones:
            if conexion.espacio_a not in self._espacios_por_id:
                raise ValueError(f"Conexion a espacio inexistente: {conexion.espacio_a}")
            if conexion.espacio_b not in self._espacios_por_id:
                raise ValueError(f"Conexion a espacio inexistente: {conexion.espacio_b}")
            if conexion.espacio_a == conexion.espacio_b:
                raise ValueError("Una conexion termica no puede unir un espacio consigo mismo.")
            if conexion.conductancia < 0:
                raise ValueError("La conductancia entre espacios no puede ser negativa.")

    def _construir_adyacencia(self) -> dict[str, list[tuple[str, float]]]:
        adyacencia: dict[str, list[tuple[str, float]]] = {
            espacio.id: []
            for espacio in self.espacios()
        }
        for conexion in self.conexiones:
            adyacencia[conexion.espacio_a].append(
                (conexion.espacio_b, conexion.conductancia)
            )
            adyacencia[conexion.espacio_b].append(
                (conexion.espacio_a, conexion.conductancia)
            )
        return adyacencia
