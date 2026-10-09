"""Interfaz de línea de comandos."""

import argparse
import sys
from datetime import date

from onboarding.informes import (
    alertas_sin_contacto,
    dias_sin_contacto,
    documentos_pendientes_por_frecuencia,
    farmacias_con_documentos_pendientes,
    filtrar,
    resumen_por_estado,
)
from onboarding.lector import FORMATO_FECHA, ErrorCSV, leer_farmacias
from onboarding.modelos import Estado, Farmacia, estados_validos

DIAS_ALERTA_POR_DEFECTO = 15


def main(argv: list[str] | None = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)
    try:
        farmacias = leer_farmacias(args.csv)
    except FileNotFoundError:
        print(f"Error: no existe el archivo {args.csv}", file=sys.stderr)
        return 1
    except ErrorCSV as e:
        print(f"Error en {args.csv}: {e}", file=sys.stderr)
        return 1
    args.comando(farmacias, args)
    return 0


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="onboarding",
        description="Seguimiento del onboarding de farmacias.",
    )
    subparsers = parser.add_subparsers(required=True, metavar="comando")

    # Argumento común a todos los comandos.
    con_csv = argparse.ArgumentParser(add_help=False)
    con_csv.add_argument("csv", help="ruta al CSV de farmacias")

    resumen = subparsers.add_parser(
        "resumen", parents=[con_csv], help="cuenta las farmacias por estado"
    )
    resumen.set_defaults(comando=_comando_resumen)

    listar = subparsers.add_parser(
        "listar", parents=[con_csv], help="muestra las farmacias, con filtros opcionales"
    )
    listar.add_argument(
        "--estado", type=_tipo_estado, help=f"uno de: {estados_validos()}"
    )
    listar.add_argument(
        "--provincia", help="provincia (vale parte del nombre; ignora tildes y mayúsculas)"
    )
    listar.add_argument(
        "--responsable", help="responsable (vale parte del nombre; ignora tildes y mayúsculas)"
    )
    listar.set_defaults(comando=_comando_listar)

    alertas = subparsers.add_parser(
        "alertas",
        parents=[con_csv],
        help='farmacias que no están en "live" y llevan demasiado sin contacto',
    )
    alertas.add_argument(
        "--dias",
        type=_tipo_dias,
        default=DIAS_ALERTA_POR_DEFECTO,
        help=f"avisar si llevan más de estos días sin contacto (por defecto: {DIAS_ALERTA_POR_DEFECTO})",
    )
    alertas.set_defaults(comando=_comando_alertas)

    documentos = subparsers.add_parser(
        "documentos",
        parents=[con_csv],
        help='cuántas farmacias (sin contar las "live") tienen pendiente cada documento',
    )
    documentos.set_defaults(comando=_comando_documentos)

    return parser


def _tipo_estado(texto: str) -> Estado:
    try:
        return Estado.desde_texto(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f'"{texto}" no es un estado válido. Valores posibles: {estados_validos()}'
        ) from None


def _tipo_dias(texto: str) -> int:
    if not texto.isdigit():
        raise argparse.ArgumentTypeError(
            f'"{texto}" no es válido: debe ser un número entero de 0 en adelante'
        )
    return int(texto)


def _comando_resumen(farmacias: list[Farmacia], args: argparse.Namespace) -> None:
    resumen = resumen_por_estado(farmacias)
    ancho = max(len(e.value) for e in resumen)
    print(f"{'Estado':<{ancho}}  Farmacias")
    print("-" * (ancho + 11))
    for estado, total in resumen.items():
        print(f"{estado.value:<{ancho}}  {total:>9}")
    print("-" * (ancho + 11))
    print(f"{'Total':<{ancho}}  {len(farmacias):>9}")


def _comando_listar(farmacias: list[Farmacia], args: argparse.Namespace) -> None:
    seleccion = filtrar(farmacias, args.estado, args.provincia, args.responsable)
    if not seleccion:
        print("No hay farmacias que cumplan los filtros.")
        return
    _imprimir_tabla(
        ["Nombre", "Provincia", "Responsable", "Estado", "Último contacto", "Documentos pendientes"],
        [
            [
                f.nombre,
                f.provincia,
                f.responsable,
                f.estado.value,
                f.fecha_ultimo_contacto.strftime(FORMATO_FECHA),
                _documentos(f),
            ]
            for f in seleccion
        ],
    )
    print(f"\n{_contar_farmacias(len(seleccion))}")


def _comando_alertas(farmacias: list[Farmacia], args: argparse.Namespace) -> None:
    hoy = date.today()
    en_alerta = alertas_sin_contacto(farmacias, args.dias, hoy)
    if not en_alerta:
        print(f"No hay farmacias sin contacto desde hace más de {args.dias} días.")
        return
    _imprimir_tabla(
        ["Nombre", "Responsable", "Estado", "Último contacto", "Días", "Documentos pendientes"],
        [
            [
                f.nombre,
                f.responsable,
                f.estado.value,
                f.fecha_ultimo_contacto.strftime(FORMATO_FECHA),
                str(dias_sin_contacto(f, hoy)),
                _documentos(f),
            ]
            for f in en_alerta
        ],
    )
    print(
        f"\n{_contar_farmacias(len(en_alerta))} sin contacto "
        f"desde hace más de {args.dias} días"
    )


def _comando_documentos(farmacias: list[Farmacia], args: argparse.Namespace) -> None:
    documentos = documentos_pendientes_por_frecuencia(farmacias)
    if not documentos:
        print("Ninguna farmacia fuera de live tiene documentos pendientes.")
        return
    _imprimir_tabla(
        ["Documento", "Farmacias"],
        [[documento, str(total)] for documento, total in documentos],
        columnas_numericas={1},
    )
    total = len(farmacias_con_documentos_pendientes(farmacias))
    print(
        f"\n{_contar_farmacias(total)} con documentos pendientes "
        "(sin contar las que están en live)"
    )


def _imprimir_tabla(
    cabeceras: list[str], filas: list[list[str]], columnas_numericas: set[int] = frozenset()
) -> None:
    """Imprime una tabla alineada. Las columnas numéricas se alinean a la derecha."""
    anchos = [max(len(valor) for valor in columna) for columna in zip(cabeceras, *filas)]

    def linea(valores: list[str]) -> str:
        celdas = [
            v.rjust(a) if i in columnas_numericas else v.ljust(a)
            for i, (v, a) in enumerate(zip(valores, anchos))
        ]
        return "  ".join(celdas).rstrip()

    print(linea(cabeceras))
    print("  ".join("-" * a for a in anchos))
    for fila in filas:
        print(linea(fila))


def _documentos(farmacia: Farmacia) -> str:
    return ", ".join(farmacia.documentos_pendientes) or "-"


def _contar_farmacias(n: int) -> str:
    return f"{n} farmacia" if n == 1 else f"{n} farmacias"
