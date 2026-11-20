import unittest

from evaluacion import evaluar_espacios
from modelos import ConexionTermica, Edificio, Espacio, Nivel
from simulacion import calcular_siguiente_paso, simular


def edificio_simple(espacios, conexiones):
    return Edificio(
        id="T",
        nombre="Edificio de prueba",
        niveles=[Nivel("N", 1, espacios)],
        conexiones=conexiones,
    )


class PruebasSimulacionTermica(unittest.TestCase):
    def test_sin_diferencias_permanece_estable(self):
        edificio = edificio_simple(
            [
                Espacio("A", "A", 1, "salon", 22.0, 1000.0, 5.0, 0.0),
                Espacio("B", "B", 1, "salon", 22.0, 1000.0, 5.0, 0.0),
            ],
            [ConexionTermica("A", "B", 4.0)],
        )

        resultado = simular(edificio, 22.0, 100.0, 10.0)

        self.assertAlmostEqual(resultado.historial["A"][-1], 22.0)
        self.assertAlmostEqual(resultado.historial["B"][-1], 22.0)

    def test_dos_espacios_intercambian_calor(self):
        edificio = edificio_simple(
            [
                Espacio("A", "Caliente", 1, "salon", 30.0, 1000.0),
                Espacio("B", "Frio", 1, "salon", 20.0, 1000.0),
            ],
            [ConexionTermica("A", "B", 10.0)],
        )

        resultado = simular(edificio, 0.0, 10.0, 1.0)

        self.assertLess(resultado.historial["A"][-1], 30.0)
        self.assertGreater(resultado.historial["B"][-1], 20.0)

    def test_energia_total_se_conserva_aproximadamente_en_sistema_aislado(self):
        edificio = edificio_simple(
            [
                Espacio("A", "A", 1, "salon", 30.0, 1000.0),
                Espacio("B", "B", 1, "salon", 20.0, 2000.0),
            ],
            [ConexionTermica("A", "B", 8.0)],
        )

        resultado = simular(edificio, 0.0, 50.0, 1.0)
        inicial = 1000.0 * 30.0 + 2000.0 * 20.0
        final = (
            1000.0 * resultado.historial["A"][-1]
            + 2000.0 * resultado.historial["B"][-1]
        )

        self.assertAlmostEqual(inicial, final, places=7)

    def test_conexion_vertical_participa_en_calculo(self):
        edificio = Edificio(
            id="V",
            nombre="Vertical",
            niveles=[
                Nivel("N1", 1, [Espacio("A", "Piso 1", 1, "salon", 30.0, 1000.0)]),
                Nivel("N2", 2, [Espacio("B", "Piso 2", 2, "salon", 20.0, 1000.0)]),
            ],
            conexiones=[ConexionTermica("A", "B", 10.0)],
        )

        siguiente = calcular_siguiente_paso(
            edificio,
            edificio.temperaturas_iniciales(),
            temperatura_exterior=0.0,
            paso_segundos=1.0,
        )

        self.assertLess(siguiente["A"], 30.0)
        self.assertGreater(siguiente["B"], 20.0)

    def test_orden_de_espacios_no_cambia_un_paso(self):
        conexiones = [ConexionTermica("A", "B", 10.0)]
        edificio_1 = edificio_simple(
            [
                Espacio("A", "A", 1, "salon", 30.0, 1000.0),
                Espacio("B", "B", 1, "salon", 20.0, 1000.0),
            ],
            conexiones,
        )
        edificio_2 = edificio_simple(
            [
                Espacio("B", "B", 1, "salon", 20.0, 1000.0),
                Espacio("A", "A", 1, "salon", 30.0, 1000.0),
            ],
            conexiones,
        )

        paso_1 = calcular_siguiente_paso(edificio_1, edificio_1.temperaturas_iniciales(), 0.0, 1.0)
        paso_2 = calcular_siguiente_paso(edificio_2, edificio_2.temperaturas_iniciales(), 0.0, 1.0)

        self.assertEqual(paso_1, paso_2)

    def test_rechaza_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            edificio_simple(
                [Espacio("A", "A", 1, "salon", 20.0, 0.0)],
                [],
            )

        with self.assertRaises(ValueError):
            edificio_simple(
                [
                    Espacio("A", "A", 1, "salon", 20.0, 1000.0),
                    Espacio("B", "B", 1, "salon", 20.0, 1000.0),
                ],
                [ConexionTermica("A", "B", -1.0)],
            )

    def test_evaluacion_identifica_cumplimiento(self):
        edificio = edificio_simple(
            [
                Espacio("A", "A", 1, "salon", 22.0, 1000.0),
                Espacio("B", "B", 1, "salon", 28.0, 1000.0),
            ],
            [],
        )

        resultados = evaluar_espacios(
            edificio,
            {"A": 22.0, "B": 28.0},
            {"salon": (20.0, 25.0)},
        )

        self.assertTrue(resultados[0].cumple)
        self.assertFalse(resultados[1].cumple)


if __name__ == "__main__":
    unittest.main()
