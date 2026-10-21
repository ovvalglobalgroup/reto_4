# Punto de entrada y menú principal del sistema
"""Sistema Integral de Gestión Académica SIGA

Ejecutar: python index.py
Demostración reproducible: python index.py --demo
Benchmarks: python index.py --benchmark
Pruebas: python -m unittest discover -s tests -v
"""

import argparse
import tempfile
from pathlib import Path
from src.sistema import SIGA
from src.persistencia import exportar, importar
from src.benchmarks import correr_benchmarks, guardar_benchmarks, tabla_resumen


BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"

# Prepara la carpeta donde se guardan los archivos
def obtener_directorio_datos() -> Path:
    """Crea y devuelve el directorio de datos del proyecto"""
    # Se crea la carpeta de datos solo cuando hace falta
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


# Lee un número y comprueba el límite indicado
def leer_entero(texto: str, minimo: int | None = None) -> int:
    """Solicita un entero y comprueba su rango mínimo"""
    # Se convierte el texto ingresado en un número entero
    numero = int(input(texto).strip())
    if minimo is not None and numero < minimo:
        raise ValueError(f"Debe ingresar un número mayor o igual a {minimo}")
    return numero


# Muestra inscritos, cupos y colas actuales
def mostrar_estado(sistema: SIGA) -> None:
    """Muestra cupos, inscritos y tres colas sin perder sus nodos"""
    print(f"\nCURSO: {sistema.curso} | CUPOS: {sistema.cupos} "
          f"| INSCRITOS: {sistema.inscritos.size()}")
    print("Inscritos:")
    # La lista de inscritos se lee sin modificarla
    for persona in sistema.inscritos.recorrer():
        print("  ", persona)
    if sistema.inscritos.is_empty():
        print("   (sin inscritos)")
    print("Simple:   ", sistema.cola_simple.mostrar())
    print("Circular: ", sistema.cola_circular.mostrar())
    print("Prioridad:", sistema.cola_prioridad.mostrar())
    print("Consistencia:", "OK" if sistema.validar_consistencia() else "ERROR")


# Permite revisar y editar el historial académico
def submenu_historial(sistema: SIGA) -> None:
    """Gestiona los semestres por estudiante y sus calificaciones"""
    # El submenú permanece activo hasta elegir volver
    while True:
        
        print("\n" + "*" * 56)
        print(" HISTORIAL")
        print("*" * 56 + "\n")
        print(" 1. Agregar semestre")
        print(" 2. Añadir/actualizar nota")
        print(" 3. Recorrer adelante")
        print(" 4. Recorrer atrás")
        print(" 5. Buscar")
        print(" 0. Volver")
        print("\n")
        opcion = input("Seleccione una opción ").strip()
        if opcion == "0":
            return
        # Evita operar con una opción inexistente
        if opcion not in ("1", "2", "3", "4", "5"):
            print("Opción no válida")
            continue
        estudiante_id = input("ID de estudiante: ").strip()
        if opcion == "1":
            anio, term = leer_entero("Año: "), leer_entero("Término (1-4): ")
            print(sistema.agregar_semestre(estudiante_id, anio, term))
        elif opcion == "2":
            anio, term = leer_entero("Año: "), leer_entero("Término: ")
            cod, nombre = input("Código materia: ").strip(), input("Nombre materia: ").strip()
            nota = float(input("Nota (0-20): ").strip())
            print(sistema.agregar_o_actualizar_nota(estudiante_id, anio, term, cod, nombre, nota))
        # Permite consultar los semestres en ambos sentidos
        elif opcion in ("3", "4"):
            semestres = sistema.recorrer_historial(estudiante_id, adelante=(opcion == "3"))
            encontrados = 0
            for semestre in semestres:
                encontrados += 1
                print(f"{semestre.anio}/{semestre.term}:")
                for materia in semestre.materias.recorrer():
                    print(f"   {materia.cod} - {materia.nombre}: {materia.nota:.2f}")
            if not encontrados:
                print("Sin semestres")
        else:
            anio, term = leer_entero("Año: "), leer_entero("Término: ")
            semestre = sistema.buscar_semestre(estudiante_id, anio, term)
            print("Encontrado:", f"{semestre.anio}/{semestre.term}" if semestre else "No existe")


# Presenta las opciones y atiende cada elección
def menu() -> None:
    """Ofrece las once opciones mínimas del enunciado"""
    # Al iniciar todavía no existe un curso
    # El programa inicia sin curso configurado
    sistema: SIGA | None = None

    # El menú vuelve a mostrarse después de cada operación
    while True:
        print("\n" + "*" * 56)
        print(" SISTEMA INTEGRAL DE GESTIÓN ACADÉMICA")
        print("*" * 56 + "\n")
        print(" 1. Configurar curso")
        print(" 2. Llegada de estudiante")
        print(" 3. Procesar N turnos")
        print(" 4. Retirar estudiante y reasignar")
        print(" 5. Mostrar inscritos")
        print(" 6. Mostrar todas las colas")
        print(" 7. Historial académico")
        print(" 8. Deshacer última acción")
        print(" 9. Exportar/importar")
        print("10. Benchmarks y tabla comparativa")
        print("11. Salir")

        try:
            print("\n")
            opcion = input("Seleccione una opción: ").strip()

            # Las pruebas y la salida funcionan sin crear un curso
            # Estas opciones necesitan que ya exista un curso
            if sistema is None and opcion in ("2", "3", "4", "5", "6", "7", "8"):
                print("AVISO: Primero debe configurar un curso mediante la opción 1")
                continue

            # Permite configurar el curso o reemplazarlo
            if opcion == "1":
                nombre = input("Nombre del curso: ").strip()
                cupos = leer_entero("Cupos: ", 0)
                if sistema is None:
                    sistema = SIGA(nombre, cupos)
                    print(f"Curso '{sistema.curso}' configurado con {sistema.cupos} cupos")
                else:
                    print(sistema.configurar_curso(nombre, cupos))

            # Recoge los datos del estudiante que llega
            elif opcion == "2":
                ident = input("ID: ").strip()
                nombre = input("Nombre: ").strip()
                correo = input("Correo (opcional): ").strip()
                texto = input("Prioridad 1-5 (Enter = normal): ").strip()
                prioridad = int(texto) if texto else None
                print(sistema.llegada(ident, nombre, correo, prioridad))

            # Procesa la cantidad solicitada de turnos
            elif opcion == "3":
                cantidad = leer_entero("Cantidad de turnos: ", 0)
                resultado = sistema.procesar_turnos(cantidad)
                print("\n".join(resultado) if resultado else "No hay turnos procesables")

            # Retira un inscrito y busca quien ocupe su lugar
            elif opcion == "4":
                ident = input("ID del inscrito a retirar: ").strip()
                print("\n".join(sistema.retirar(ident)))

            # Consulta a los estudiantes que ya tienen cupo
            elif opcion == "5":
                print(f"Inscritos ({sistema.inscritos.size()}/{sistema.cupos}):")
                for persona in sistema.inscritos.recorrer():
                    print(" ", persona)

            # Muestra el estado completo de las colas
            elif opcion == "6":
                mostrar_estado(sistema)

            # Abre las opciones del historial académico
            elif opcion == "7":
                submenu_historial(sistema)

            # Revierte la última operación guardada
            elif opcion == "8":
                print(sistema.deshacer())

            # Deja elegir entre exportar e importar datos
            elif opcion == "9":
                accion = input("E=Exportar / I=Importar: ").strip().upper()

                # Solo permite exportar cuando existe un curso
                if accion == "E":
                    # Exportar exige tener un curso configurado
                    if sistema is None:
                        print("AVISO: No existe un curso configurado para exportar")
                        print("Primero configure un curso mediante la opción 1")
                        continue

                    rutas = exportar(sistema, obtener_directorio_datos())
                    print("Archivos exportados correctamente")
                    for ruta in rutas:
                        print(" -", ruta)

                # Importar no exige configurar un curso antes
                elif accion == "I":
                    # Importar también funciona sin curso previo
                    # Sin carpeta de datos no hay archivos que recuperar
                    if not DATA_DIR.is_dir():
                        print("AVISO: No existe la carpeta de datos para importar")
                        continue

                    # La recuperación se hace primero en un sistema temporal
                    # Se crea una instancia temporal para importar
                    sistema_temporal = SIGA("Curso temporal", 0)
                    resultado = importar(sistema_temporal, DATA_DIR)

                    # Se comprueba que exista un curso recuperado
                    # Se comprueba que se haya recuperado un curso
                    if sistema_temporal.curso == "Curso temporal":
                        print("AVISO: No se pudo restaurar un curso desde los archivos")
                        continue

                    # Los datos nuevos deben pasar la validación
                    if not sistema_temporal.validar_consistencia():
                        print("AVISO: Los datos importados no son consistentes")
                        continue

                    # El sistema actual se sustituye solo al validar
                    # Solo entonces se reemplaza el sistema actual
                    sistema = sistema_temporal
                    print(resultado)

                else:
                    print("Debe elegir E o I")

            # Ejecuta las pruebas de rendimiento y guarda el CSV
            elif opcion == "10":
                print("Midiendo promedios de cinco ejecuciones por escenario..")
                resultados = correr_benchmarks()
                print(tabla_resumen(resultados))
                ruta = obtener_directorio_datos() / "benchmarks.csv"
                guardar_benchmarks(resultados, ruta)
                print("Resultados exportados correctamente:", ruta)

            # Termina el programa de forma normal
            elif opcion == "11":
                print("Saliendo de SIGA. Hasta pronto")
                return

            else:
                print("Opción no válida; use 1-11")

        # Los errores esperados se muestran sin cerrar el programa
        except (ValueError, IndexError, KeyError, TypeError, OSError) as error:
            print("AVISO:", error)
        # Permite salir al interrumpir la consola
        except (KeyboardInterrupt, EOFError):
            print("\nSesión finalizada")
            return


# Reproduce los ejemplos preparados para la entrega
def demo() -> None:
    """Ejecuta los siete casos mínimos sin inventar resultados"""
    print("SIGA | DEMOSTRACIÓN REPRODUCIBLE DEL RETO 4")
    # Se utiliza un curso pequeño para repetir los casos
    s = SIGA("Estructuras de Datos", 3)
    print("\n[CASO 1 y 2] Dos normales, dos prioritarios y tres cupos")
    for argumentos in (("1001", "Ana", "", None),
                       ("1002", "Luis", "", None),
                       ("1003", "Carla", "", 5),
                       ("1004", "Mario", "", 3)):
        print(s.llegada(*argumentos))
    print("Atención de 3 turnos:")
    for evento in s.procesar_turnos(3):
        print(" ", evento)
    print("Orden esperado: Carla(p=5), Mario(p=3), Ana(normal)")
    print("Atención adicional con cupo lleno:")
    for evento in s.procesar_turnos(1):
        print(" ", evento)
    print(s.llegada("1005", "Sofía"))
    for evento in s.procesar_turnos(1):
        print(" ", evento)
    mostrar_estado(s)

    # Se comprueba la retirada y la reasignación
    print("\n[CASO 3] Retirar y reasignar: prioridad antes que circular")
    print(s.llegada("1006", "Diego", prioridad=4))
    for evento in s.retirar("1001"):
        print(" ", evento)
    for evento in s.retirar("1003"):
        print(" ", evento)
    mostrar_estado(s)

    # Se comprueba la opción para deshacer
    print("\n[CASO 4] DESHACER de REASIGNAR y de INSCRIBIR")
    print(s.deshacer())
    mostrar_estado(s)
    t = SIGA("Curso auxiliar para deshacer", 1)
    t.llegada("2001", "Elena")
    print("Antes:", t.cola_simple.mostrar())
    print("Procesar:", t.procesar_turnos(1))
    print("Deshacer:", t.deshacer())
    print("Restaurada cola simple:", t.cola_simple.mostrar())
    print("Inscritos:", t.inscritos.size())

    # Se prueba el orden de los semestres
    print("\n[CASO 5] Semestres fuera de orden; ambos recorridos y búsqueda")
    for anio, term in ((2025, 2), (2024, 1), (2025, 1)):
        print(s.agregar_semestre("1003", anio, term))
    print("Ascendente:", [(x.anio, x.term) for x in s.recorrer_historial("1003")])
    print("Descendente:", [(x.anio, x.term) for x in s.recorrer_historial("1003", False)])
    print("Búsqueda 2025/1:", bool(s.buscar_semestre("1003", 2025, 1)))
    print(s.agregar_o_actualizar_nota("1003", 2025, 1, "ED-101", "Estructuras I", 18))
    print(s.agregar_o_actualizar_nota("1003", 2025, 1, "ED-101", "Estructuras I", 19))

    print("\n[CASO 6] Persistencia y reconstrucción")
    # Los archivos de prueba se guardan temporalmente
    with tempfile.TemporaryDirectory(prefix="siga_prueba_") as carpeta:
        rutas = exportar(s, carpeta)
        print("Exportados:", ", ".join(Path(p).name for p in rutas))
        restaurado = SIGA("Otro curso", 0)
        print(importar(restaurado, carpeta))
        print("Datos idénticos:", restaurado.a_dict() == s.a_dict())
        print("Consistencia:", restaurado.validar_consistencia())
    print("\n[CASO 7] Ejecutar 'python index.py --benchmark' para tabla de tiempos")


# Elige entre menú, demostración y pruebas de rendimiento
def main() -> None:
    """Selecciona el modo interactivo, demostración o medición"""
    # Prepara los parámetros que acepta la consola
    parser = argparse.ArgumentParser(description="SIGA: proyecto final de estructuras enlazadas")
    parser.add_argument("--demo", action="store_true", help="demostración de los casos exigidos")
    parser.add_argument("--benchmark", action="store_true", help="medición con perf_counter y CSV")
    args = parser.parse_args()
    # Ejecuta la demostración cuando se solicita
    if args.demo:
        demo()
    # Ejecuta la medición cuando se solicita
    if args.benchmark:
        mediciones = correr_benchmarks()
        print("\n[CASO 7] RESULTADOS DE EFICIENCIA")
        print(tabla_resumen(mediciones))
        ruta = obtener_directorio_datos() / "benchmarks.csv"
        guardar_benchmarks(mediciones, ruta)
        print("Resultados guardados:", ruta)
    # Sin parámetros se abre el menú principal
    if not args.demo and not args.benchmark:
        menu()


if __name__ == "__main__":
    main()
