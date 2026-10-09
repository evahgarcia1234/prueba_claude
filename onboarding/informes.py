"""Informes de seguimiento sobre la lista de farmacias."""

from collections import Counter
from datetime import date

from onboarding.modelos import Estado, Farmacia, normalizar


def resumen_por_estado(farmacias: list[Farmacia]) -> dict[Estado, int]:
    """Número de farmacias en cada estado, incluidos los estados sin ninguna."""
    conteo = Counter(f.estado for f in farmacias)
    return {estado: conteo[estado] for estado in Estado}


def filtrar(
    farmacias: list[Farmacia],
    estado: Estado | None = None,
    provincia: str | None = None,
    responsable: str | None = None,
) -> list[Farmacia]:
    """Farmacias que cumplen todos los filtros indicados (los que son None no filtran).

    Provincia y responsable no distinguen mayúsculas ni tildes y aceptan parte
    del texto, así que "lucia" encuentra a "Lucía Pérez".
    """
    return [
        f
        for f in farmacias
        if (estado is None or f.estado is estado)
        and _contiene(f.provincia, provincia)
        and _contiene(f.responsable, responsable)
    ]


def dias_sin_contacto(farmacia: Farmacia, hoy: date) -> int:
    return (hoy - farmacia.fecha_ultimo_contacto).days


def alertas_sin_contacto(farmacias: list[Farmacia], dias: int, hoy: date) -> list[Farmacia]:
    """Farmacias que no están en live y llevan más de `dias` días sin contacto.

    Ordenadas de la que lleva más tiempo sin contacto a la que menos.
    """
    en_alerta = [
        f
        for f in farmacias
        if f.estado is not Estado.LIVE and dias_sin_contacto(f, hoy) > dias
    ]
    return sorted(en_alerta, key=lambda f: f.fecha_ultimo_contacto)


def farmacias_con_documentos_pendientes(farmacias: list[Farmacia]) -> list[Farmacia]:
    """Farmacias que no están en live y tienen algún documento pendiente."""
    return [
        f for f in farmacias if f.estado is not Estado.LIVE and f.documentos_pendientes
    ]


def documentos_pendientes_por_frecuencia(farmacias: list[Farmacia]) -> list[tuple[str, int]]:
    """Cuántas farmacias (sin contar las live) tienen pendiente cada documento.

    Ordenado de más a menos farmacias y, en caso de empate, alfabéticamente.
    No distingue mayúsculas ni tildes ("PNT" y "pnt" son el mismo documento);
    se muestra el nombre tal y como aparece escrito la primera vez.
    """
    conteo = Counter()
    nombre_mostrado: dict[str, str] = {}
    for f in farmacias_con_documentos_pendientes(farmacias):
        # Un set para que un documento repetido en la misma farmacia cuente una sola vez.
        claves = set()
        for documento in f.documentos_pendientes:
            clave = normalizar(documento)
            nombre_mostrado.setdefault(clave, documento)
            claves.add(clave)
        conteo.update(claves)
    ordenadas = sorted(conteo, key=lambda clave: (-conteo[clave], clave))
    return [(nombre_mostrado[clave], conteo[clave]) for clave in ordenadas]


def _contiene(valor: str, buscado: str | None) -> bool:
    return buscado is None or normalizar(buscado) in normalizar(valor)
