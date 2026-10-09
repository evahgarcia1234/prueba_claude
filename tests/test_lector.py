from datetime import date

import pytest

from onboarding.lector import ErrorCSV, leer_farmacias
from onboarding.modelos import Estado

CABECERA = "nombre;provincia;responsable;estado;fecha_ultimo_contacto;documentos_pendientes\n"


def escribir_csv(tmp_path, filas, codificacion="utf-8-sig"):
    ruta = tmp_path / "farmacias.csv"
    ruta.write_text(CABECERA + "".join(filas), encoding=codificacion)
    return ruta


@pytest.mark.parametrize("codificacion", ["utf-8-sig", "cp1252"])
def test_lee_fila_con_codificaciones_de_excel(tmp_path, codificacion):
    ruta = escribir_csv(
        tmp_path,
        ["Farmacia Peña;Ávila;Lucía;subsanacion;05/03/2026;contrato|PNT\n"],
        codificacion,
    )

    [farmacia] = leer_farmacias(ruta)

    assert farmacia.nombre == "Farmacia Peña"
    assert farmacia.provincia == "Ávila"
    assert farmacia.estado is Estado.SUBSANACION
    assert farmacia.fecha_ultimo_contacto == date(2026, 3, 5)
    assert farmacia.documentos_pendientes == ["contrato", "PNT"]


def test_documentos_vacios_y_estado_con_tilde(tmp_path):
    ruta = escribir_csv(tmp_path, ["F1;Madrid;Ana;En Revisión;01/01/2026;\n"])

    [farmacia] = leer_farmacias(ruta)

    assert farmacia.estado is Estado.EN_REVISION
    assert farmacia.documentos_pendientes == []


def test_ignora_filas_vacias_de_excel(tmp_path):
    ruta = escribir_csv(tmp_path, ["F1;Madrid;Ana;live;01/01/2026;\n", ";;;;;\n"])

    assert len(leer_farmacias(ruta)) == 1


def test_estado_invalido_indica_la_fila(tmp_path):
    ruta = escribir_csv(tmp_path, ["F1;Madrid;Ana;cerrada;01/01/2026;\n"])

    with pytest.raises(ErrorCSV, match='Fila 2: estado "cerrada"'):
        leer_farmacias(ruta)


def test_fecha_invalida_indica_la_fila(tmp_path):
    ruta = escribir_csv(tmp_path, ["F1;Madrid;Ana;live;2026-01-01;\n"])

    with pytest.raises(ErrorCSV, match="Fila 2: fecha"):
        leer_farmacias(ruta)


def test_faltan_columnas(tmp_path):
    ruta = tmp_path / "farmacias.csv"
    ruta.write_text("nombre;provincia\nF1;Madrid\n", encoding="utf-8")

    with pytest.raises(ErrorCSV, match="Faltan columnas"):
        leer_farmacias(ruta)
