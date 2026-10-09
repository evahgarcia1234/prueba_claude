# Onboarding de farmacias

Herramienta de línea de comandos para hacer el seguimiento del onboarding de farmacias a partir de un CSV exportado desde Excel.

## Requisitos

Python 3.10 o superior. No necesita librerías externas (solo `pytest` para los tests).

## Uso

Desde la carpeta del proyecto:

```
python -m onboarding resumen datos/farmacias_ejemplo.csv
python -m onboarding listar datos/farmacias_ejemplo.csv --responsable lucia
python -m onboarding listar datos/farmacias_ejemplo.csv --estado "en revision" --provincia madrid
python -m onboarding alertas datos/farmacias_ejemplo.csv --dias 30
python -m onboarding documentos datos/farmacias_ejemplo.csv
```

### Comandos

| Comando   | Qué hace |
|-----------|----------|
| `resumen` | Cuenta cuántas farmacias hay en cada estado |
| `listar`  | Muestra las farmacias. Filtros opcionales, combinables: `--estado`, `--provincia`, `--responsable` |
| `alertas` | Muestra las farmacias que **no** están en `live` y llevan más de `--dias` días sin contacto (por defecto 15), de la más antigua a la más reciente |
| `documentos` | Cuenta cuántas farmacias tienen pendiente cada documento, de más a menos. No cuenta las que están en `live` |

Notas sobre los filtros:
- `--provincia` y `--responsable` no distinguen mayúsculas ni tildes y aceptan parte del texto: `--responsable lucia` encuentra a "Lucía Pérez".
- Los estados de dos palabras van entre comillas: `--estado "pendiente documentacion"`.

`python -m onboarding <comando> --help` muestra la ayuda de cada comando.

## Formato del CSV

- Separador `;` (el que usa Excel en español).
- Codificación: vale tanto "CSV UTF-8" como "CSV (delimitado por comas)" de Excel.
- Columnas: `nombre;provincia;responsable;estado;fecha_ultimo_contacto;documentos_pendientes`

| Columna                 | Formato |
|-------------------------|---------|
| `estado`                | `pendiente documentacion`, `en revision`, `subsanacion`, `live` o `paralizada` (se aceptan mayúsculas y tildes) |
| `fecha_ultimo_contacto` | `dd/mm/aaaa` |
| `documentos_pendientes` | Nombres separados por `\|`, por ejemplo `contrato\|PNT\|certificado`. Vacío si no falta nada. |

Hay un ejemplo en `datos/farmacias_ejemplo.csv`.

## Tests

```
pip install -r requirements.txt
python -m pytest
```
