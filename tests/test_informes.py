from datetime import date

from onboarding.informes import (
    alertas_sin_contacto,
    documentos_pendientes_por_frecuencia,
    filtrar,
    resumen_por_estado,
)
from onboarding.modelos import Estado, Farmacia

HOY = date(2026, 10, 9)


def farmacia(
    estado=Estado.EN_REVISION,
    nombre="F",
    provincia="Madrid",
    responsable="Ana",
    fecha=date(2026, 1, 1),
    documentos=(),
):
    return Farmacia(nombre, provincia, responsable, estado, fecha, list(documentos))


def nombres(farmacias):
    return [f.nombre for f in farmacias]


def test_resumen_cuenta_por_estado_e_incluye_estados_vacios():
    farmacias = [farmacia(Estado.LIVE), farmacia(Estado.LIVE), farmacia(Estado.PARALIZADA)]

    resumen = resumen_por_estado(farmacias)

    assert resumen[Estado.LIVE] == 2
    assert resumen[Estado.PARALIZADA] == 1
    assert resumen[Estado.EN_REVISION] == 0
    assert list(resumen) == list(Estado)


# --- filtrar ---

FARMACIAS = [
    farmacia(Estado.LIVE, "A", "Ávila", "Lucía Pérez"),
    farmacia(Estado.SUBSANACION, "B", "Madrid", "Jorge Ruiz"),
    farmacia(Estado.LIVE, "C", "Madrid", "Lucía Pérez"),
]


def test_filtrar_sin_filtros_devuelve_todas():
    assert nombres(filtrar(FARMACIAS)) == ["A", "B", "C"]


def test_filtrar_por_estado():
    assert nombres(filtrar(FARMACIAS, estado=Estado.LIVE)) == ["A", "C"]


def test_filtrar_ignora_tildes_y_mayusculas_y_acepta_parte_del_texto():
    assert nombres(filtrar(FARMACIAS, provincia="AVILA")) == ["A"]
    assert nombres(filtrar(FARMACIAS, responsable="lucia")) == ["A", "C"]


def test_filtrar_combina_filtros():
    assert nombres(filtrar(FARMACIAS, provincia="madrid", responsable="lucía")) == ["C"]


def test_filtrar_sin_resultados():
    assert filtrar(FARMACIAS, estado=Estado.PARALIZADA) == []


# --- alertas_sin_contacto ---


def test_alertas_solo_mas_de_n_dias():
    farmacias = [
        farmacia(nombre="justo 15", fecha=date(2026, 9, 24)),
        farmacia(nombre="16 dias", fecha=date(2026, 9, 23)),
    ]

    assert nombres(alertas_sin_contacto(farmacias, 15, HOY)) == ["16 dias"]


def test_alertas_excluye_live_pero_no_paralizada():
    antigua = date(2026, 1, 1)
    farmacias = [
        farmacia(Estado.LIVE, "live", fecha=antigua),
        farmacia(Estado.PARALIZADA, "paralizada", fecha=antigua),
    ]

    assert nombres(alertas_sin_contacto(farmacias, 15, HOY)) == ["paralizada"]


def test_alertas_ordenadas_de_mas_antigua_a_mas_reciente():
    farmacias = [
        farmacia(nombre="agosto", fecha=date(2026, 8, 1)),
        farmacia(nombre="junio", fecha=date(2026, 6, 1)),
        farmacia(nombre="julio", fecha=date(2026, 7, 1)),
    ]

    assert nombres(alertas_sin_contacto(farmacias, 15, HOY)) == ["junio", "julio", "agosto"]


# --- documentos_pendientes_por_frecuencia ---


def test_documentos_cuenta_y_ordena_de_mas_a_menos():
    farmacias = [
        farmacia(documentos=["contrato", "PNT"]),
        farmacia(documentos=["PNT"]),
        farmacia(documentos=["PNT", "certificado", "contrato"]),
    ]

    assert documentos_pendientes_por_frecuencia(farmacias) == [
        ("PNT", 3),
        ("contrato", 2),
        ("certificado", 1),
    ]


def test_documentos_no_cuenta_live_pero_si_paralizada():
    farmacias = [
        farmacia(Estado.LIVE, documentos=["contrato"]),
        farmacia(Estado.PARALIZADA, documentos=["PNT"]),
    ]

    assert documentos_pendientes_por_frecuencia(farmacias) == [("PNT", 1)]


def test_documentos_repetido_en_una_farmacia_cuenta_una_vez():
    farmacias = [farmacia(documentos=["contrato", "contrato"])]

    assert documentos_pendientes_por_frecuencia(farmacias) == [("contrato", 1)]


def test_documentos_agrupa_mayusculas_y_tildes_con_el_primer_nombre_escrito():
    farmacias = [
        farmacia(documentos=["Título"]),
        farmacia(documentos=["titulo"]),
        farmacia(documentos=["TITULO"]),
    ]

    assert documentos_pendientes_por_frecuencia(farmacias) == [("Título", 3)]


def test_documentos_empate_en_orden_alfabetico():
    farmacias = [farmacia(documentos=["PNT", "contrato", "certificado"])]

    assert documentos_pendientes_por_frecuencia(farmacias) == [
        ("certificado", 1),
        ("contrato", 1),
        ("PNT", 1),
    ]


def test_documentos_sin_pendientes():
    farmacias = [farmacia(), farmacia(Estado.LIVE)]

    assert documentos_pendientes_por_frecuencia(farmacias) == []
