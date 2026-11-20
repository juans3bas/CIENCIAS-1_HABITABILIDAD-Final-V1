from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _NodoArbolB:
    hoja: bool = True
    claves: list[float] = field(default_factory=list)
    valores: list[list] = field(default_factory=list)
    hijos: list["_NodoArbolB"] = field(default_factory=list)


class ArbolB:
    """Arbol B (balanceado) generico, clave -> lista de valores.

    Grado minimo `t`: cada nodo (salvo la raiz) tiene entre `t - 1` y
    `2t - 1` claves. Se admiten claves repetidas: cada clave guarda una
    lista de valores asociados.

    Se usa para indexar los espacios del edificio por su temperatura
    final, lo que permite busquedas puntuales y por rango en tiempo
    O(log n) en lugar de recorrer la lista completa de espacios.
    """

    def __init__(self, grado_minimo: int = 3) -> None:
        if grado_minimo < 2:
            raise ValueError("El grado minimo del arbol B debe ser >= 2.")
        self.t = grado_minimo
        self.raiz = _NodoArbolB()

    def insertar(self, clave: float, valor) -> None:
        raiz = self.raiz
        if len(raiz.claves) == 2 * self.t - 1:
            nueva_raiz = _NodoArbolB(hoja=False, hijos=[raiz])
            self.raiz = nueva_raiz
            self._dividir_hijo(nueva_raiz, 0)
            self._insertar_no_lleno(nueva_raiz, clave, valor)
        else:
            self._insertar_no_lleno(raiz, clave, valor)

    def _dividir_hijo(self, padre: _NodoArbolB, indice: int) -> None:
        t = self.t
        hijo = padre.hijos[indice]
        nuevo = _NodoArbolB(hoja=hijo.hoja)

        nuevo.claves = hijo.claves[t:]
        nuevo.valores = hijo.valores[t:]
        clave_media = hijo.claves[t - 1]
        valor_medio = hijo.valores[t - 1]

        hijo.claves = hijo.claves[: t - 1]
        hijo.valores = hijo.valores[: t - 1]

        if not hijo.hoja:
            nuevo.hijos = hijo.hijos[t:]
            hijo.hijos = hijo.hijos[:t]

        padre.hijos.insert(indice + 1, nuevo)
        padre.claves.insert(indice, clave_media)
        padre.valores.insert(indice, valor_medio)

    def _insertar_no_lleno(self, nodo: _NodoArbolB, clave: float, valor) -> None:
        indice = _posicion(nodo.claves, clave)

        if indice < len(nodo.claves) and nodo.claves[indice] == clave:
            nodo.valores[indice].append(valor)
            return

        if nodo.hoja:
            nodo.claves.insert(indice, clave)
            nodo.valores.insert(indice, [valor])
            return

        if len(nodo.hijos[indice].claves) == 2 * self.t - 1:
            self._dividir_hijo(nodo, indice)
            if clave == nodo.claves[indice]:
                nodo.valores[indice].append(valor)
                return
            if clave > nodo.claves[indice]:
                indice += 1

        self._insertar_no_lleno(nodo.hijos[indice], clave, valor)

    def buscar(self, clave: float) -> list | None:
        return self._buscar_en(self.raiz, clave)

    def _buscar_en(self, nodo: _NodoArbolB, clave: float) -> list | None:
        indice = _posicion(nodo.claves, clave)
        if indice < len(nodo.claves) and nodo.claves[indice] == clave:
            return nodo.valores[indice]
        if nodo.hoja:
            return None
        return self._buscar_en(nodo.hijos[indice], clave)

    def buscar_rango(self, clave_minima: float, clave_maxima: float) -> list[tuple[float, object]]:
        """Devuelve pares (clave, valor) con clave_minima <= clave <= clave_maxima, en orden."""
        resultados: list[tuple[float, object]] = []
        self._recorrer_rango(self.raiz, clave_minima, clave_maxima, resultados)
        return resultados

    def _recorrer_rango(
        self,
        nodo: _NodoArbolB,
        clave_minima: float,
        clave_maxima: float,
        resultados: list[tuple[float, object]],
    ) -> None:
        for indice, clave in enumerate(nodo.claves):
            if not nodo.hoja and clave >= clave_minima:
                self._recorrer_rango(nodo.hijos[indice], clave_minima, clave_maxima, resultados)
            if clave_minima <= clave <= clave_maxima:
                for valor in nodo.valores[indice]:
                    resultados.append((clave, valor))

        if not nodo.hoja and (not nodo.claves or nodo.claves[-1] < clave_maxima):
            self._recorrer_rango(nodo.hijos[-1], clave_minima, clave_maxima, resultados)

    def recorrido_ordenado(self) -> list[tuple[float, object]]:
        resultados: list[tuple[float, object]] = []
        self._recorrer_todo(self.raiz, resultados)
        return resultados

    def _recorrer_todo(self, nodo: _NodoArbolB, resultados: list[tuple[float, object]]) -> None:
        for indice, clave in enumerate(nodo.claves):
            if not nodo.hoja:
                self._recorrer_todo(nodo.hijos[indice], resultados)
            for valor in nodo.valores[indice]:
                resultados.append((clave, valor))
        if not nodo.hoja:
            self._recorrer_todo(nodo.hijos[-1], resultados)

    def altura(self) -> int:
        nodo = self.raiz
        altura = 1
        while not nodo.hoja:
            altura += 1
            nodo = nodo.hijos[0]
        return altura


def _posicion(claves: list[float], clave: float) -> int:
    """Primer indice i tal que claves[i] >= clave (busqueda binaria)."""
    bajo, alto = 0, len(claves)
    while bajo < alto:
        medio = (bajo + alto) // 2
        if claves[medio] < clave:
            bajo = medio + 1
        else:
            alto = medio
    return bajo


def construir_indice_por_temperatura(
    resultados_evaluacion, grado_minimo: int = 3
) -> ArbolB:
    """Indexa ResultadoEvaluacion por temperatura_final en un arbol B."""
    arbol = ArbolB(grado_minimo=grado_minimo)
    for resultado in resultados_evaluacion:
        arbol.insertar(round(resultado.temperatura_final, 4), resultado.espacio_id)
    return arbol
