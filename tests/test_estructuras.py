"""Pruebas unitarias de las estructuras enlazadas del SIGA"""

import unittest
from src.estructuras import (Pila, ColaSimple, ColaCircular,
                             ColaPrioridad, ListaSimple, ListaDoble)
from src.modelos import Estudiante, Semestre


class PruebasPila(unittest.TestCase):
    """Verifica LIFO y underflow"""

    def test_push_pop_peek(self):
        pila = Pila()
        self.assertTrue(pila.is_empty())
        pila.push("a")
        pila.push("b")
        self.assertEqual(pila.peek(), "b")
        self.assertEqual(pila.size(), 2)
        self.assertEqual(pila.pop(), "b")
        self.assertEqual(pila.pop(), "a")
        self.assertTrue(pila.is_empty())

    def test_pila_vacia_lanza_excepcion(self):
        pila = Pila()
        with self.assertRaises(IndexError):
            pila.pop()
        with self.assertRaises(IndexError):
            pila.peek()


class PruebasColas(unittest.TestCase):
    """Comprueba FIFO, prioridad y límites de las tres colas"""

    def test_cola_simple_fifo(self):
        cola = ColaSimple()
        cola.enqueue("Ana")
        cola.enqueue("Luis")
        self.assertEqual(cola.front(), "Ana")
        self.assertEqual(cola.dequeue(), "Ana")
        self.assertEqual(cola.dequeue(), "Luis")
        self.assertTrue(cola.is_empty())

    def test_cola_simple_underflow(self):
        cola = ColaSimple()
        with self.assertRaises(IndexError):
            cola.front()
        with self.assertRaises(IndexError):
            cola.dequeue()

    def test_cola_circular_estructura_circular(self):
        cola = ColaCircular()
        for x in (1, 2, 3):
            cola.enqueue(x)
        self.assertIs(cola._ultimo.siguiente.siguiente.siguiente, cola._ultimo)
        self.assertEqual(tuple(cola.recorrer()), (1, 2, 3))
        self.assertEqual(cola.dequeue(), 1)
        cola.enqueue(4)
        self.assertEqual(tuple(cola.recorrer()), (2, 3, 4))
        self.assertEqual(cola.front(), 2)

    def test_cola_circular_un_nodo_y_underflow(self):
        cola = ColaCircular()
        cola.enqueue("único")
        self.assertEqual(cola.dequeue(), "único")
        self.assertTrue(cola.is_empty())
        with self.assertRaises(IndexError):
            cola.dequeue()
        with self.assertRaises(IndexError):
            cola.front()

    def test_prioridad_orden_y_empates_fifo(self):
        cola = ColaPrioridad()
        for e in (Estudiante("a", "A", prioridad=3),
                  Estudiante("b", "B", prioridad=5),
                  Estudiante("c", "C", prioridad=5),
                  Estudiante("d", "D", prioridad=1)):
            cola.enqueue(e)
        self.assertEqual(cola.front().id, "b")
        self.assertEqual(tuple(e.id for e in cola.recorrer()), ("b", "c", "a", "d"))
        self.assertEqual(tuple(cola.dequeue().id for _ in range(4)), ("b", "c", "a", "d"))
        self.assertTrue(cola.is_empty())

    def test_prioridad_invalida_underflow(self):
        cola = ColaPrioridad()
        with self.assertRaises(ValueError):
            cola.enqueue("ejemplo", prioridad=0)
        with self.assertRaises(ValueError):
            cola.enqueue("ejemplo", prioridad=6)
        with self.assertRaises(IndexError):
            cola.front()
        with self.assertRaises(IndexError):
            cola.dequeue()


class PruebasListas(unittest.TestCase):
    """Comprueba inserción, búsqueda, eliminación y enlaces reversos"""

    def test_lista_simple_buscar_eliminar_cabeza_medio_final(self):
        lista = ListaSimple()
        for i in range(5):
            lista.insertar(i)
        self.assertEqual(lista.buscar(2), 2)
        self.assertEqual(lista.eliminar(0), 0)
        self.assertEqual(lista.eliminar(2), 2)
        self.assertEqual(lista.eliminar(4), 4)
        self.assertEqual(tuple(lista.recorrer()), (1, 3))
        self.assertEqual(lista.size(), 2)

    def test_lista_simple_vacia_y_no_encontrado(self):
        lista = ListaSimple()
        self.assertIsNone(lista.buscar("x"))
        self.assertIsNone(lista.eliminar("x"))
        lista.insertar("x")
        self.assertEqual(lista.eliminar("x"), "x")
        self.assertTrue(lista.is_empty())
        lista.insertar("y")
        self.assertEqual(tuple(lista.recorrer()), ("y",))

    def test_lista_doble_ordenamiento_y_recorridos(self):
        lista = ListaDoble()
        for anio, term in ((2025, 2), (2024, 1), (2025, 1)):
            lista.insertar_ordenado(Semestre(anio, term), lambda s: s.clave())
        self.assertEqual(tuple(s.clave() for s in lista.recorrer_adelante()),
                         ((2024, 1), (2025, 1), (2025, 2)))
        self.assertEqual(tuple(s.clave() for s in lista.recorrer_atras()),
                         ((2025, 2), (2025, 1), (2024, 1)))
        self.assertIsNotNone(lista.buscar((2025, 1), lambda s: s.clave()))

    def test_lista_doble_eliminar_extremos_y_medio(self):
        lista = ListaDoble()
        for i in (3, 1, 5, 2, 4):
            lista.insertar_ordenado(i, lambda x: x)
        self.assertEqual(lista.eliminar(1), 1)
        self.assertEqual(lista.eliminar(3), 3)
        self.assertEqual(lista.eliminar(5), 5)
        self.assertEqual(tuple(lista.recorrer_adelante()), (2, 4))
        self.assertEqual(tuple(lista.recorrer_atras()), (4, 2))
        self.assertIsNone(lista.eliminar(100))

    def test_lista_doble_vacia_y_un_nodo(self):
        lista = ListaDoble()
        self.assertEqual(tuple(lista.recorrer_atras()), ())
        lista.insertar_ordenado(4, lambda x: x)
        with self.assertRaises(ValueError):
            lista.insertar_ordenado(4, lambda x: x)
        self.assertEqual(lista.eliminar(4), 4)
        self.assertTrue(lista.is_empty())
        lista.agregar_final(6)
        lista.agregar_final(7)
        with self.assertRaises(ValueError):
            lista.agregar_final(5)
        self.assertEqual(tuple(lista.recorrer_atras()), (7, 6))


if __name__ == "__main__":
    unittest.main()
