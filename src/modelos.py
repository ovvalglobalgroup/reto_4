# Aquí se definen los datos de estudiantes, materias y semestres
"""Entidades académicas y validaciones de dominio"""

from dataclasses import dataclass, field
from typing import Optional
from .estructuras import ListaSimple


# Datos básicos de cada estudiante
@dataclass
class Estudiante:
    """Representa un estudiante y su prioridad de atención opcional"""
    id: str
    nombre: str
    correo: str = ""
    prioridad: Optional[int] = None

    # Limpia los datos y comprueba que sean válidos
    def __post_init__(self) -> None:
        # Quita espacios sobrantes de los datos recibidos
        self.id = str(self.id).strip()
        self.nombre = str(self.nombre).strip()
        self.correo = str(self.correo).strip()
        # El ID y el nombre no pueden quedar vacíos
        if not self.id or not self.nombre:
            raise ValueError("El ID y el nombre son obligatorios")
        # La prioridad solo se valida cuando fue indicada
        if self.prioridad is not None:
            if type(self.prioridad) is not int or not 1 <= self.prioridad <= 5:
                raise ValueError("Prioridad opcional: entero del 1 al 5")

    # Prepara los datos para guardarlos
    def a_dict(self) -> dict:
        """Serializa sin exponer referencias de nodos"""
        return {"id": self.id, "nombre": self.nombre,
                "correo": self.correo, "prioridad": self.prioridad}

    # Recupera un estudiante desde sus datos guardados
    @classmethod
    def desde_dict(cls, datos: dict) -> "Estudiante":
        """Crea un estudiante desde un registro validado"""
        # Evita crear estudiantes desde datos incorrectos
        if not isinstance(datos, dict):
            raise ValueError("Registro de estudiante inválido")
        return cls(datos["id"], datos["nombre"], datos.get("correo", ""),
                   datos.get("prioridad"))

    # Arma el texto que aparece en la consola
    def __str__(self) -> str:
        tipo = f" [p={self.prioridad}]" if self.prioridad is not None else " [normal]"
        return f"{self.id} - {self.nombre}{tipo}"


# Materia con su nota correspondiente
@dataclass
class Materia:
    """Asocia código, nombre y calificación académica"""
    cod: str
    nombre: str
    nota: float

    # Revisa los datos de la materia y su calificación
    def __post_init__(self) -> None:
        self.cod = str(self.cod).strip()
        self.nombre = str(self.nombre).strip()
        # Los datos principales de la materia son obligatorios
        if not self.cod or not self.nombre:
            raise ValueError("Código y nombre de la materia son obligatorios")
        # No se aceptan valores lógicos como calificaciones
        if isinstance(self.nota, bool) or not isinstance(self.nota, (int, float)):
            raise ValueError("La nota debe ser numérica")
        # Se usa la escala de notas de cero a veinte
        if not 0 <= self.nota <= 20:
            raise ValueError("La nota debe estar entre 0 y 20 (escala asumida)")
        self.nota = float(self.nota)

    # Prepara la materia para exportarla
    def a_dict(self) -> dict:
        """Representa la materia como un objeto JSON"""
        return {"cod": self.cod, "nombre": self.nombre, "nota": self.nota}


# Conjunto de materias de un período académico
@dataclass
class Semestre:
    """Contiene un período académico y materias en una lista enlazada"""
    anio: int
    term: int
    materias: ListaSimple = field(default_factory=ListaSimple)

    # Comprueba el año y el término académico
    def __post_init__(self) -> None:
        # Comprueba el rango permitido para el año
        if type(self.anio) is not int or not 1900 <= self.anio <= 2200:
            raise ValueError("El año debe ser un entero entre 1900 y 2200")
        # Los términos admitidos van del uno al cuatro
        if type(self.term) is not int or not 1 <= self.term <= 4:
            raise ValueError("El término debe ser un entero entre 1 y 4")

    # Identifica el semestre para ordenarlo
    def clave(self) -> tuple:
        """Devuelve clave de clasificación ascendente"""
        return (self.anio, self.term)

    # Agrega una materia o cambia una nota existente
    def poner_materia(self, cod: str, nombre: str, nota: float) -> str:
        """Inserta o actualiza la materia identificada por su código"""
        nuevo = Materia(cod, nombre, nota)
        # Busca primero si la materia ya existe
        anterior = self.materias.buscar(nuevo.cod, lambda m: m.cod)
        # Si no existe se agrega como una materia nueva
        if anterior is None:
            self.materias.insertar(nuevo)
            return "AÑADIR_MATERIA"
        # Si ya existe se actualizan sus datos
        anterior.nombre = nuevo.nombre
        anterior.nota = nuevo.nota
        return "ACTUALIZAR_NOTA"

    # Reúne las materias para guardar el semestre
    def a_dict(self) -> dict:
        """Convierte las materias a una lista temporal para JSON"""
        return {"anio": self.anio, "term": self.term,
                "materias": [materia.a_dict() for materia in self.materias.recorrer()]}
