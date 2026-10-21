"""Coordina inscripciones, historial y reversión transaccional mediante pila"""

from dataclasses import dataclass
from typing import Optional
from .estructuras import Pila, ColaSimple, ColaCircular, ColaPrioridad, ListaSimple, ListaDoble
from .modelos import Estudiante, Semestre


@dataclass
class RegistroAccion:
    """Guarda una instantánea previa y las acciones atómicas observadas"""
    nombre: str
    detalle: str
    estado_anterior: dict


class SIGA:
    """Sistema académico de un curso con cuatro estructuras enlazadas"""

    def __init__(self, nombre_curso: str = "Programación II", cupos: int = 3) -> None:
        self.curso = ""
        self.cupos = 0
        self.cola_simple = ColaSimple()
        self.cola_circular = ColaCircular()
        self.cola_prioridad = ColaPrioridad()
        self.inscritos = ListaSimple()
        self.historiales: dict[str, ListaDoble] = {}
        self.acciones = Pila()
        self._establecer_curso(nombre_curso, cupos)

    def _establecer_curso(self, nombre: str, cupos: int) -> None:
        if not str(nombre).strip():
            raise ValueError("El nombre del curso no puede estar vacío")
        if type(cupos) is not int or cupos < 0:
            raise ValueError("Los cupos deben ser un entero no negativo")
        self.curso = str(nombre).strip()
        self.cupos = cupos

    def _reiniciar_datos(self) -> None:
        self.cola_simple = ColaSimple()
        self.cola_circular = ColaCircular()
        self.cola_prioridad = ColaPrioridad()
        self.inscritos = ListaSimple()
        self.historiales = {}

    def _registrar(self, nombre: str, detalle: str, anterior: dict) -> None:
        self.acciones.push(RegistroAccion(nombre, detalle, anterior))

    def configurar_curso(self, nombre: str, cupos: int) -> str:
        """Configura el curso; reinicia sus datos y permite deshacer"""
        anterior = self.a_dict()
        self._establecer_curso(nombre, cupos)
        self._reiniciar_datos()
        self._registrar("CONFIGURAR", "Reiniciar las inscripciones e historial", anterior)
        return f"Curso '{self.curso}' configurado con {self.cupos} cupos"

    def _todos_los_estudiantes(self):
        yield from self.inscritos.recorrer()
        yield from self.cola_simple.recorrer()
        yield from self.cola_circular.recorrer()
        yield from self.cola_prioridad.recorrer()

    def buscar_estudiante(self, estudiante_id: str) -> Optional[Estudiante]:
        """Localiza un estudiante sin crear contenedores alternativos"""
        clave = str(estudiante_id).strip()
        for estudiante in self._todos_los_estudiantes():
            if estudiante.id == clave:
                return estudiante
        return None

    def llegada(self, estudiante_id: str, nombre: str, correo: str = "",
                prioridad: Optional[int] = None) -> str:
        """Agrega un turno normal o de prioridad, rechazando IDs repetidos"""
        estudiante = Estudiante(estudiante_id, nombre, correo, prioridad)
        if self.buscar_estudiante(estudiante.id) is not None:
            raise ValueError(f"El estudiante {estudiante.id} ya existe")
        anterior = self.a_dict()
        if estudiante.prioridad is None:
            self.cola_simple.enqueue(estudiante)
            detalle = "ENVIAR_A_COLA_SIMPLE"
        else:
            self.cola_prioridad.enqueue(estudiante)
            detalle = "ENVIAR_A_PRIORIDAD"
        self._registrar("LLEGADA", detalle + ": " + estudiante.id, anterior)
        return f"Llegada registrada: {estudiante}"

    def _hay_cupo(self) -> bool:
        return self.inscritos.size() < self.cupos

    def procesar_turnos(self, cantidad: int) -> list[str]:
        """Prioriza p=5; si hay saturación traslada normales a circular.

        Cuando no hay cupo, los prioritarios permanecen en prioridad
        y los turnos simples pasan a la espera circular. Se trata de
        una sola operación deshacible aunque procese varios turnos.
        """
        if type(cantidad) is not int or cantidad < 0:
            raise ValueError("La cantidad de turnos debe ser un entero no negativo")
        anterior = self.a_dict()
        mensajes = []  # Solo resultados de salida, nunca estructura base.
        for _ in range(cantidad):
            if self._hay_cupo():
                if not self.cola_prioridad.is_empty():
                    est = self.cola_prioridad.dequeue()
                elif not self.cola_simple.is_empty():
                    est = self.cola_simple.dequeue()
                else:
                    break
                self.inscritos.insertar(est)
                mensajes.append(f"INSCRIBIR: {est}")
            elif not self.cola_simple.is_empty():
                est = self.cola_simple.dequeue()
                self.cola_circular.enqueue(est)
                mensajes.append(f"ENVIAR_A_ESPERA: {est}")
            else:
                break
        if mensajes:
            self._registrar("PROCESAR_TURNOS", " | ".join(mensajes), anterior)
        return mensajes

    def retirar(self, estudiante_id: str) -> list[str]:
        """Retira a un inscrito y reasigna prioridad > circular > simple"""
        anterior = self.a_dict()
        est = self.inscritos.eliminar(str(estudiante_id).strip(), lambda e: e.id)
        if est is None:
            raise ValueError("El ID no figura entre los inscritos")
        mensajes = [f"RETIRAR: {est}"]
        if not self.cola_prioridad.is_empty():
            nuevo = self.cola_prioridad.dequeue()
            origen = "Prioridad"
        elif not self.cola_circular.is_empty():
            nuevo = self.cola_circular.dequeue()
            origen = "Circular"
        elif not self.cola_simple.is_empty():
            nuevo = self.cola_simple.dequeue()
            origen = "Simple"
        else:
            nuevo = None
        if nuevo is not None:
            self.inscritos.insertar(nuevo)
            mensajes.append(f"REASIGNAR ({origen}): {nuevo}")
        self._registrar("RETIRAR", " | ".join(mensajes), anterior)
        return mensajes

    def agregar_semestre(self, estudiante_id: str, anio: int, term: int) -> str:
        """Inserta un semestre cronológicamente en la lista doble"""
        clave = str(estudiante_id).strip()
        if self.buscar_estudiante(clave) is None and clave not in self.historiales:
            raise ValueError("El estudiante debe registrarse primero en el sistema")
        semestre = Semestre(anio, term)
        historial = self.historiales.get(clave)
        if historial is not None and historial.buscar(semestre.clave(), lambda s: s.clave()):
            raise ValueError("Ese semestre ya está registrado")
        anterior = self.a_dict()
        if historial is None:
            historial = ListaDoble()
            self.historiales[clave] = historial
        historial.insertar_ordenado(semestre, lambda s: s.clave())
        self._registrar("AGREGAR_SEMESTRE", f"{clave} - {anio}/{term}", anterior)
        return f"Semestre {anio}/{term} agregado a {clave}"

    def agregar_o_actualizar_nota(self, estudiante_id: str, anio: int, term: int,
                                 cod: str, nombre: str, nota: float) -> str:
        """Agrega o actualiza una nota con respaldo para deshacer"""
        clave = str(estudiante_id).strip()
        historial = self.historiales.get(clave)
        semestre = historial.buscar((anio, term), lambda s: s.clave()) if historial else None
        if semestre is None:
            raise ValueError("No existe el semestre solicitado")
        anterior = self.a_dict()
        evento = semestre.poner_materia(cod, nombre, nota)
        self._registrar(evento, f"{clave}, {anio}/{term}, {cod}: {nota}", anterior)
        return f"{evento}: {cod} ({nota:.2f}/20)"

    def buscar_semestre(self, estudiante_id: str, anio: int, term: int) -> Optional[Semestre]:
        """Busca un período por clave (año, término)"""
        historial = self.historiales.get(str(estudiante_id).strip())
        return historial.buscar((anio, term), lambda s: s.clave()) if historial else None

    def recorrer_historial(self, estudiante_id: str, adelante: bool = True):
        """Obtiene el iterador de semestres en el sentido solicitado"""
        historial = self.historiales.get(str(estudiante_id).strip())
        if historial is None:
            return iter(())
        return historial.recorrer_adelante() if adelante else historial.recorrer_atras()

    def a_dict(self) -> dict:
        """Serializa los nodos a registros transitorios sin perder su orden"""
        return {
            "curso": self.curso, "cupos": self.cupos,
            "inscritos": [e.a_dict() for e in self.inscritos.recorrer()],
            "simple": [e.a_dict() for e in self.cola_simple.recorrer()],
            "circular": [e.a_dict() for e in self.cola_circular.recorrer()],
            "prioridad": [e.a_dict() for e in self.cola_prioridad.recorrer()],
            "historiales": [
                {"estudiante_id": ident, "semestres": [s.a_dict() for s in lista.recorrer_adelante()]}
                for ident, lista in sorted(self.historiales.items())
            ],
        }

    @classmethod
    def desde_dict(cls, datos: dict) -> "SIGA":
        """Valida y reconstruye todas las estructuras desde registros planos"""
        if not isinstance(datos, dict):
            raise ValueError("El estado principal debe ser un objeto JSON")
        curso = datos["curso"]
        cupos = datos["cupos"]
        sistema = cls(curso, cupos)
        ids = set()
        for nombre_campo, estructura in (
            ("inscritos", sistema.inscritos),
            ("simple", sistema.cola_simple),
            ("circular", sistema.cola_circular),
            ("prioridad", sistema.cola_prioridad),
        ):
            registros = datos[nombre_campo]
            if not isinstance(registros, list):
                raise ValueError(f"El campo {nombre_campo} debe ser un arreglo")
            for registro in registros:
                e = Estudiante.desde_dict(registro)
                if e.id in ids:
                    raise ValueError(f"ID duplicado entre estructuras: {e.id}")
                ids.add(e.id)
                if nombre_campo == "prioridad" and e.prioridad is None:
                    raise ValueError("No se admiten estudiantes sin prioridad en la cola prioritaria")
                if nombre_campo != "prioridad" and e.prioridad is not None:
                    # Un prioritario que fue inscrito conserva su prioridad.
                    if nombre_campo in ("simple", "circular"):
                        raise ValueError("La cola normal contiene un estudiante prioritario")
                if nombre_campo == "inscritos":
                    estructura.insertar(e)
                else:
                    estructura.enqueue(e)
        if sistema.inscritos.size() > cupos:
            raise ValueError("La cantidad de inscritos supera los cupos")
        historiales = datos["historiales"]
        if not isinstance(historiales, list):
            raise ValueError("El historial debe ser un arreglo")
        for elemento in historiales:
            if not isinstance(elemento, dict):
                raise ValueError("Entrada de historial inválida")
            ident = str(elemento["estudiante_id"]).strip()
            if not ident or ident in sistema.historiales:
                raise ValueError("ID de historial vacío o duplicado")
            # Se conserva el historial incluso después de que alguien se retire.
            lista = ListaDoble()
            semestres = elemento["semestres"]
            if not isinstance(semestres, list):
                raise ValueError("Los semestres deben ser un arreglo")
            for dato in semestres:
                sem = Semestre(dato["anio"], dato["term"])
                lista.insertar_ordenado(sem, lambda s: s.clave())
                materias = dato["materias"]
                if not isinstance(materias, list):
                    raise ValueError("Las materias deben ser un arreglo")
                for mat in materias:
                    if sem.materias.buscar(mat["cod"], lambda m: m.cod):
                        raise ValueError("Materia duplicada en un semestre")
                    sem.poner_materia(mat["cod"], mat["nombre"], mat["nota"])
            sistema.historiales[ident] = lista
        sistema.acciones = Pila()
        return sistema

    def _restaurar(self, datos: dict) -> None:
        otro = self.desde_dict(datos)
        self.curso, self.cupos = otro.curso, otro.cupos
        self.inscritos = otro.inscritos
        self.cola_simple = otro.cola_simple
        self.cola_circular = otro.cola_circular
        self.cola_prioridad = otro.cola_prioridad
        self.historiales = otro.historiales
        # La pila de acciones se conserva, salvo en la carga inicial.

    def deshacer(self) -> str:
        """Restaura exactamente el estado anterior de la última transacción"""
        if self.acciones.is_empty():
            raise IndexError("No hay acciones para deshacer")
        accion = self.acciones.pop()
        self._restaurar(accion.estado_anterior)
        return f"DESHACER {accion.nombre}: {accion.detalle}"

    def importar_estado(self, datos: dict) -> str:
        """Importa de modo atómico: primero valida, luego sustituye"""
        anterior = self.a_dict()
        otro = self.desde_dict(datos)  # Puede fallar sin modificar self.
        self._restaurar(otro.a_dict())
        self._registrar("IMPORTAR", "Reconstruir inscritos, colas e historial", anterior)
        return "Importación correcta: estructuras reconstruidas y verificadas"

    def validar_consistencia(self) -> bool:
        """Comprueba unicidad y respeto de la capacidad del curso"""
        ids = set()
        if self.inscritos.size() > self.cupos:
            return False
        for est in self._todos_los_estudiantes():
            if est.id in ids:
                return False
            ids.add(est.id)
        return True  # Los historiales también pueden pertenecer a retirados
