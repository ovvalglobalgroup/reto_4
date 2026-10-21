"""Entidades académicas y validaciones de dominio"""

from dataclasses import dataclass, field
from typing import Optional
from .estructuras import ListaSimple


@dataclass
class Estudiante:
    """Representa un estudiante y su prioridad de atención opcional"""
    id: str
    nombre: str
    correo: str = ""
    prioridad: Optional[int] = None

    def __post_init__(self) -> None:
        self.id = str(self.id).strip()
        self.nombre = str(self.nombre).strip()
        self.correo = str(self.correo).strip()
        if not self.id or not self.nombre:
            raise ValueError("El ID y el nombre son obligatorios")
        if self.prioridad is not None:
            if type(self.prioridad) is not int or not 1 <= self.prioridad <= 5:
                raise ValueError("Prioridad opcional: entero del 1 al 5")

    def a_dict(self) -> dict:
        """Serializa sin exponer referencias de nodos"""
        return {"id": self.id, "nombre": self.nombre,
                "correo": self.correo, "prioridad": self.prioridad}

    @classmethod
    def desde_dict(cls, datos: dict) -> "Estudiante":
        """Crea un estudiante desde un registro validado"""
        if not isinstance(datos, dict):
            raise ValueError("Registro de estudiante inválido")
        return cls(datos["id"], datos["nombre"], datos.get("correo", ""),
                   datos.get("prioridad"))

    def __str__(self) -> str:
        tipo = f" [p={self.prioridad}]" if self.prioridad is not None else " [normal]"
        return f"{self.id} - {self.nombre}{tipo}"


@dataclass
class Materia:
    """Asocia código, nombre y calificación académica"""
    cod: str
    nombre: str
    nota: float

    def __post_init__(self) -> None:
        self.cod = str(self.cod).strip()
        self.nombre = str(self.nombre).strip()
        if not self.cod or not self.nombre:
            raise ValueError("Código y nombre de la materia son obligatorios")
        if isinstance(self.nota, bool) or not isinstance(self.nota, (int, float)):
            raise ValueError("La nota debe ser numérica")
        if not 0 <= self.nota <= 20:
            raise ValueError("La nota debe estar entre 0 y 20 (escala asumida)")
        self.nota = float(self.nota)

    def a_dict(self) -> dict:
        """Representa la materia como un objeto JSON"""
        return {"cod": self.cod, "nombre": self.nombre, "nota": self.nota}


@dataclass
class Semestre:
    """Contiene un período académico y materias en una lista enlazada"""
    anio: int
    term: int
    materias: ListaSimple = field(default_factory=ListaSimple)

    def __post_init__(self) -> None:
        if type(self.anio) is not int or not 1900 <= self.anio <= 2200:
            raise ValueError("El año debe ser un entero entre 1900 y 2200")
        if type(self.term) is not int or not 1 <= self.term <= 4:
            raise ValueError("El término debe ser un entero entre 1 y 4")

    def clave(self) -> tuple:
        """Devuelve clave de clasificación ascendente"""
        return (self.anio, self.term)

    def poner_materia(self, cod: str, nombre: str, nota: float) -> str:
        """Inserta o actualiza la materia identificada por su código"""
        nuevo = Materia(cod, nombre, nota)
        anterior = self.materias.buscar(nuevo.cod, lambda m: m.cod)
        if anterior is None:
            self.materias.insertar(nuevo)
            return "AÑADIR_MATERIA"
        anterior.nombre = nuevo.nombre
        anterior.nota = nuevo.nota
        return "ACTUALIZAR_NOTA"

    def a_dict(self) -> dict:
        """Convierte las materias a una lista temporal para JSON"""
        return {"anio": self.anio, "term": self.term,
                "materias": [materia.a_dict() for materia in self.materias.recorrer()]}
