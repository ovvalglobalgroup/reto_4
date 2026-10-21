# Estructuras enlazadas usadas por el sistema académico
"""Implementaciones propias de estructuras enlazadas (sin list/deque como base)"""

from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional


# Nodo con enlace al siguiente elemento
@dataclass
class NodoSimple:
    """Almacena un elemento y la referencia al siguiente nodo"""
    valor: Any
    siguiente: Optional["NodoSimple"] = None


# Nodo con enlaces hacia ambos lados
@dataclass
class NodoDoble:
    """Almacena un elemento y las referencias de una lista doble"""
    valor: Any
    anterior: Optional["NodoDoble"] = None
    siguiente: Optional["NodoDoble"] = None


# Pila para recuperar la última acción realizada
class Pila:
    """Implementa una pila LIFO con inserción y extracción O(1)"""

    # Empieza con una pila vacía
    def __init__(self) -> None:
        self._cima = None
        self._n = 0

    # Coloca un elemento en la parte superior
    def push(self, valor: Any) -> None:
        """Agrega el valor a la cima"""
        self._cima = NodoSimple(valor, self._cima)
        self._n += 1

    # Saca el último elemento guardado
    def pop(self) -> Any:
        """Extrae la cima; lanza IndexError si está vacía"""
        # No se puede retirar un elemento de una pila vacía
        if self.is_empty():
            raise IndexError("Pila vacía (underflow)")
        valor = self._cima.valor
        # El siguiente nodo pasa a ser la nueva cima
        self._cima = self._cima.siguiente
        self._n -= 1
        return valor

    # Mira el último elemento sin quitarlo
    def peek(self) -> Any:
        """Consulta la cima sin eliminarla"""
        if self.is_empty():
            raise IndexError("Pila vacía (underflow)")
        return self._cima.valor

    # Comprueba si la pila está vacía
    def is_empty(self) -> bool:
        """Indica si no hay elementos"""
        return self._n == 0

    # Devuelve el total de elementos de la pila
    def size(self) -> int:
        """Obtiene la cantidad de elementos"""
        return self._n


# Cola que atiende según el orden de llegada
class ColaSimple:
    """Cola FIFO enlazada con extremos; enqueue y dequeue O(1)"""

    # Inicializa los extremos de la cola
    def __init__(self) -> None:
        self._inicio = None
        self._fin = None
        self._n = 0

    # Agrega un turno al final de la cola
    def enqueue(self, valor: Any) -> None:
        """Inserta al final de la cola"""
        nodo = NodoSimple(valor)
        # Si no hay nodos este también será el primero
        if self._fin is None:
            self._inicio = nodo
        else:
            self._fin.siguiente = nodo
        self._fin = nodo
        self._n += 1

    # Atiende y retira el primer turno
    def dequeue(self) -> Any:
        """Retira el primero; informa underflow mediante IndexError"""
        # Evita retirar elementos cuando la cola está vacía
        if self.is_empty():
            raise IndexError("Cola simple vacía (underflow)")
        valor = self._inicio.valor
        self._inicio = self._inicio.siguiente
        self._n -= 1
        # Si se retiró el último nodo también se limpia el final
        if self._inicio is None:
            self._fin = None
        return valor

    # Consulta el primer turno pendiente
    def front(self) -> Any:
        """Consulta el primer elemento"""
        if self.is_empty():
            raise IndexError("Cola simple vacía (underflow)")
        return self._inicio.valor

    # Comprueba si quedan turnos pendientes
    def is_empty(self) -> bool:
        """Indica si no hay turnos"""
        return self._n == 0

    # Cuenta los turnos de la cola
    def size(self) -> int:
        """Cuenta los turnos pendientes"""
        return self._n

    # Lee cada turno sin retirarlo
    def recorrer(self) -> Iterator[Any]:
        """Itera sin transformar la cola en una lista"""
        actual = self._inicio
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    # Presenta el orden de la cola en pantalla
    def mostrar(self) -> str:
        """Devuelve una vista legible del orden FIFO"""
        return " -> ".join(str(item) for item in self.recorrer()) or "(vacía)"


# Cola de espera con enlaces circulares
class ColaCircular:
    """Lista circular simple para espera FIFO y reasignación O(1)"""

    # Prepara la espera circular vacía
    def __init__(self) -> None:
        self._ultimo = None
        self._n = 0

    # Añade un turno y mantiene el círculo cerrado
    def enqueue(self, valor: Any) -> None:
        """Agrega un nodo conservando el enlace circular"""
        nodo = NodoSimple(valor)
        # El primer nodo se enlaza consigo mismo
        if self._ultimo is None:
            nodo.siguiente = nodo
            self._ultimo = nodo
        else:
            # Los siguientes nodos se unen sin romper el círculo
            nodo.siguiente = self._ultimo.siguiente
            self._ultimo.siguiente = nodo
            self._ultimo = nodo
        self._n += 1

    # Retira al estudiante que llegó primero
    def dequeue(self) -> Any:
        """Retira el nodo más antiguo"""
        if self.is_empty():
            raise IndexError("Cola circular vacía (underflow)")
        primero = self._ultimo.siguiente
        valor = primero.valor
        # Cuando solo queda un nodo la cola se vacía
        if self._n == 1:
            self._ultimo = None
        else:
            # El último nodo vuelve a apuntar al primero
            self._ultimo.siguiente = primero.siguiente
        self._n -= 1
        return valor

    # Mira quién sigue en la espera
    def front(self) -> Any:
        """Consulta el primero sin retirarlo"""
        if self.is_empty():
            raise IndexError("Cola circular vacía (underflow)")
        return self._ultimo.siguiente.valor

    # Verifica si hay estudiantes en espera
    def is_empty(self) -> bool:
        """Indica si la espera está vacía"""
        return self._n == 0

    # Cuenta los estudiantes en espera
    def size(self) -> int:
        """Cuenta los elementos de la cola circular"""
        return self._n

    # Recorre la cola una sola vuelta
    def recorrer(self) -> Iterator[Any]:
        """Recorre exactamente n nodos para evitar ciclos infinitos"""
        if self._ultimo is not None:
            actual = self._ultimo.siguiente
            # El número de nodos evita un recorrido infinito
            for _ in range(self._n):
                yield actual.valor
                actual = actual.siguiente

    # Muestra a los estudiantes en espera
    def mostrar(self) -> str:
        """Representa la espera en su orden de salida"""
        return " -> ".join(str(item) for item in self.recorrer()) or "(vacía)"


# Colas separadas según el nivel de prioridad
class ColaPrioridad:
    """Cinco subcolas FIFO enlazadas; operaciones O(1) para prioridades 1-5"""

    # Prepara las cinco colas de prioridad
    def __init__(self) -> None:
        # Se usan cinco colas propias en vez de una lista convencional
        self._niveles = (ColaSimple(), ColaSimple(), ColaSimple(),
                         ColaSimple(), ColaSimple())
        self._n = 0

    # Envía el turno al nivel que le corresponde
    def enqueue(self, valor: Any, prioridad: Optional[int] = None) -> None:
        """Encola según rango 1-5 y respeta FIFO entre iguales"""
        # Se usa la prioridad del estudiante salvo que se indique otra
        p = valor.prioridad if prioridad is None else prioridad
        if type(p) is not int or not 1 <= p <= 5:
            raise ValueError("La prioridad debe ser un entero entre 1 y 5")
        # Cada prioridad tiene su propia cola de llegada
        self._niveles[p - 1].enqueue(valor)
        self._n += 1

    # Encuentra el nivel más urgente con turnos
    def _primer_nivel(self) -> ColaSimple:
        # Se empieza siempre por la prioridad cinco
        for indice in range(4, -1, -1):
            if not self._niveles[indice].is_empty():
                return self._niveles[indice]
        raise IndexError("Cola de prioridad vacía (underflow)")

    # Atiende primero la prioridad más alta
    def dequeue(self) -> Any:
        """Retira el elemento del nivel más alto no vacío"""
        valor = self._primer_nivel().dequeue()
        self._n -= 1
        return valor

    # Consulta al próximo estudiante prioritario
    def front(self) -> Any:
        """Consulta el siguiente elemento crítico"""
        return self._primer_nivel().front()

    # Revisa si hay turnos prioritarios
    def is_empty(self) -> bool:
        """Indica si no hay estudiantes prioritarios pendientes"""
        return self._n == 0

    # Cuenta los turnos prioritarios
    def size(self) -> int:
        """Cuenta los turnos prioritarios"""
        return self._n

    # Lee los turnos de mayor a menor prioridad
    def recorrer(self) -> Iterator[Any]:
        """Entrega prioridades de 5 a 1, y FIFO dentro de cada nivel"""
        # Se respetan los niveles del cinco al uno
        for indice in range(4, -1, -1):
            yield from self._niveles[indice].recorrer()

    # Muestra el orden de atención prioritario
    def mostrar(self) -> str:
        """Representa la prioridad y los nombres de los estudiantes"""
        return " -> ".join(str(item) for item in self.recorrer()) or "(vacía)"


# Lista enlazada usada para estudiantes y materias
class ListaSimple:
    """Lista simplemente enlazada para inscritos y materias"""

    # Crea una lista inicialmente vacía
    def __init__(self) -> None:
        self._inicio = None
        self._fin = None
        self._n = 0

    # Añade un nuevo nodo al final
    def insertar(self, valor: Any) -> None:
        """Inserta al final en O(1)"""
        nodo = NodoSimple(valor)
        # Si es el primer elemento también queda al inicio
        if self._fin is None:
            self._inicio = nodo
        else:
            self._fin.siguiente = nodo
        self._fin = nodo
        self._n += 1

    # Busca el primer elemento que coincida
    def buscar(self, clave: Any, extractor: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Devuelve el primer valor cuya clave coincide; O(n)"""
        # Recorre los nodos hasta encontrar la clave
        for valor in self.recorrer():
            if extractor(valor) == clave:
                return valor
        return None

    # Quita el primer elemento que coincida
    def eliminar(self, clave: Any, extractor: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Elimina el primer valor coincidente; O(n)"""
        anterior = None
        actual = self._inicio
        # Busca el nodo y conserva la referencia al anterior
        while actual is not None:
            if extractor(actual.valor) == clave:
                # Si está al inicio se mueve la cabeza de la lista
                if anterior is None:
                    self._inicio = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                # También se actualiza el final si era el último
                if actual is self._fin:
                    self._fin = anterior
                self._n -= 1
                return actual.valor
            anterior, actual = actual, actual.siguiente
        return None

    # Lee la lista desde su primer nodo
    def recorrer(self) -> Iterator[Any]:
        """Itera desde la cabeza hasta el final"""
        actual = self._inicio
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    # Devuelve el tamaño de la lista
    def size(self) -> int:
        """Cuenta sus elementos"""
        return self._n

    # Verifica si la lista está vacía
    def is_empty(self) -> bool:
        """Indica si no hay nodos"""
        return self._n == 0


# Lista con recorridos en ambas direcciones
class ListaDoble:
    """Lista doble ordenada de menor a mayor por clave (año, término)"""

    # Prepara una lista con dos extremos
    def __init__(self) -> None:
        self._inicio = None
        self._fin = None
        self._n = 0

    # Ubica el nuevo elemento según su clave
    def insertar_ordenado(self, valor: Any, clave: Callable[[Any], Any]) -> None:
        """Inserta un elemento en su posición ascendente; O(n)"""
        k = clave(valor)
        # Evita insertar dos elementos con la misma clave
        if self.buscar(k, clave) is not None:
            raise ValueError("Ya existe un semestre con ese año y término")
        nuevo = NodoDoble(valor)
        actual = self._inicio
        # Busca el lugar que respeta el orden ascendente
        while actual is not None and clave(actual.valor) < k:
            actual = actual.siguiente
        # Si llegó al final se añade después del último
        if actual is None:
            nuevo.anterior = self._fin
            if self._fin is None:
                self._inicio = nuevo
            else:
                self._fin.siguiente = nuevo
            self._fin = nuevo
        else:
            # Si hay un siguiente se ajustan los dos enlaces
            nuevo.siguiente = actual
            nuevo.anterior = actual.anterior
            if actual.anterior is None:
                self._inicio = nuevo
            else:
                actual.anterior.siguiente = nuevo
            actual.anterior = nuevo
        self._n += 1

    # Agrega un elemento al final de la lista
    def agregar_final(self, valor: Any, clave: Callable[[Any], Any] = lambda x: x) -> None:
        """Agrega en O(1) cuando la nueva clave supera la última"""
        # Solo se aceptan claves mayores que la última
        if self._fin is not None and not clave(self._fin.valor) < clave(valor):
            raise ValueError("La clave debe ser estrictamente creciente")
        nodo = NodoDoble(valor, anterior=self._fin)
        if self._fin is None:
            self._inicio = nodo
        else:
            self._fin.siguiente = nodo
        self._fin = nodo
        self._n += 1

    # Busca un elemento por su clave
    def buscar(self, objetivo: Any, clave: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Busca por una clave recorriendo hacia delante; O(n)"""
        for valor in self.recorrer_adelante():
            if clave(valor) == objetivo:
                return valor
        return None

    # Retira un nodo y reconecta sus vecinos
    def eliminar(self, objetivo: Any, clave: Callable[[Any], Any] = lambda x: x) -> Optional[Any]:
        """Retira el elemento de clave dada y repara ambos enlaces"""
        actual = self._inicio
        while actual is not None:
            if clave(actual.valor) == objetivo:
                # Si era el primero se mueve el inicio
                if actual.anterior is None:
                    self._inicio = actual.siguiente
                else:
                    actual.anterior.siguiente = actual.siguiente
                # Si era el último se mueve el final
                if actual.siguiente is None:
                    self._fin = actual.anterior
                else:
                    actual.siguiente.anterior = actual.anterior
                self._n -= 1
                return actual.valor
            actual = actual.siguiente
        return None

    # Recorre los nodos del primero al último
    def recorrer_adelante(self) -> Iterator[Any]:
        """Itera en orden cronológico ascendente"""
        actual = self._inicio
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    # Recorre los nodos del último al primero
    def recorrer_atras(self) -> Iterator[Any]:
        """Itera en orden cronológico descendente"""
        actual = self._fin
        while actual is not None:
            yield actual.valor
            actual = actual.anterior

    # Cuenta los nodos de la lista doble
    def size(self) -> int:
        """Cuenta sus nodos"""
        return self._n

    # Comprueba si faltan elementos
    def is_empty(self) -> bool:
        """Indica si no existen semestres"""
        return self._n == 0
