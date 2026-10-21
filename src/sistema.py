# Aquí se coordina la inscripción y el historial de cada estudiante
"""Coordina inscripciones, historial y reversión transaccional mediante pila"""

from dataclasses import dataclass
from typing import Optional
from .estructuras import Pila, ColaSimple, ColaCircular, ColaPrioridad, ListaSimple, ListaDoble
from .modelos import Estudiante, Semestre


# Respaldo de una operación para poder deshacerla
@dataclass
class RegistroAccion:
    """Guarda una instantánea previa y las acciones atómicas observadas"""
    nombre: str
    detalle: str
    estado_anterior: dict


# Lógica que conecta todas las partes del sistema
class SIGA:
    """Sistema académico de un curso con cuatro estructuras enlazadas"""

    # Crea las colas y prepara el curso
    def __init__(self, nombre_curso: str = "Programación II", cupos: int = 3) -> None:
        self.curso = ""
        self.cupos = 0
        # Se crean las estructuras que almacenan los turnos
        self.cola_simple = ColaSimple()
        self.cola_circular = ColaCircular()
        self.cola_prioridad = ColaPrioridad()
        self.inscritos = ListaSimple()
        # Cada estudiante tiene su historial por separado
        self.historiales: dict[str, ListaDoble] = {}
        self.acciones = Pila()
        self._establecer_curso(nombre_curso, cupos)

    # Revisa los datos antes de guardar el curso
    def _establecer_curso(self, nombre: str, cupos: int) -> None:
        # No se puede trabajar con un curso sin nombre
        if not str(nombre).strip():
            raise ValueError("El nombre del curso no puede estar vacío")
        # Los cupos deben ser un número entero válido
        if type(cupos) is not int or cupos < 0:
            raise ValueError("Los cupos deben ser un entero no negativo")
        self.curso = str(nombre).strip()
        self.cupos = cupos

    # Vacía las estructuras al cambiar de curso
    def _reiniciar_datos(self) -> None:
        self.cola_simple = ColaSimple()
        self.cola_circular = ColaCircular()
        self.cola_prioridad = ColaPrioridad()
        self.inscritos = ListaSimple()
        self.historiales = {}

    # Guarda una acción para poder deshacerla
    def _registrar(self, nombre: str, detalle: str, anterior: dict) -> None:
        self.acciones.push(RegistroAccion(nombre, detalle, anterior))

    # Actualiza el curso y guarda el estado anterior
    def configurar_curso(self, nombre: str, cupos: int) -> str:
        """Configura el curso; reinicia sus datos y permite deshacer"""
        # Se guarda el curso anterior para poder deshacer el cambio
        anterior = self.a_dict()
        self._establecer_curso(nombre, cupos)
        # El nuevo curso comienza sin inscripciones
        self._reiniciar_datos()
        self._registrar("CONFIGURAR", "Reiniciar las inscripciones e historial", anterior)
        return f"Curso '{self.curso}' configurado con {self.cupos} cupos"

    # Recorre inscritos y estudiantes en espera
    def _todos_los_estudiantes(self):
        yield from self.inscritos.recorrer()
        yield from self.cola_simple.recorrer()
        yield from self.cola_circular.recorrer()
        yield from self.cola_prioridad.recorrer()

    # Busca un ID en todas las estructuras
    def buscar_estudiante(self, estudiante_id: str) -> Optional[Estudiante]:
        """Localiza un estudiante sin crear contenedores alternativos"""
        clave = str(estudiante_id).strip()
        for estudiante in self._todos_los_estudiantes():
            if estudiante.id == clave:
                return estudiante
        return None

    # Registra una nueva solicitud de inscripción
    def llegada(self, estudiante_id: str, nombre: str, correo: str = "",
                prioridad: Optional[int] = None) -> str:
        """Agrega un turno normal o de prioridad, rechazando IDs repetidos"""
        estudiante = Estudiante(estudiante_id, nombre, correo, prioridad)
        # Un mismo ID solo puede existir una vez
        if self.buscar_estudiante(estudiante.id) is not None:
            raise ValueError(f"El estudiante {estudiante.id} ya existe")
        anterior = self.a_dict()
        # Sin prioridad especial se usa la cola simple
        if estudiante.prioridad is None:
            self.cola_simple.enqueue(estudiante)
            detalle = "ENVIAR_A_COLA_SIMPLE"
        else:
            # Los casos prioritarios van a su cola correspondiente
            self.cola_prioridad.enqueue(estudiante)
            detalle = "ENVIAR_A_PRIORIDAD"
        self._registrar("LLEGADA", detalle + ": " + estudiante.id, anterior)
        return f"Llegada registrada: {estudiante}"

    # Revisa si el curso aún tiene espacio
    def _hay_cupo(self) -> bool:
        return self.inscritos.size() < self.cupos

    # Atiende turnos siguiendo las reglas del curso
    def procesar_turnos(self, cantidad: int) -> list[str]:
        """Prioriza p=5; si hay saturación traslada normales a circular.

        Cuando no hay cupo, los prioritarios permanecen en prioridad
        y los turnos simples pasan a la espera circular. Se trata de
        una sola operación deshacible aunque procese varios turnos.
        """
        # Evita procesar cantidades negativas o inválidas
        if type(cantidad) is not int or cantidad < 0:
            raise ValueError("La cantidad de turnos debe ser un entero no negativo")
        # Se guarda el estado por si luego se necesita deshacer
        anterior = self.a_dict()
        mensajes = []  # Esta lista guarda mensajes y no reemplaza las colas
        for _ in range(cantidad):
            # Con cupos disponibles se atiende la siguiente solicitud
            if self._hay_cupo():
                # Los estudiantes prioritarios pasan primero
                if not self.cola_prioridad.is_empty():
                    est = self.cola_prioridad.dequeue()
                # Si no hay prioridad se atiende en orden de llegada
                elif not self.cola_simple.is_empty():
                    est = self.cola_simple.dequeue()
                else:
                    break
                self.inscritos.insertar(est)
                mensajes.append(f"INSCRIBIR: {est}")
            # Con el curso lleno los normales pasan a espera
            elif not self.cola_simple.is_empty():
                est = self.cola_simple.dequeue()
                self.cola_circular.enqueue(est)
                mensajes.append(f"ENVIAR_A_ESPERA: {est}")
            else:
                break
        # Solo se registra la acción cuando hubo cambios
        if mensajes:
            self._registrar("PROCESAR_TURNOS", " | ".join(mensajes), anterior)
        return mensajes

    # Retira un inscrito y cubre su lugar si es posible
    def retirar(self, estudiante_id: str) -> list[str]:
        """Retira a un inscrito y reasigna prioridad > circular > simple"""
        anterior = self.a_dict()
        # Solo se puede retirar a quien ya esté inscrito
        est = self.inscritos.eliminar(str(estudiante_id).strip(), lambda e: e.id)
        if est is None:
            raise ValueError("El ID no figura entre los inscritos")
        mensajes = [f"RETIRAR: {est}"]
        # Las vacantes se ofrecen primero a la cola prioritaria
        if not self.cola_prioridad.is_empty():
            nuevo = self.cola_prioridad.dequeue()
            origen = "Prioridad"
        # Después se atiende a quienes esperan en la cola circular
        elif not self.cola_circular.is_empty():
            nuevo = self.cola_circular.dequeue()
            origen = "Circular"
        # La cola simple se utiliza como última alternativa
        elif not self.cola_simple.is_empty():
            nuevo = self.cola_simple.dequeue()
            origen = "Simple"
        else:
            nuevo = None
        # Si se encontró reemplazo ocupa el cupo disponible
        if nuevo is not None:
            self.inscritos.insertar(nuevo)
            mensajes.append(f"REASIGNAR ({origen}): {nuevo}")
        self._registrar("RETIRAR", " | ".join(mensajes), anterior)
        return mensajes

    # Agrega un período al historial del estudiante
    def agregar_semestre(self, estudiante_id: str, anio: int, term: int) -> str:
        """Inserta un semestre cronológicamente en la lista doble"""
        clave = str(estudiante_id).strip()
        # El estudiante debe existir antes de crear su historial
        if self.buscar_estudiante(clave) is None and clave not in self.historiales:
            raise ValueError("El estudiante debe registrarse primero en el sistema")
        semestre = Semestre(anio, term)
        historial = self.historiales.get(clave)
        if historial is not None and historial.buscar(semestre.clave(), lambda s: s.clave()):
            raise ValueError("Ese semestre ya está registrado")
        anterior = self.a_dict()
        # Se crea la lista doble al agregar el primer semestre
        if historial is None:
            historial = ListaDoble()
            self.historiales[clave] = historial
        historial.insertar_ordenado(semestre, lambda s: s.clave())
        self._registrar("AGREGAR_SEMESTRE", f"{clave} - {anio}/{term}", anterior)
        return f"Semestre {anio}/{term} agregado a {clave}"

    # Guarda una nueva nota o actualiza la anterior
    def agregar_o_actualizar_nota(self, estudiante_id: str, anio: int, term: int,
                                 cod: str, nombre: str, nota: float) -> str:
        """Agrega o actualiza una nota con respaldo para deshacer"""
        clave = str(estudiante_id).strip()
        historial = self.historiales.get(clave)
        semestre = historial.buscar((anio, term), lambda s: s.clave()) if historial else None
        # Solo se pueden guardar notas en semestres existentes
        if semestre is None:
            raise ValueError("No existe el semestre solicitado")
        anterior = self.a_dict()
        # La materia se crea o actualiza según corresponda
        evento = semestre.poner_materia(cod, nombre, nota)
        self._registrar(evento, f"{clave}, {anio}/{term}, {cod}: {nota}", anterior)
        return f"{evento}: {cod} ({nota:.2f}/20)"

    # Encuentra un período académico específico
    def buscar_semestre(self, estudiante_id: str, anio: int, term: int) -> Optional[Semestre]:
        """Busca un período por clave (año, término)"""
        historial = self.historiales.get(str(estudiante_id).strip())
        return historial.buscar((anio, term), lambda s: s.clave()) if historial else None

    # Permite consultar el historial en ambos sentidos
    def recorrer_historial(self, estudiante_id: str, adelante: bool = True):
        """Obtiene el iterador de semestres en el sentido solicitado"""
        historial = self.historiales.get(str(estudiante_id).strip())
        # Sin historial se devuelve un recorrido vacío
        if historial is None:
            return iter(())
        return historial.recorrer_adelante() if adelante else historial.recorrer_atras()

    # Convierte el estado actual en datos guardables
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

    # Reconstruye el sistema a partir de datos guardados
    @classmethod
    def desde_dict(cls, datos: dict) -> "SIGA":
        """Valida y reconstruye todas las estructuras desde registros planos"""
        # Comprueba el formato general antes de reconstruir
        if not isinstance(datos, dict):
            raise ValueError("El estado principal debe ser un objeto JSON")
        curso = datos["curso"]
        cupos = datos["cupos"]
        sistema = cls(curso, cupos)
        # Se usa un conjunto temporal para detectar IDs repetidos
        ids = set()
        # Cada registro vuelve a su estructura de origen
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
                # Se rechazan estudiantes repetidos entre las colas
                if e.id in ids:
                    raise ValueError(f"ID duplicado entre estructuras: {e.id}")
                ids.add(e.id)
                if nombre_campo == "prioridad" and e.prioridad is None:
                    raise ValueError("No se admiten estudiantes sin prioridad en la cola prioritaria")
                if nombre_campo != "prioridad" and e.prioridad is not None:
                    # Los inscritos pueden conservar su prioridad original
                    if nombre_campo in ("simple", "circular"):
                        raise ValueError("La cola normal contiene un estudiante prioritario")
                if nombre_campo == "inscritos":
                    estructura.insertar(e)
                else:
                    estructura.enqueue(e)
        # Nunca deben quedar inscritos por encima del cupo
        if sistema.inscritos.size() > cupos:
            raise ValueError("La cantidad de inscritos supera los cupos")
        historiales = datos["historiales"]
        if not isinstance(historiales, list):
            raise ValueError("El historial debe ser un arreglo")
        # Los semestres también se reconstruyen por estudiante
        for elemento in historiales:
            if not isinstance(elemento, dict):
                raise ValueError("Entrada de historial inválida")
            ident = str(elemento["estudiante_id"]).strip()
            if not ident or ident in sistema.historiales:
                raise ValueError("ID de historial vacío o duplicado")
            # El historial permanece aunque se retire un estudiante
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
        # El sistema recuperado empieza con una pila nueva
        sistema.acciones = Pila()
        return sistema

    # Reemplaza las estructuras por las del respaldo
    def _restaurar(self, datos: dict) -> None:
        # Primero se reconstruye un estado completo y válido
        otro = self.desde_dict(datos)
        self.curso, self.cupos = otro.curso, otro.cupos
        self.inscritos = otro.inscritos
        self.cola_simple = otro.cola_simple
        self.cola_circular = otro.cola_circular
        self.cola_prioridad = otro.cola_prioridad
        self.historiales = otro.historiales
        # La pila de acciones se mantiene durante la restauración

    # Recupera los datos previos a la última operación
    def deshacer(self) -> str:
        """Restaura exactamente el estado anterior de la última transacción"""
        # No se puede deshacer si todavía no hay acciones
        if self.acciones.is_empty():
            raise IndexError("No hay acciones para deshacer")
        # Se recupera la última operación registrada
        accion = self.acciones.pop()
        self._restaurar(accion.estado_anterior)
        return f"DESHACER {accion.nombre}: {accion.detalle}"

    # Carga datos nuevos después de revisarlos
    def importar_estado(self, datos: dict) -> str:
        """Importa de modo atómico: primero valida, luego sustituye"""
        # Se conserva el estado actual por seguridad
        anterior = self.a_dict()
        # Los datos se validan antes de cambiar el sistema
        otro = self.desde_dict(datos)  # Si los datos son inválidos no se modifica el sistema
        self._restaurar(otro.a_dict())
        self._registrar("IMPORTAR", "Reconstruir inscritos, colas e historial", anterior)
        return "Importación correcta: estructuras reconstruidas y verificadas"

    # Verifica que los estudiantes no estén duplicados
    def validar_consistencia(self) -> bool:
        """Comprueba unicidad y respeto de la capacidad del curso"""
        ids = set()
        # El total de inscritos no puede superar los cupos
        if self.inscritos.size() > self.cupos:
            return False
        for est in self._todos_los_estudiantes():
            # Un estudiante no puede aparecer dos veces
            if est.id in ids:
                return False
            ids.add(est.id)
        return True  # Los historiales pueden ser de estudiantes retirados
