"""Exportación e importación CSV/JSON con validación previa y reconstrucción"""

import csv
import json
from pathlib import Path
from .sistema import SIGA


COLUMNAS = ("id", "nombre", "correo", "cod_curso", "prioridad")


def exportar(sistema: SIGA, directorio: str | Path = "data") -> list[Path]:
    """Guarda estudiantes inscritos en CSV e historial/colas en JSON"""
    carpeta = Path(directorio)
    carpeta.mkdir(parents=True, exist_ok=True)
    estado = sistema.a_dict()
    ruta_csv = carpeta / "inscritos.csv"
    ruta_historial = carpeta / "historial.json"
    ruta_esperas = carpeta / "esperas.json"

    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for est in estado["inscritos"]:
            escritor.writerow({"id": est["id"], "nombre": est["nombre"],
                               "correo": est["correo"], "cod_curso": estado["curso"],
                               "prioridad": est["prioridad"] if est["prioridad"] is not None else ""})

    with ruta_historial.open("w", encoding="utf-8") as archivo:
        json.dump({"historiales": estado["historiales"]}, archivo,
                  ensure_ascii=False, indent=2)

    esperas = {clave: estado[clave] for clave in ("curso", "cupos", "simple", "circular", "prioridad")}
    with ruta_esperas.open("w", encoding="utf-8") as archivo:
        json.dump(esperas, archivo, ensure_ascii=False, indent=2)
    return [ruta_csv, ruta_historial, ruta_esperas]


def importar(sistema: SIGA, directorio: str | Path = "data") -> str:
    """Valida tres archivos antes de cambiar cualquier dato en memoria"""
    carpeta = Path(directorio)
    try:
        with (carpeta / "esperas.json").open(encoding="utf-8") as archivo:
            esperas = json.load(archivo)
        with (carpeta / "historial.json").open(encoding="utf-8") as archivo:
            historial = json.load(archivo)
        with (carpeta / "inscritos.csv").open(encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            if lector.fieldnames is None or not set(COLUMNAS).issubset(lector.fieldnames):
                raise ValueError("CSV: faltan columnas obligatorias")
            inscritos = []  # Registros temporales de intercambio CSV, no lista base.
            for fila in lector:
                if None in fila:
                    raise ValueError("CSV: fila con columnas sobrantes")
                if fila["cod_curso"] != esperas["curso"]:
                    raise ValueError("CSV: código de curso distinto al de esperas.json")
                prioridad = int(fila["prioridad"]) if fila["prioridad"] else None
                inscritos.append({"id": fila["id"], "nombre": fila["nombre"],
                                  "correo": fila["correo"], "prioridad": prioridad})
        if not isinstance(esperas, dict) or not isinstance(historial, dict):
            raise ValueError("La raíz JSON debe ser un objeto")
        datos = {
            "curso": esperas["curso"], "cupos": esperas["cupos"],
            "inscritos": inscritos, "simple": esperas["simple"],
            "circular": esperas["circular"], "prioridad": esperas["prioridad"],
            "historiales": historial["historiales"],
        }
        # SIGA.desde_dict valida todas las referencias y límites.
        return sistema.importar_estado(datos)
    except (OSError, KeyError, ValueError, TypeError, csv.Error, json.JSONDecodeError) as error:
        raise ValueError(f"No se pudo importar; estado original intacto: {error}") from error
