# Simulador de habitabilidad termica

El programa representa un edificio completo como un grafo termico ponderado (espacios = nodos, conexiones = aristas con conductancia), simula la evolucion de temperatura de cada espacio, evalua si queda dentro del intervalo configurado para su actividad, lo clasifica por color de habitabilidad, calcula una solucion y su costo cuando es posible corregirlo (mostrandolos directamente sobre el grafo), prueba el balanceo del grafo como alternativa mas barata, indexa los resultados en un arbol B y exporta todo a Excel y a un grafo SVG coloreado.

No reconoce planos ni usa OCR, no tiene interfaz web y no modifica arquitectura real: es un modelo academico ilustrativo.

## Requisitos cubiertos

- **Edificacion completa**: `datos_ejemplo.py` construye un edificio de 3 pisos y 9 espacios con conexiones horizontales, verticales y hacia el exterior (ver [`modelos.py`](modelos.py), [`datos_ejemplo.py`](datos_ejemplo.py)).
- **Simulacion completa**: `simulacion.py` resuelve el balance termico de todos los espacios paso a paso (Euler explicito) hasta la duracion configurada.
- **Grafos clasificados por colores**: `clasificacion.py` + `visualizacion.py` clasifican cada espacio en verde (habitable), amarillo (no habitable pero con solucion) o rojo (no habitable sin solucion viable). En `grafo_habitabilidad.svg`, cada nodo amarillo muestra directamente cual es la solucion y cuanto cuesta; cada nodo rojo muestra que no tiene solucion viable.
- **Arbol B**: `estructuras.py` implementa un arbol B balanceado (insercion con division de nodos, busqueda puntual y por rango) usado para indexar los espacios por su temperatura final.
- **Balanceo del grafo**: `balanceo.py` intenta corregir un espacio no habitable subiendo la conductancia (la arista) hacia alguno de sus vecinos y re-simulando el edificio completo; se compara su costo contra instalar climatizacion y se usa la opcion mas barata como solucion del espacio amarillo.

## Estructura

- `modelos.py`: define `Edificio`, `Nivel`, `Espacio` y `ConexionTermica` (el grafo termico). Valida identificadores duplicados, referencias inexistentes, capacidades no positivas y conductancias negativas.
- `datos_ejemplo.py`: construye el edificio academico de 3 pisos y 9 espacios, con conexiones horizontales, verticales e intercambio con el exterior, y los criterios termicos por actividad.
- `simulacion.py`: implementa el balance termico iterativo con Euler explicito para todos los espacios del grafo.
- `evaluacion.py`: compara temperaturas finales contra intervalos por actividad.
- `clasificacion.py`: clasifica cada espacio en verde/amarillo/rojo; calcula la potencia de climatizacion necesaria y su costo estimado para los casos corregibles.
- `balanceo.py`: intenta "balancear" el grafo termico aumentando la conductancia (la arista) entre un espacio problematico y sus vecinos, re-simulando el edificio para comprobar si esa alternativa pasiva es suficiente y cuanto cuesta frente a instalar climatizacion.
- `estructuras.py`: arbol B generico (`ArbolB`), usado para indexar los espacios por temperatura final y resolver busquedas puntuales o por rango en O(log n).
- `visualizacion.py`: genera `grafo_habitabilidad.svg`, el grafo del edificio coloreado por habitabilidad, sin dependencias externas.
- `main.py`: ejecuta la demostracion completa (simulacion, evaluacion, clasificacion, balanceo, arbol B) e imprime tablas, exporta `historial_temperaturas.xlsx` (hojas `Historial`, `Leyenda` y `Clasificacion`) y `grafo_habitabilidad.svg`.
- `test_simulacion.py`, `test_estructuras.py`, `test_clasificacion.py`: pruebas automatizadas de comportamiento fisico, validaciones, el arbol B y la logica de clasificacion.

## Ejecucion

```bash
python main.py
```

Para ejecutar las pruebas:

```bash
python -m unittest
```

## Modelo usado

Cada espacio es un nodo del grafo. Cada conexion termica es una arista con conductancia `G` en W/K. La conductancia representa la facilidad de intercambio de calor entre dos espacios.

Para cada espacio `i` se usa:

```text
C_i * dT_i/dt = sum(G_ij * (T_j - T_i)) + G_i_ext * (T_ext - T_i) + Q_i
```

Variables:

- `T_i`: temperatura del espacio, en grados Celsius.
- `C_i`: capacidad termica del espacio, en J/K.
- `G_ij`: conductancia entre espacios, en W/K.
- `T_ext`: temperatura exterior, en grados Celsius.
- `G_i_ext`: conductancia equivalente hacia el exterior, en W/K.
- `Q_i`: fuente interna neta de calor, en W.
- `t`: tiempo, en segundos.

La ecuacion se discretiza con Euler explicito:

```text
T_i(t + dt) = T_i(t) + dt * flujo_total_i / C_i
```

Todas las temperaturas nuevas se calculan usando las temperaturas del paso anterior. Asi, el resultado no depende del orden en que se recorran los espacios.

## Datos del ejemplo

Los valores son ilustrativos para una simulacion academica. No provienen de mediciones reales ni son limites legales universales.

- Temperatura: grados Celsius.
- Capacidad termica: J/K.
- Conductancia entre espacios y hacia exterior: W/K.
- Fuente interna: W.
- Tiempo: segundos.

El edificio de ejemplo tiene:

- Piso 1: salon, oficina y pasillo.
- Piso 2: laboratorio, salon y pasillo.
- Piso 3: auditorio, cuarto tecnico (con una fuente interna de calor muy alta, a proposito, para mostrar un caso sin solucion viable) y pasillo.
- Conexiones horizontales dentro de cada piso.
- Conexiones verticales `P101 <-> P201` y `S101 <-> S201` (piso 1-2), `P201 <-> P301` (piso 2-3).
- Intercambio con exterior en todos los espacios.

## Evaluacion termica

Cada actividad tiene un intervalo configurado:

- salon: 20.0 a 28.0 C.
- oficina: 21.0 a 24.0 C.
- laboratorio: 20.0 a 23.0 C.
- pasillo: 18.0 a 30.0 C.
- auditorio: 19.0 a 27.0 C.
- sala_tecnica: 18.0 a 24.0 C.

Al final se indica para cada espacio si cumple o no cumple. El edificio se reporta como no conforme si al menos un espacio incumple el criterio configurado.

## Clasificacion por colores, solucion y costo

Para cada espacio que no cumple el criterio termico se evaluan dos posibles soluciones y se elige la mas barata:

1. **Climatizacion activa** (`clasificacion.py`): potencia constante de calefaccion/enfriamiento necesaria para llevar la temperatura final al punto medio del intervalo permitido, estimada con la misma ecuacion del modelo (`C * dT = Q * dt`). El costo es `costo_fijo_instalacion + costo_por_watt * potencia`.
2. **Balanceo del grafo** (`balanceo.py`): subir la conductancia (la arista) hacia alguno de los vecinos del espacio y volver a simular el edificio completo; si eso basta para cumplir el criterio, el costo es `costo_fijo_ducto + costo_por_W/K * incremento_de_conductancia`.

Con ese resultado, cada espacio se clasifica en:

- **Verde**: habitable, cumple el criterio.
- **Amarillo**: no habitable, pero existe una solucion viable (climatizacion o balanceo) dentro de los limites configurados; se muestra cual es y su costo, tanto en el grafo (`grafo_habitabilidad.svg`) como en la consola y la hoja `Clasificacion` del Excel.
- **Rojo**: no habitable y ninguna solucion (climatizacion ni balanceo) es viable dentro de los limites configurados. No se propone nada mas: queda marcado simplemente como sin solucion.

Todos los valores de costo son ilustrativos (en pesos colombianos, COP) para poder comparar las dos soluciones entre si, igual que el resto de parametros del proyecto.

## Arbol B

`estructuras.py` implementa un arbol B balanceado de proposito general (insercion con division de nodos llenos, busqueda puntual y busqueda por rango). `main.py` lo usa para indexar los espacios del edificio por su temperatura final, lo que permite, por ejemplo, responder en O(log n) "que espacios tienen una temperatura final entre X y Y grados" en vez de recorrer la lista completa.

## Supuestos y limitaciones

- Modelo de parametros concentrados: cada espacio tiene una sola temperatura uniforme.
- Solo se evalua temperatura, no humedad, radiacion, velocidad del aire, ocupacion detallada ni normativa legal.
- Las conductancias, fuentes internas y costos son valores ilustrativos.
- El paso de tiempo se valida con una comprobacion conservadora de estabilidad numerica.
- La potencia de climatizacion necesaria se estima con una aproximacion lineal (ver `clasificacion.py`), no con una segunda simulacion iterativa.
- La exportacion XLSX y el grafo SVG se generan con la biblioteca estandar de Python, sin dependencias externas.
- Para cambiar los datos, edita `datos_ejemplo.py` (edificio y criterios) o los parametros de simulacion y los limites de costo en `main.py`, `clasificacion.py` y `balanceo.py`, y vuelve a ejecutar `python main.py`.

## Explicacion para sustentacion

El edificio se convierte en un grafo termico: los espacios son nodos y las conexiones fisicas entre espacios son aristas con conductancia. En cada paso de tiempo se calcula cuanto calor entra o sale de cada espacio por sus vecinos, por el exterior y por fuentes internas, y se actualiza la temperatura con Euler explicito.

Con la temperatura final de cada espacio se evalua si cumple el criterio de su actividad. Para los que no cumplen, se buscan dos soluciones posibles (instalar climatizacion, o balancear el grafo subiendo una conductancia) y se clasifica el espacio en verde/amarillo/rojo segun el resultado: habitable, corregible con una solucion y su costo, o sin ninguna solucion viable. Esa clasificacion se dibuja como un grafo coloreado (`grafo_habitabilidad.svg`), mostrando directamente sobre cada nodo amarillo cual es la solucion y cuanto cuesta, y se indexa en un arbol B por temperatura final para consultas eficientes.

La implementacion separa claramente datos, simulacion, evaluacion, clasificacion, balanceo, estructura de datos (arbol B) y visualizacion, cada una en su propio modulo con pruebas automatizadas. Las funciones no pretenden certificar habitabilidad real; son un modelo academico verificable, pensado para explicarse y extenderse.
