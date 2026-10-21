# Pruebas de rendimiento para comparar las estructuras
"""Comparación reproducible de operaciones con cinco ejecuciones por escenario"""

import csv
import statistics
import time
from pathlib import Path
from .estructuras import ListaSimple, ListaDoble, ColaSimple, ColaCircular, ColaPrioridad
from .modelos import Estudiante


# Calcula el tiempo medio de varias ejecuciones
def _medir(funcion, repeticiones: int = 5) -> tuple[float, float]:
    """Devuelve promedio y desviación en milisegundos"""
    mediciones = []
    # Se ejecuta la misma operación varias veces
    for _ in range(repeticiones):
        # Se mide el tiempo con un reloj de alta precisión
        inicio = time.perf_counter()
        funcion()
        mediciones.append((time.perf_counter() - inicio) * 1000)
    return (statistics.mean(mediciones), statistics.pstdev(mediciones))


# Prepara una lista simple para la prueba
def _rellenar_simple(n: int) -> ListaSimple:
    lista = ListaSimple()
    # Se insertan tantos elementos como indique la prueba
    for i in range(n):
        lista.insertar(i)
    return lista


# Prepara una lista doble para la prueba
def _rellenar_doble(n: int) -> ListaDoble:
    lista = ListaDoble()
    # La lista doble se llena en orden ascendente
    for i in range(n):
        lista.agregar_final(i)
    return lista


# Ejecuta las comparaciones de rendimiento
def correr_benchmarks(repeticiones: int = 5) -> list[dict]:
    """Mide inserción, búsqueda, eliminación y throughput por tamaños.

    Incluye preparación fuera de los segmentos medidos para las búsquedas
    y eliminaciones. No mide E/S, impresión ni construcción de fixtures.
    """
    resultados = []

    # Guarda cada medición y su variación
    def agregar(estructura: str, operacion: str, n: int, escenario: str, fn) -> None:
        promedio, desviacion = _medir(fn, repeticiones)
        resultados.append({"estructura": estructura, "operacion": operacion,
                           "n": n, "escenario": escenario,
                           "promedio_ms": round(promedio, 6),
                           "desviacion_ms": round(desviacion, 6),
                           "repeticiones": repeticiones})

    # Se repiten pruebas con tres tamaños diferentes
    for n in (1000, 5000, 10000):
        agregar("ListaSimple", "insertar n nodos", n, "total", lambda n=n: _rellenar_simple(n))
        # Se revisan posiciones del inicio, medio y final
        for escenario, posicion in (("inicio", 0), ("medio", n // 2), ("fin", n - 1)):
            lista = _rellenar_simple(n)
            agregar("ListaSimple", "buscar", n, escenario,
                    lambda lista=lista, posicion=posicion: lista.buscar(posicion))
        for escenario, posicion in (("inicio", 0), ("medio", n // 2), ("fin", n - 1)):
            # Mide la eliminación en una lista simple
            def borrar_simple(n=n, posicion=posicion):
                # La preparación de datos queda fuera del tiempo medido
                lista = _rellenar_simple(n)
                inicio = time.perf_counter()
                lista.eliminar(posicion)
                return (time.perf_counter() - inicio) * 1000

            # Mide la eliminación en una lista doble
            def borrar_doble(n=n, posicion=posicion):
                # La preparación de datos queda fuera del tiempo medido
                lista = _rellenar_doble(n)
                inicio = time.perf_counter()
                lista.eliminar(posicion)
                return (time.perf_counter() - inicio) * 1000

            # Los datos se preparan antes de medir la eliminación
            for estructura, preparador in (("ListaSimple", borrar_simple), ("ListaDoble", borrar_doble)):
                tiempos = [preparador() for _ in range(repeticiones)]
                resultados.append({"estructura": estructura, "operacion": "eliminar",
                                   "n": n, "escenario": escenario,
                                   "promedio_ms": round(statistics.mean(tiempos), 6),
                                   "desviacion_ms": round(statistics.pstdev(tiempos), 6),
                                   "repeticiones": repeticiones})

    # También se comparan las tres clases de cola
    for nombre, constructor in (("ColaSimple", ColaSimple),
                                ("ColaCircular", ColaCircular),
                                ("ColaPrioridad", ColaPrioridad)):
        # Prueba entradas y salidas de una cola
        def probar_conjunto(constructor=constructor, nombre=nombre):
            cola = constructor()
            # Se agregan diez mil elementos a cada cola
            for i in range(10000):
                if nombre == "ColaPrioridad":
                    cola.enqueue(Estudiante(str(i), "Estudiante", prioridad=1 + i % 5))
                else:
                    cola.enqueue(i)
            # Después se retiran todos los elementos
            for _ in range(10000):
                cola.dequeue()
            assert cola.is_empty()

        agregar(nombre, "enqueue + dequeue", 10000, "10k + 10k", probar_conjunto)
    return resultados


# Escribe los resultados en un archivo CSV
def guardar_benchmarks(resultados: list[dict], ruta: str | Path) -> None:
    """Conserva los tiempos reales para reproducir el informe"""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # La carpeta de resultados se prepara antes de guardar
    # No se genera un CSV sin resultados
    if not resultados:
        raise ValueError("No hay mediciones que exportar")
    # La codificación permite abrir el archivo en Excel
    with ruta.open("w", newline="", encoding="utf-8-sig") as salida:
        escritor = csv.DictWriter(salida, fieldnames=resultados[0].keys())
        escritor.writeheader()
        escritor.writerows(resultados)


# Prepara la tabla de resultados para la consola
def tabla_resumen(resultados: list[dict]) -> str:
    """Construye una tabla monoespaciada para la CLI"""
    filas = ["Estructura       Operación            n     Escenario    media (ms)   sd (ms)",
             "-" * 79]
    # Cada medición ocupa una fila de la tabla
    for fila in resultados:
        filas.append(f"{fila['estructura']:<16}{fila['operacion']:<21}"
                     f"{fila['n']:>6}  {fila['escenario']:<11}"
                     f"{fila['promedio_ms']:>11.5f}  {fila['desviacion_ms']:>9.5f}")
    return "\n".join(filas)
