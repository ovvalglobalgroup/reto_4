"""Implementaciones propias de estructuras enlazadas (sin list/deque como base)"""

from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional


@dataclass
class NodoSimple:
    """Almacena un elemento y la referencia al siguiente nodo"""
    valor: Any
    siguiente: Optional["NodoSimple"] = None


@dataclass
class NodoDoble:
    """Almacena un elemento y las referencias de una lista doble"""
    valor: Any
    anterior: Optional["NodoDoble"] = None
    siguiente: Optional["NodoDoble"] = None


class Pila:
    """Implementa una pila LIFO con inserción y extracción O(1)"""

    def __init__(self) -> None:
        self._cima = None
        self._n = 0

    def push(self, valor: Any) -> None:
        """Agrega el valor a la cima"""
        self._cima = NodoSimple(valor, self._cima)
        self._n += 1

    def pop(self) -> Any:
        """Extrae la cima; lanza IndexError si está vacía"""
        if self.is_empty():
            raise IndexError("Pila vacía (underflow)")
        valor = self._cima.valor
        self._cima = self._cima.siguiente
        self._n -= 1
        return valor

    def peek(self) -> Any:
        """Consulta la cima sin eliminarla"""
        if self.is_empty():
            raise IndexError("Pila vacía (underflow)")
        return self._cima.valor

    def is_empty(self) -> bool:
        """Indica si no hay elementos"""
        return self._n == 0

    def size(self) -> int:
        """Obtiene la cantidad de elementos"""
        return self._n


class ColaSimple:
    """Cola FIFO enlazada con extremos; enqueue y dequeue O(1)"""

    def __init__(self) -> None:
        self._inicio = None
        self._fin = None
        self._n = 0

    def enqueue(self, valor: Any) -> None:
        """Inserta al final de la cola"""
        nodo = NodoSimple(valor)
        if self._fin is None:
            self._inicio = nodo
        else:
            self._fin.siguiente = nodo
        self._fin = nodo
        self._n += 1

    def dequeue(self) -> Any:
        """Retira el primero; informa underflow mediante IndexError"""
        if self.is_empty():
            raise IndexError("Cola simple vacía (underflow)")
        valor = self._inicio.valor
        self._inicio = self._inicio.siguiente
        self._n -= 1
        if self._inicio is None:
            self._fin = None
        return valor

    def front(self) -> Any:
        """Consulta el primer elemento"""
        if self.is_empty():
            raise IndexError("Cola simple vacía (underflow)")
        return self._inicio.valor

    def is_empty(self) -> bool:
        """Indica si no hay turnos"""
        return self._n == 0

    def size(self) -> int:
        """Cuenta los turnos pendientes"""
        return self._n

    def recorrer(self) -> Iterator[Any]:
        """Itera sin transformar la cola en una lista"""
        actual = self._inicio
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    def mostrar(self) -> str:
        """Devuelve una vista legible del orden FIFO"""
        return " -> ".join(str(item) for item in self.recorrer()) or "(vacía)"


class ColaCircular:
    """Lista circular simple para espera FIFO y reasignación O(1)"""

    def __init__(self) -> None:
        self._ultimo = None
        self._n = 0

    def enqueue(self, valor: Any) -> None:
        """Agrega un nodo conservando el enlace circular"""
        nodo = NodoSimple(valor)
        if self._ultimo is None:
            nodo.siguiente = nodo
            self._ultimo = nodo
        else:
            nodo.siguiente = self._ultimo.siguiente
            self._ultimo.siguiente = nodo
            self._ultimo = nodo
        self._n += 1

    def dequeue(self) -> Any:
        """Retira el nodo más antiguo"""
        if self.is_empty():
            raise IndexError("Cola circular vacía (underflow)")
        primero = self._ultimo.siguiente
        valor = primero.valor
        if self._n == 1:
            self._ultimo = None
        else:
            self._ultimo.siguiente = primero.siguiente
        self._n -= 1
        return valor

    def front(self) -> Any:
        """Consulta el primero sin retirarlo"""
        if self.is_empty():
            raise IndexError("Cola circular vacía (underflow)")
        return self._ultimo.siguiente.valor

    def is_empty(self) -> bool:
        """Indica si la espera está vacía"""
        return self._n == 0

    def size(self) -> int:
        """Cuenta los elementos de la cola circular"""
        return self._n

    def recorrer(self) -> Iterator[Any]:
        """Recorre exactamente n nodos para evitar ciclos infinitos"""
        if self._ultimo is not None:
            actual = self._ultimo.siguiente
            for _ in range(self._n):
                yield actual.valor
                actual = actual.siguiente

    def mostrar(self) -> str:
        """Representa la espera en su orden de salida"""
        return " -> ".join(str(item) for item in self.recorrer()) or "(vacía)"


class ColaPrioridad:
    """Cinco subcolas FIFO enlazadas; operaciones O(1) para prioridades 1-5"""

    def __init__(self) -> None:
        # Tupla fija de cinco colas propias: ninguna lista nativa es contenedor base.
        self._niveles = (ColaSimple(), ColaSimple(), ColaSimple(),
                         ColaSimple(), ColaSimple())
        self._n = 0

    def enqueue(self, valor: Any, prioridad: Optional[int] = None) -> None:
        """Encola según rango 1-5 y respeta FIFO entre iguales"""
        p = valor.prioridad if prioridad is None else prioridad
        if type(p) is not int or not 1 <= p <= 5:
            raise ValueError("La prioridad debe ser un entero entre 1 y 5")
        self._niveles[p - 1].enqueue(valor)
        self._n += 1

    def _primer_nivel(self) -> ColaSimple:
        for indice in range(4, -1, -1):
            if not self._niveles[indice].is_empty():
                return self._niveles[indice]
        raise IndexError("Cola de prioridad vacía (underflow)")

    def dequeue(self) -> Any:
        """Retira el elemento del nivel más alto no vacío"""
        valor = self._primer_nivel().dequeue()
        self._n -= 1
        return valor

    def front(self) -> Any:
        """Consulta el siguiente elemento crítico"""
        return self._primer_nivel().front()

    def is_empty(self) -> bool:
        """Indica si no hay estudiantes prioritarios pendientes"""
        return self._n == 0

    def size(self) -> int:
        """Cuenta los turnos prioritarios"""
        return self._n

    def recorrer(self) -> Iterator[Any]:
        """Entrega prioridades de 5 a 1, y FIFO dentro de cada nivel"""
        for indice in range(4, -1, -1):
            yield from self._niveles[indice].recorrer()

    def mostrar(self) -> str:
        """Representa la prioridad y los nombres de los estudiantes"""
        return " -> ".join(str(item) for item in self.recorrer()) or "(vacía)"


class ListaSimple:
    """Lista simplemente enlazada para inscritos y materias"""

    def __init__(self) -> None:
        self._inicio = None
        self._fin = None
        self._n = 0

    def insertar(self, valor: Any) -> None:
        """Inserta al final en O(1)"""
        nodo = NodoSimple(valor)
        if self._fin is None:
            self._inicio = nodo
        else:
            self._fin.siguiente = nodo
        self._fin = nodo
        self._n += 1

    def buscar(self, clave: Any, extractor: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Devuelve el primer valor cuya clave coincide; O(n)"""
        for valor in self.recorrer():
            if extractor(valor) == clave:
                return valor
        return None

    def eliminar(self, clave: Any, extractor: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Elimina el primer valor coincidente; O(n)"""
        anterior = None
        actual = self._inicio
        while actual is not None:
            if extractor(actual.valor) == clave:
                if anterior is None:
                    self._inicio = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                if actual is self._fin:
                    self._fin = anterior
                self._n -= 1
                return actual.valor
            anterior, actual = actual, actual.siguiente
        return None

    def recorrer(self) -> Iterator[Any]:
        """Itera desde la cabeza hasta el final"""
        actual = self._inicio
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    def size(self) -> int:
        """Cuenta sus elementos"""
        return self._n

    def is_empty(self) -> bool:
        """Indica si no hay nodos"""
        return self._n == 0


class ListaDoble:
    """Lista doble ordenada de menor a mayor por clave (año, término)"""

    def __init__(self) -> None:
        self._inicio = None
        self._fin = None
        self._n = 0

    def insertar_ordenado(self, valor: Any, clave: Callable[[Any], Any]) -> None:
        """Inserta un elemento en su posición ascendente; O(n)"""
        k = clave(valor)
        if self.buscar(k, clave) is not None:
            raise ValueError("Ya existe un semestre con ese año y término")
        nuevo = NodoDoble(valor)
        actual = self._inicio
        while actual is not None and clave(actual.valor) < k:
            actual = actual.siguiente
        if actual is None:
            nuevo.anterior = self._fin
            if self._fin is None:
                self._inicio = nuevo
            else:
                self._fin.siguiente = nuevo
            self._fin = nuevo
        else:
            nuevo.siguiente = actual
            nuevo.anterior = actual.anterior
            if actual.anterior is None:
                self._inicio = nuevo
            else:
                actual.anterior.siguiente = nuevo
            actual.anterior = nuevo
        self._n += 1

    def agregar_final(self, valor: Any, clave: Callable[[Any], Any] = lambda x: x) -> None:
        """Agrega en O(1) cuando la nueva clave supera la última"""
        if self._fin is not None and not clave(self._fin.valor) < clave(valor):
            raise ValueError("La clave debe ser estrictamente creciente")
        nodo = NodoDoble(valor, anterior=self._fin)
        if self._fin is None:
            self._inicio = nodo
        else:
            self._fin.siguiente = nodo
        self._fin = nodo
        self._n += 1

    def buscar(self, objetivo: Any, clave: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Busca por una clave recorriendo hacia delante; O(n)"""
        for valor in self.recorrer_adelante():
            if clave(valor) == objetivo:
                return valor
        return None

    def eliminar(self, objetivo: Any, clave: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Retira el elemento de clave dada y repara ambos enlaces"""
        actual = self._inicio
        while actual is not None:
            if clave(actual.valor) == objetivo:
                if actual.anterior is None:
                    self._inicio = actual.siguiente
                else:
                    actual.anterior.siguiente = actual.siguiente
                if actual.siguiente is None:
                    self._fin = actual.anterior
                else:
                    actual.siguiente.anterior = actual.anterior
                self._n -= 1
                return actual.valor
            actual = actual.siguiente
        return None

    def recorrer_adelante(self) -> Iterator[Any]:
        """Itera en orden cronológico ascendente"""
        actual = self._inicio
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    def recorrer_atras(self) -> Iterator[Any]:
        """Itera en orden cronológico descendente"""
        actual = self._fin
        while actual is not None:
            yield actual.valor
            actual = actual.anterior

    def size(self) -> int:
        """Cuenta sus nodos"""
        return self._n

    def is_empty(self) -> bool:
        """Indica si no existen semestres"""
        return self._n == 0
