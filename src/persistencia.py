# Guardado y recuperación de los datos del curso
"""Exportación e importación CSV/JSON con validación previa y reconstrucción"""

import csv
import json
from pathlib import Path
from .sistema import SIGA


COLUMNAS = ("id", "nombre", "correo", "cod_curso", "prioridad")


# Guarda inscritos, historiales y colas en archivos
def exportar(sistema: SIGA, directorio: str | Path = "data") -> list[Path]:
    """Guarda estudiantes inscritos en CSV e historial/colas en JSON"""
    carpeta = Path(directorio)
    # Se crea la carpeta si todavía no existe
    carpeta.mkdir(parents=True, exist_ok=True)
    estado = sistema.a_dict()
    ruta_csv = carpeta / "inscritos.csv"
    ruta_historial = carpeta / "historial.json"
    ruta_esperas = carpeta / "esperas.json"

    # El CSV contiene únicamente los estudiantes inscritos
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for est in estado["inscritos"]:
            escritor.writerow({"id": est["id"], "nombre": est["nombre"],
                               "correo": est["correo"], "cod_curso": estado["curso"],
                               "prioridad": est["prioridad"] if est["prioridad"] is not None else ""})

    # El historial académico se guarda como JSON
    with ruta_historial.open("w", encoding="utf-8") as archivo:
        json.dump({"historiales": estado["historiales"]}, archivo,
                  ensure_ascii=False, indent=2)

    # Las colas y los cupos se guardan en otro JSON
    esperas = {clave: estado[clave] for clave in ("curso", "cupos", "simple", "circular", "prioridad")}
    with ruta_esperas.open("w", encoding="utf-8") as archivo:
        json.dump(esperas, archivo, ensure_ascii=False, indent=2)
    return [ruta_csv, ruta_historial, ruta_esperas]


# Lee los archivos y restaura los datos del curso
def importar(sistema: SIGA, directorio: str | Path = "data") -> str:
    """Valida tres archivos antes de cambiar cualquier dato en memoria"""
    carpeta = Path(directorio)
    try:
        # Primero se leen las colas y la configuración del curso
        with (carpeta / "esperas.json").open(encoding="utf-8") as archivo:
            esperas = json.load(archivo)
        # Después se recupera el historial académico
        with (carpeta / "historial.json").open(encoding="utf-8") as archivo:
            historial = json.load(archivo)
        # El CSV devuelve los estudiantes inscritos
        with (carpeta / "inscritos.csv").open(encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            # La importación exige las columnas esperadas
            if lector.fieldnames is None or not set(COLUMNAS).issubset(lector.fieldnames):
                raise ValueError("CSV: faltan columnas obligatorias")
            inscritos = []  # Lista temporal usada únicamente para leer el CSV
            for fila in lector:
                if None in fila:
                    raise ValueError("CSV: fila con columnas sobrantes")
                # Se comprueba que los archivos pertenezcan al mismo curso
                if fila["cod_curso"] != esperas["curso"]:
                    raise ValueError("CSV: código de curso distinto al de esperas.json")
                prioridad = int(fila["prioridad"]) if fila["prioridad"] else None
                inscritos.append({"id": fila["id"], "nombre": fila["nombre"],
                                  "correo": fila["correo"], "prioridad": prioridad})
        if not isinstance(esperas, dict) or not isinstance(historial, dict):
            raise ValueError("La raíz JSON debe ser un objeto")
        # Se arma el estado completo antes de restaurarlo
        datos = {
            "curso": esperas["curso"], "cupos": esperas["cupos"],
            "inscritos": inscritos, "simple": esperas["simple"],
            "circular": esperas["circular"], "prioridad": esperas["prioridad"],
            "historiales": historial["historiales"],
        }
        # El sistema valida todas las estructuras antes de cargarlas
        # La reconstrucción se aplica solo después de validar
        return sistema.importar_estado(datos)
    # Un error deja intactos los datos que ya estaban cargados
    except (OSError, KeyError, ValueError, TypeError, csv.Error, json.JSONDecodeError) as error:
        raise ValueError(f"No se pudo importar; estado original intacto: {error}") from error
