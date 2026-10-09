from datetime import date, timedelta

import pytest

from onboarding.cli import main

CABECERA = "nombre;provincia;responsable;estado;fecha_ultimo_contacto;documentos_pendientes\n"


def hace(dias):
    return (date.today() - timedelta(days=dias)).strftime("%d/%m/%Y")


@pytest.fixture
def csv_farmacias(tmp_path):
    # Fechas relativas a hoy para que el comando alertas dé siempre el mismo resultado.
    ruta = tmp_path / "farmacias.csv"
    ruta.write_text(
        CABECERA
        + f"Farmacia Castañeda;Madrid;Lucía Pérez;pendiente documentacion;{hace(30)};contrato|PNT\n"
        + f"Farmacia del Carmen;Sevilla;Jorge Ruiz;en revision;{hace(5)};\n"
        + f"Farmacia La Rambla;Barcelona;Lucía Pérez;live;{hace(60)};certificado\n"
        + f"Farmacia El Pilar;Zaragoza;Jorge Ruiz;paralizada;{hace(90)};contrato\n",
        encoding="utf-8-sig",
    )
    return str(ruta)


# --- listar ---


def test_listar_sin_filtros(csv_farmacias, capsys):
    assert main(["listar", csv_farmacias]) == 0

    salida = capsys.readouterr().out
    assert "Farmacia Castañeda" in salida
    assert "contrato, PNT" in salida
    assert "4 farmacias" in salida


def test_listar_con_filtros(csv_farmacias, capsys):
    main(["listar", csv_farmacias, "--responsable", "lucia", "--provincia", "madrid"])

    salida = capsys.readouterr().out
    assert "Farmacia Castañeda" in salida
    assert "La Rambla" not in salida
    assert "1 farmacia" in salida


def test_listar_estado_acepta_tildes_y_mayusculas(csv_farmacias, capsys):
    main(["listar", csv_farmacias, "--estado", "En Revisión"])

    salida = capsys.readouterr().out
    assert "Farmacia del Carmen" in salida
    assert "1 farmacia" in salida


def test_listar_sin_resultados(csv_farmacias, capsys):
    main(["listar", csv_farmacias, "--provincia", "Cuenca"])

    assert "No hay farmacias que cumplan los filtros." in capsys.readouterr().out


def test_listar_estado_invalido(csv_farmacias, capsys):
    with pytest.raises(SystemExit) as salida:
        main(["listar", csv_farmacias, "--estado", "cerrada"])

    assert salida.value.code != 0
    assert '"cerrada" no es un estado válido' in capsys.readouterr().err


# --- alertas ---


def test_alertas_por_defecto_15_dias(csv_farmacias, capsys):
    assert main(["alertas", csv_farmacias]) == 0

    salida = capsys.readouterr().out
    # La Rambla lleva 60 días pero está en live, así que no sale.
    assert "La Rambla" not in salida
    assert "Farmacia del Carmen" not in salida
    # La más antigua aparece primero.
    assert salida.index("El Pilar") < salida.index("Castañeda")
    assert "2 farmacias sin contacto desde hace más de 15 días" in salida


def test_alertas_con_dias(csv_farmacias, capsys):
    main(["alertas", csv_farmacias, "--dias", "60"])

    salida = capsys.readouterr().out
    assert "El Pilar" in salida
    assert "Castañeda" not in salida
    assert "1 farmacia sin contacto desde hace más de 60 días" in salida


def test_alertas_sin_resultados(csv_farmacias, capsys):
    main(["alertas", csv_farmacias, "--dias", "365"])

    assert "No hay farmacias sin contacto desde hace más de 365 días." in capsys.readouterr().out


@pytest.mark.parametrize("dias", ["-3", "diez", "1.5"])
def test_alertas_dias_invalidos(csv_farmacias, capsys, dias):
    with pytest.raises(SystemExit) as salida:
        main(["alertas", csv_farmacias, "--dias", dias])

    assert salida.value.code != 0
    assert "debe ser un número entero" in capsys.readouterr().err


# --- documentos ---


def test_documentos(csv_farmacias, capsys):
    assert main(["documentos", csv_farmacias]) == 0

    salida = capsys.readouterr().out
    lineas = salida.splitlines()
    assert lineas[0].split() == ["Documento", "Farmacias"]
    assert lineas[2].split() == ["contrato", "2"]
    assert lineas[3].split() == ["PNT", "1"]
    # El certificado solo lo tiene pendiente La Rambla, que está en live.
    assert "certificado" not in salida
    assert "2 farmacias con documentos pendientes" in salida


def test_documentos_sin_pendientes(tmp_path, capsys):
    ruta = tmp_path / "farmacias.csv"
    ruta.write_text(
        CABECERA
        + "F1;Madrid;Ana;en revision;01/10/2026;\n"
        + "F2;Madrid;Ana;live;01/10/2026;contrato\n",
        encoding="utf-8",
    )

    main(["documentos", str(ruta)])

    assert (
        "Ninguna farmacia fuera de live tiene documentos pendientes."
        in capsys.readouterr().out
    )
