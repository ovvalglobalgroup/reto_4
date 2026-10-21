"""Sistema Integral de Gestión Académica SIGA - Reto 4

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

def obtener_directorio_datos() -> Path:
    """Crea y devuelve el directorio de datos del proyecto"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def leer_entero(texto: str, minimo: int | None = None) -> int:
    """Solicita un entero y comprueba su rango mínimo"""
    numero = int(input(texto).strip())
    if minimo is not None and numero < minimo:
        raise ValueError(f"Debe ingresar un número mayor o igual a {minimo}")
    return numero


def mostrar_estado(sistema: SIGA) -> None:
    """Muestra cupos, inscritos y tres colas sin perder sus nodos"""
    print(f"\nCURSO: {sistema.curso} | CUPOS: {sistema.cupos} "
          f"| INSCRITOS: {sistema.inscritos.size()}")
    print("Inscritos:")
    for persona in sistema.inscritos.recorrer():
        print("  ", persona)
    if sistema.inscritos.is_empty():
        print("   (sin inscritos)")
    print("Simple:   ", sistema.cola_simple.mostrar())
    print("Circular: ", sistema.cola_circular.mostrar())
    print("Prioridad:", sistema.cola_prioridad.mostrar())
    print("Consistencia:", "OK" if sistema.validar_consistencia() else "ERROR")


def submenu_historial(sistema: SIGA) -> None:
    """Gestiona los semestres por estudiante y sus calificaciones"""
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


def menu() -> None:
    """Ofrece las once opciones mínimas del enunciado"""
    # No hay curso configurado hasta seleccionar la opción 1.
    sistema: SIGA | None = None

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

            # Las operaciones del curso requieren una configuración previa.
            # Los benchmarks y la salida funcionan sin un curso creado.
            if sistema is None and opcion in ("2", "3", "4", "5", "6", "7", "8", "9"):
                print("AVISO: Primero debe configurar un curso mediante la opción 1.")
                continue

            if opcion == "1":
                nombre = input("Nombre del curso: ").strip()
                cupos = leer_entero("Cupos: ", 0)
                if sistema is None:
                    sistema = SIGA(nombre, cupos)
                    print(f"Curso '{sistema.curso}' configurado con {sistema.cupos} cupos")
                else:
                    print(sistema.configurar_curso(nombre, cupos))

            elif opcion == "2":
                ident = input("ID: ").strip()
                nombre = input("Nombre: ").strip()
                correo = input("Correo (opcional): ").strip()
                texto = input("Prioridad 1-5 (Enter = normal): ").strip()
                prioridad = int(texto) if texto else None
                print(sistema.llegada(ident, nombre, correo, prioridad))

            elif opcion == "3":
                cantidad = leer_entero("Cantidad de turnos: ", 0)
                resultado = sistema.procesar_turnos(cantidad)
                print("\n".join(resultado) if resultado else "No hay turnos procesables")

            elif opcion == "4":
                ident = input("ID del inscrito a retirar: ").strip()
                print("\n".join(sistema.retirar(ident)))

            elif opcion == "5":
                print(f"Inscritos ({sistema.inscritos.size()}/{sistema.cupos}):")
                for persona in sistema.inscritos.recorrer():
                    print(" ", persona)

            elif opcion == "6":
                mostrar_estado(sistema)

            elif opcion == "7":
                submenu_historial(sistema)

            elif opcion == "8":
                print(sistema.deshacer())

            elif opcion == "9":
                accion = input("E=Exportar / I=Importar: ").strip().upper()

                if accion == "E":
                    # Generar data/ solo al exportar; ruta única para CSV/JSON.
                    rutas = exportar(sistema, obtener_directorio_datos())
                    print("Archivos exportados correctamente:")
                    for ruta in rutas:
                        print(" -", ruta)

                elif accion == "I":
                    # Importar no crea carpetas ni archivos vacíos.
                    if not DATA_DIR.is_dir():
                        print("AVISO: No existe la carpeta de datos para importar.")
                    else:
                        print(importar(sistema, DATA_DIR))

                else:
                    print("Debe elegir E o I")

            elif opcion == "10":
                print("Midiendo promedios de cinco ejecuciones por escenario...")
                resultados = correr_benchmarks()
                print(tabla_resumen(resultados))
                ruta = obtener_directorio_datos() / "benchmarks.csv"
                guardar_benchmarks(resultados, ruta)
                print("Resultados exportados correctamente:", ruta)

            elif opcion == "11":
                print("Saliendo de SIGA. Hasta pronto")
                return

            else:
                print("Opción no válida; use 1-11")

        except (ValueError, IndexError, KeyError, TypeError, OSError) as error:
            print("AVISO:", error)
        except (KeyboardInterrupt, EOFError):
            print("\nSesión finalizada")
            return


def demo() -> None:
    """Ejecuta los siete casos mínimos sin inventar resultados"""
    print("SIGA | DEMOSTRACIÓN REPRODUCIBLE DEL RETO 4")
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

    print("\n[CASO 3] Retirar y reasignar: prioridad antes que circular")
    print(s.llegada("1006", "Diego", prioridad=4))
    for evento in s.retirar("1001"):
        print(" ", evento)
    for evento in s.retirar("1003"):
        print(" ", evento)
    mostrar_estado(s)

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

    print("\n[CASO 5] Semestres fuera de orden; ambos recorridos y búsqueda")
    for anio, term in ((2025, 2), (2024, 1), (2025, 1)):
        print(s.agregar_semestre("1003", anio, term))
    print("Ascendente:", [(x.anio, x.term) for x in s.recorrer_historial("1003")])
    print("Descendente:", [(x.anio, x.term) for x in s.recorrer_historial("1003", False)])
    print("Búsqueda 2025/1:", bool(s.buscar_semestre("1003", 2025, 1)))
    print(s.agregar_o_actualizar_nota("1003", 2025, 1, "ED-101", "Estructuras I", 18))
    print(s.agregar_o_actualizar_nota("1003", 2025, 1, "ED-101", "Estructuras I", 19))

    print("\n[CASO 6] Persistencia y reconstrucción")
    with tempfile.TemporaryDirectory(prefix="siga_prueba_") as carpeta:
        rutas = exportar(s, carpeta)
        print("Exportados:", ", ".join(Path(p).name for p in rutas))
        restaurado = SIGA("Otro curso", 0)
        print(importar(restaurado, carpeta))
        print("Datos idénticos:", restaurado.a_dict() == s.a_dict())
        print("Consistencia:", restaurado.validar_consistencia())
    print("\n[CASO 7] Ejecutar 'python index.py --benchmark' para tabla de tiempos")


def main() -> None:
    """Selecciona el modo interactivo, demostración o medición"""
    parser = argparse.ArgumentParser(description="SIGA: proyecto final de estructuras enlazadas")
    parser.add_argument("--demo", action="store_true", help="demostración de los casos exigidos")
    parser.add_argument("--benchmark", action="store_true", help="medición con perf_counter y CSV")
    args = parser.parse_args()
    if args.demo:
        demo()
    if args.benchmark:
        mediciones = correr_benchmarks()
        print("\n[CASO 7] RESULTADOS DE EFICIENCIA")
        print(tabla_resumen(mediciones))
        ruta = obtener_directorio_datos() / "benchmarks.csv"
        guardar_benchmarks(mediciones, ruta)
        print("Resultados guardados:", ruta)
    if not args.demo and not args.benchmark:
        menu()


if __name__ == "__main__":
    main()
