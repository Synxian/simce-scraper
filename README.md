# Script para scrapear los datos del simce

Actualmente tiene los datos para scrapear el simce del 2024 (actualicé el código y los archivos el 17/03/2025)
Recomiendo fuertemente ir guardando batches de resultados, a veces el webdriver falla y se cae el proceso.

Script.py contiene la fase de scrapeo inicial, processing.py procesa los datos, y corrige la extraccióñ del GSE (importante esta parte porque la inicial no la maneja correctamente).
Processing-2 genera los datos de salida con normalizaciones y cosas varias.

## Datos

El csv de matriculas se obtiene de la página de datos abiertos del mineduc, especificamente [aquí](https://datosabiertos.mineduc.cl/resumen-de-matricula-por-establecimiento-educacional/)
El json con todos los colegios se descarga desde la página de la agencia de la educación: [establecimientos.json](https://www.agenciaeducacion.cl/wp-content/themes/ace-child/data/establecimientos.json)
Y el ive desde la página de la junaeb: aquí [IVE](https://www.junaeb.cl/wp-content/uploads/2024/04/IVE-2024.xlsx)

Ojo que los links cambian año a año.

También recomiendo revisar los excel, del año 2023 al 2024 el archivo del ive pasó de comenzar en la fila 4 a la 5.

De todas maneras, al correr get_data se descargan todos los archivos necesarios.

## Contacto

Cualquier duda sobre el código hablar a <felix@pulsoescolar.com> o <felix.melo@ug.uchile.cl>
Código disponible en <https://github.com/Synxian/simce-scraper>
