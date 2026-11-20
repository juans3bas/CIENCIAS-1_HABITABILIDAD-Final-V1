import random
import unittest

from estructuras import ArbolB


class PruebasArbolB(unittest.TestCase):
    def test_insertar_y_buscar(self):
        arbol = ArbolB(grado_minimo=2)
        arbol.insertar(10, "A")
        arbol.insertar(5, "B")
        arbol.insertar(20, "C")

        self.assertEqual(arbol.buscar(10), ["A"])
        self.assertEqual(arbol.buscar(5), ["B"])
        self.assertEqual(arbol.buscar(20), ["C"])
        self.assertIsNone(arbol.buscar(99))

    def test_claves_repetidas_acumulan_valores(self):
        arbol = ArbolB(grado_minimo=2)
        arbol.insertar(15.0, "X")
        arbol.insertar(15.0, "Y")

        self.assertEqual(arbol.buscar(15.0), ["X", "Y"])

    def test_recorrido_ordenado_con_muchas_claves(self):
        arbol = ArbolB(grado_minimo=2)
        claves = [7, 3, 18, 1, 9, 23, 5, 12, 2, 30, 14, 8]
        for clave in claves:
            arbol.insertar(clave, f"v{clave}")

        recorrido = [clave for clave, _ in arbol.recorrido_ordenado()]
        self.assertEqual(recorrido, sorted(claves))

    def test_el_arbol_se_mantiene_balanceado_con_muchas_inserciones(self):
        arbol = ArbolB(grado_minimo=3)
        claves = list(range(500))
        random.Random(42).shuffle(claves)
        for clave in claves:
            arbol.insertar(clave, clave)

        # Con grado minimo t=3, un arbol balanceado con 500 claves no deberia
        # superar una altura logaritmica (muy por debajo de una lista lineal).
        self.assertLessEqual(arbol.altura(), 6)
        self.assertEqual(
            [clave for clave, _ in arbol.recorrido_ordenado()], sorted(claves)
        )

    def test_busqueda_por_rango(self):
        arbol = ArbolB(grado_minimo=2)
        for clave in [10, 25, 3, 47, 18, 31, 7, 22]:
            arbol.insertar(clave, f"v{clave}")

        resultado = [clave for clave, _ in arbol.buscar_rango(10, 25)]
        self.assertEqual(resultado, [10, 18, 22, 25])

    def test_rechaza_grado_minimo_invalido(self):
        with self.assertRaises(ValueError):
            ArbolB(grado_minimo=1)


if __name__ == "__main__":
    unittest.main()
