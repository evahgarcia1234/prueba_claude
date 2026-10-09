"""Lectura y validación del CSV de farmacias exportado desde Excel."""

import csv
import io
from datetime import datetime
from pathlib import Path

from onboarding.modelos import Estado, Farmacia, estados_validos

COLUMNAS = (
    "nombre",
    "provincia",
    "responsable",
    "estado",
    "fecha_ultimo_contacto",
    "documentos_pendientes",
)
SEPARADOR = ";"
SEPARADOR_DOCUMENTOS = "|"
FORMATO_FECHA = "%d/%m/%Y"

# Excel en español guarda "CSV UTF-8" con BOM (utf-8-sig) y el "CSV" normal
# en Windows-1252. cp1252 va al final porque decodifica casi cualquier byte.
CODIFICACIONES = ("utf-8-sig", "cp1252")


class ErrorCSV(Exception):
    """El CSV no tiene el formato esperado."""


def leer_farmacias(ruta: str | Path) -> list[Farmacia]:
    texto = _leer_texto(Path(ruta))
    lector = csv.DictReader(io.StringIO(texto), delimiter=SEPARADOR)
    if lector.fieldnames is None:
        raise ErrorCSV("El CSV está vacío.")
    lector.fieldnames = [c.strip().lower() for c in lector.fieldnames]

    faltan = [c for c in COLUMNAS if c not in lector.fieldnames]
    if faltan:
        raise ErrorCSV(f"Faltan columnas en el CSV: {', '.join(faltan)}")

    farmacias = []
    # La fila 1 es la cabecera, así que los datos empiezan en la 2.
    for num_fila, fila in enumerate(lector, start=2):
        # Excel a veces deja filas finales vacías del tipo ";;;;;".
        if not any((fila.get(c) or "").strip() for c in COLUMNAS):
            continue
        farmacias.append(_parsear_fila(fila, num_fila))
    return farmacias


def _leer_texto(ruta: Path) -> str:
    datos = ruta.read_bytes()
    for codificacion in CODIFICACIONES:
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    raise ErrorCSV(f"No se pudo leer la codificación de {ruta}")


def _parsear_fila(fila: dict[str, str], num_fila: int) -> Farmacia:
    valores = {c: (fila.get(c) or "").strip() for c in COLUMNAS}
    return Farmacia(
        nombre=valores["nombre"],
        provincia=valores["provincia"],
        responsable=valores["responsable"],
        estado=_parsear_estado(valores["estado"], num_fila),
        fecha_ultimo_contacto=_parsear_fecha(valores["fecha_ultimo_contacto"], num_fila),
        documentos_pendientes=[
            d.strip()
            for d in valores["documentos_pendientes"].split(SEPARADOR_DOCUMENTOS)
            if d.strip()
        ],
    )


def _parsear_estado(valor: str, num_fila: int) -> Estado:
    try:
        return Estado.desde_texto(valor)
    except ValueError:
        raise ErrorCSV(
            f'Fila {num_fila}: estado "{valor}" no válido. '
            f"Valores posibles: {estados_validos()}"
        ) from None


def _parsear_fecha(valor: str, num_fila: int):
    try:
        return datetime.strptime(valor, FORMATO_FECHA).date()
    except ValueError:
        raise ErrorCSV(
            f'Fila {num_fila}: fecha "{valor}" no válida. Formato esperado: dd/mm/aaaa'
        ) from None
