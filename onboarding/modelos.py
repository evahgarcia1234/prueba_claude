"""Modelos de datos del onboarding de farmacias."""

import unicodedata
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


def normalizar(texto: str) -> str:
    """Quita tildes, mayúsculas y espacios sobrantes para comparar textos escritos a mano."""
    descompuesto = unicodedata.normalize("NFD", texto.strip())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").lower()


class Estado(Enum):
    """Estados posibles del onboarding de una farmacia."""

    PENDIENTE_DOCUMENTACION = "pendiente documentacion"
    EN_REVISION = "en revision"
    SUBSANACION = "subsanacion"
    LIVE = "live"
    PARALIZADA = "paralizada"

    @classmethod
    def desde_texto(cls, texto: str) -> "Estado":
        """Acepta mayúsculas y tildes ("En revisión"). Lanza ValueError si no es válido."""
        return cls(normalizar(texto))


def estados_validos() -> str:
    """Lista de estados para mostrar en mensajes de error y ayuda."""
    return ", ".join(f'"{e.value}"' for e in Estado)


@dataclass
class Farmacia:
    nombre: str
    provincia: str
    responsable: str
    estado: Estado
    fecha_ultimo_contacto: date
    documentos_pendientes: list[str] = field(default_factory=list)
