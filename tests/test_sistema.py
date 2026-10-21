"""Pruebas de integración, persistencia y errores sin pérdida de datos"""

import json
import tempfile
import unittest
from pathlib import Path
from src.sistema import SIGA
from src.persistencia import exportar, importar


class PruebasSIGA(unittest.TestCase):
    """Valida escenarios normales, críticos y situaciones límite"""

    def setUp(self):
        self.sistema = SIGA("Programación II", 3)

    def test_dos_normales_dos_criticos_y_tres_inscripciones(self):
        s = self.sistema
        s.llegada("1", "Ana")
        s.llegada("2", "Luis")
        s.llegada("3", "Carla", prioridad=5)
        s.llegada("4", "Mario", prioridad=3)
        mensajes = s.procesar_turnos(3)
        self.assertEqual(tuple(x.id for x in s.inscritos.recorrer()), ("3", "4", "1"))
        self.assertEqual(len(mensajes), 3)
        self.assertTrue(s.validar_consistencia())

    def test_saturacion_envia_espera_circular(self):
        s = SIGA("Curso", 1)
        s.llegada("1", "Ana")
        s.llegada("2", "Luis")
        s.procesar_turnos(2)
        self.assertEqual(s.inscritos.size(), 1)
        self.assertEqual(s.cola_circular.front().id, "2")

    def test_cupos_cero_no_inscribe(self):
        s = SIGA("Curso sin cupos", 0)
        s.llegada("1", "Ana")
        s.llegada("2", "Carla", prioridad=5)
        s.procesar_turnos(2)
        self.assertEqual(s.inscritos.size(), 0)
        self.assertEqual(s.cola_circular.front().id, "1")
        self.assertEqual(s.cola_prioridad.front().id, "2")

    def test_reasigna_prioridad_luego_circular(self):
        s = SIGA("Curso", 1)
        s.llegada("1", "Ana")
        s.llegada("2", "Luis")
        s.procesar_turnos(2)
        s.llegada("3", "Carla", prioridad=5)
        s.retirar("1")
        self.assertEqual(s.inscritos.buscar("3", lambda e: e.id).nombre, "Carla")
        s.retirar("3")
        self.assertEqual(s.inscritos.buscar("2", lambda e: e.id).nombre, "Luis")

    def test_deshacer_reasignacion_restituye_espera(self):
        s = SIGA("Curso", 1)
        s.llegada("1", "Ana")
        s.llegada("2", "Luis")
        s.procesar_turnos(2)
        anterior = s.a_dict()
        s.retirar("1")
        s.deshacer()
        self.assertEqual(s.a_dict(), anterior)

    def test_deshacer_inscripcion_restituye_cola_simple(self):
        s = SIGA("Curso", 1)
        s.llegada("1", "Ana")
        anterior = s.a_dict()
        s.procesar_turnos(1)
        s.deshacer()
        self.assertEqual(s.a_dict(), anterior)

    def test_deshacer_pila_vacia(self):
        with self.assertRaises(IndexError):
            self.sistema.deshacer()

    def test_retirar_no_inscrito_no_cambia_estado(self):
        anterior = self.sistema.a_dict()
        with self.assertRaises(ValueError):
            self.sistema.retirar("inexistente")
        self.assertEqual(self.sistema.a_dict(), anterior)

    def test_identificador_repetido_rechazado(self):
        self.sistema.llegada("1", "Ana")
        with self.assertRaises(ValueError):
            self.sistema.llegada("1", "Duplicado", prioridad=5)

    def test_retiros_masivos(self):
        s = SIGA("Curso", 5)
        for i in range(9):
            s.llegada(str(i), f"Estudiante {i}")
        s.procesar_turnos(9)
        for i in range(5):
            s.retirar(str(i))
        self.assertEqual(s.inscritos.size(), 4)
        self.assertTrue(s.cola_circular.is_empty())
        self.assertTrue(s.validar_consistencia())

    def test_historial_vacio_recorridos(self):
        self.assertEqual(tuple(self.sistema.recorrer_historial("1")), ())
        self.assertIsNone(self.sistema.buscar_semestre("1", 2025, 1))

    def test_historial_cronologico_y_actualizar_nota(self):
        s = self.sistema
        s.llegada("1", "Ana")
        s.agregar_semestre("1", 2025, 2)
        s.agregar_semestre("1", 2024, 1)
        s.agregar_semestre("1", 2025, 1)
        self.assertEqual(tuple(x.clave() for x in s.recorrer_historial("1")),
                         ((2024, 1), (2025, 1), (2025, 2)))
        self.assertEqual(tuple(x.clave() for x in s.recorrer_historial("1", False)),
                         ((2025, 2), (2025, 1), (2024, 1)))
        s.agregar_o_actualizar_nota("1", 2025, 1, "ED-101", "Estructuras", 18)
        s.agregar_o_actualizar_nota("1", 2025, 1, "ED-101", "Estructuras", 19)
        semestre = s.buscar_semestre("1", 2025, 1)
        self.assertEqual(semestre.materias.size(), 1)
        self.assertEqual(semestre.materias.buscar("ED-101", lambda m: m.cod).nota, 19)
        s.deshacer()
        self.assertEqual(s.buscar_semestre("1", 2025, 1).materias.buscar(
            "ED-101", lambda m: m.cod).nota, 18)

    def test_semestre_duplicado_rechazado(self):
        self.sistema.llegada("1", "Ana")
        self.sistema.agregar_semestre("1", 2025, 1)
        with self.assertRaises(ValueError):
            self.sistema.agregar_semestre("1", 2025, 1)

    def test_notas_fuera_escala_rechazadas(self):
        self.sistema.llegada("1", "Ana")
        self.sistema.agregar_semestre("1", 2025, 1)
        with self.assertRaises(ValueError):
            self.sistema.agregar_o_actualizar_nota("1", 2025, 1, "A", "Álgebra", 21)

    def test_retiro_conserva_historial(self):
        s = SIGA("Curso", 1)
        s.llegada("1", "Ana")
        s.procesar_turnos(1)
        s.agregar_semestre("1", 2025, 1)
        s.retirar("1")
        self.assertTrue(s.validar_consistencia())
        self.assertIsNotNone(SIGA.desde_dict(s.a_dict()).buscar_semestre("1", 2025, 1))

    def test_exportar_importar_conserva_orden_y_datos(self):
        s = self.sistema
        s.llegada("1", "Ana", "ana@example.com")
        s.llegada("2", "Luis")
        s.llegada("3", "Carla", prioridad=5)
        s.llegada("4", "Mario", prioridad=3)
        s.procesar_turnos(4)
        s.agregar_semestre("3", 2024, 2)
        s.agregar_o_actualizar_nota("3", 2024, 2, "ED-1", "Datos", 18)
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = exportar(s, carpeta)
            self.assertEqual(len(rutas), 3)
            self.assertTrue(all(x.is_file() for x in rutas))
            copia = SIGA("Sin datos", 0)
            importar(copia, carpeta)
            self.assertEqual(copia.a_dict(), s.a_dict())
            self.assertTrue(copia.validar_consistencia())

    def test_json_corrupto_no_destruye_estado(self):
        s = self.sistema
        s.llegada("1", "Ana")
        anterior = s.a_dict()
        with tempfile.TemporaryDirectory() as carpeta:
            exportar(s, carpeta)
            Path(carpeta, "esperas.json").write_text("{JSON MAL FORMADO", encoding="utf-8")
            with self.assertRaises(ValueError):
                importar(s, carpeta)
        self.assertEqual(s.a_dict(), anterior)

    def test_importacion_ids_duplicados_no_modifica(self):
        s = self.sistema
        s.llegada("1", "Ana")
        anterior = s.a_dict()
        mal = s.a_dict()
        mal["circular"].append(mal["simple"][0].copy())
        with self.assertRaises(ValueError):
            s.importar_estado(mal)
        self.assertEqual(s.a_dict(), anterior)

    def test_importacion_cupos_insuficientes_no_modifica(self):
        s = self.sistema
        s.llegada("1", "Ana")
        s.procesar_turnos(1)
        anterior = s.a_dict()
        mal = s.a_dict()
        mal["cupos"] = 0
        with self.assertRaises(ValueError):
            s.importar_estado(mal)
        self.assertEqual(s.a_dict(), anterior)

    def test_csv_corrupto_no_modifica(self):
        s = self.sistema
        s.llegada("1", "Ana")
        anterior = s.a_dict()
        with tempfile.TemporaryDirectory() as carpeta:
            exportar(s, carpeta)
            Path(carpeta, "inscritos.csv").write_text("columna_errónea\n1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                importar(s, carpeta)
        self.assertEqual(s.a_dict(), anterior)


if __name__ == "__main__":
    unittest.main()
