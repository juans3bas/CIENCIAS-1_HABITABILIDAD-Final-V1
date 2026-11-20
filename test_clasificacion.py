import unittest

from clasificacion import AMARILLO, ROJO, VERDE, clasificar_espacio
from evaluacion import ResultadoEvaluacion


def _resultado(temperatura_final, minimo, maximo, actividad="salon"):
    cumple = minimo <= temperatura_final <= maximo
    return ResultadoEvaluacion(
        espacio_id="X",
        piso=1,
        nombre="Espacio X",
        actividad=actividad,
        temperatura_inicial=temperatura_final,
        temperatura_final=temperatura_final,
        minimo=minimo,
        maximo=maximo,
        cumple=cumple,
    )


class PruebasClasificacion(unittest.TestCase):
    def test_espacio_que_cumple_es_verde(self):
        resultado = _resultado(24.0, 20.0, 28.0)
        clasificacion = clasificar_espacio(
            resultado, capacidad_termica=100_000.0, duracion_segundos=3600.0
        )
        self.assertEqual(clasificacion.color, VERDE)
        self.assertIsNone(clasificacion.solucion)

    def test_desviacion_pequena_es_amarillo_con_costo(self):
        resultado = _resultado(29.0, 20.0, 28.0)
        clasificacion = clasificar_espacio(
            resultado, capacidad_termica=100_000.0, duracion_segundos=3600.0
        )
        self.assertEqual(clasificacion.color, AMARILLO)
        self.assertIsNotNone(clasificacion.solucion)
        self.assertGreater(clasificacion.solucion.costo_cop, 0)

    def test_desviacion_extrema_sin_balanceo_es_rojo_sin_solucion(self):
        resultado = _resultado(90.0, 20.0, 28.0, actividad="salon")
        clasificacion = clasificar_espacio(
            resultado, capacidad_termica=200_000.0, duracion_segundos=3600.0
        )
        self.assertEqual(clasificacion.color, ROJO)
        self.assertIsNone(clasificacion.solucion)

    def test_balanceo_mas_barato_gana_sobre_climatizacion(self):
        from clasificacion import SolucionActiva

        resultado = _resultado(29.0, 20.0, 28.0)
        balanceo_barato = SolucionActiva(costo_cop=1.0)
        clasificacion = clasificar_espacio(
            resultado,
            capacidad_termica=100_000.0,
            duracion_segundos=3600.0,
            solucion_balanceo=balanceo_barato,
        )
        self.assertEqual(clasificacion.color, AMARILLO)
        self.assertIs(clasificacion.solucion, balanceo_barato)


if __name__ == "__main__":
    unittest.main()
