# Postmortem: clientes de Chile publicados como Perú en Gold

> Sin culpables: buscamos qué falló en el proceso, no quién se equivocó.

**Equipo y roles:** Comandante: [ Yovani ] · Operador: [ Cesar ] · Comunicador: [ David ]

## Resumen

- Un cambio al catálogo de países (`data/ref/paises.csv`) se describió como "agregar `iso3` y ordenar alfabéticamente", pero además cambió el mapeo de `CL`: pasó de `Chile / Cono Sur` a `Perú / Andina`.
- El cambio llegó a `main` el viernes y disparó el pipeline de producción. Los clientes de Chile del lote del viernes entraron a Silver como Perú, y Gold los sumó al segmento de Perú.
- El lunes, la campaña de Perú llegó a clientes de Chile, y la campaña de Chile salió con menos gente. El total de contactables no cambió porque los clientes se movieron de país, no desaparecieron. Por eso el dashboard no mostró nada raro.

## Impacto

- `gameday.ref_paises`: la fila `CL` quedó con el nombre y la región equivocados.
- `gameday.silver_customers_v2`: los 4 clientes `CL` del lote del viernes (ids 13, 14, 16 y 19) quedaron como `Perú / Andina`. Los clientes `CL` del jueves no cambiaron, porque `load_silver.sql` solo inserta clientes nuevos.
- `gameday.gold_contactables_por_pais`: la fila de Perú sumó 4 clientes de Chile, 3 de ellos contactables. La fila de Chile perdió esos mismos clientes.
- Marketing: la campaña de Perú se envió a 3 clientes de Chile y la campaña de Chile llegó a menos personas. Hay que reenviar o corregir la campaña de la tarde.

## Línea de tiempo

| Hora | Qué pasó |
| --- | --- |
| vie 23, 09:15 | Llega el lote del viernes: 8 clientes, 4 de Chile |
| vie 23, 17:48 | Se hace el commit del cambio al catálogo (`3915bc8`). El mensaje describe un cambio de forma, pero el diff también cambia el mapeo de `CL` |
| vie 23, 18:05 | El cambio se mergea a `main` (`9ad2866`). El push a `data/**` dispara el pipeline de producción |
| vie 23, [ hh:mm ] | El pipeline recarga `ref_paises` con el catálogo nuevo, Silver inserta a los clientes `CL` como Perú, la validación pasa y Gold se publica |
| lun 27, 09:05 | Marketing reporta que la campaña de Perú llegó a clientes de Chile |
| [ hh:mm ] | Inicio del incidente en el game day (`preparar-produccion`) |
| [ hh:mm ] | Detectamos la causa: el diff de `3915bc8` cambia `CL` a `Perú / Andina` |
| [ hh:mm ] | Contenemos: retenemos el lote del lunes y no publicamos Gold con el catálogo malo |
| [ hh:mm ] | Revertimos el cambio del catálogo en `main` |
| [ hh:mm ] | Recuperamos Silver y Gold: restore silver_customers_v2, corregir ref_paises y reprocesar lotes |
| [ hh:mm ] | Cargamos el lote del lunes |
| [ hh:mm ] | Primer `verificar` en verde |

**MTTR:** [ minutos desde el inicio del incidente hasta el primer verificar en verde ]

## Causa raíz

- **El cambio:** el commit `3915bc8` modificó valores del catálogo de referencia (`CL` → `Perú / Andina`), aunque su mensaje solo hablaba de agregar una columna y reordenar filas. La diferencia entre lo que decía el commit y lo que hacía el diff no se detectó antes del merge.
- **Por qué llegó a producción:** cualquier push a `main` que toque `data/**` corre el pipeline completo y publica Gold. No hay revisión obligatoria para los cambios en `data/ref/`, ni un ambiente intermedio.
- **Por qué los checks no lo frenaron:** `validate_silver.py` solo mira nombres nulos y menores de edad. Ningún check compara el país de Silver contra lo esperado, ni revisa que un `country_code` tenga un único nombre. Además, un `FAIL` en `ops_dq_results` no corta el pipeline: el script termina bien y Gold se publica igual.

## Qué funcionó y qué no

- **Funcionó:** el historial de Delta (`DESCRIBE HISTORY` y time travel) mostró desde qué versión el dato estaba mal; el historial de git llevó al commit exacto; Marketing avisó rápido.
- **No funcionó:** ninguna validación detectó el cambio; el dashboard no mostró nada porque el total se mantuvo; el cambio entró un viernes a la tarde y se publicó sin revisión del diff de datos.

## Acción preventiva

- Check nuevo en `framework/validation/validate_silver.py`: `country_mapping_conflicts` cuenta los `country_code` con más de un par (nombre, región) y los `country_name` con más de un `country_code`. Si el valor es mayor a 0, escribe `FAIL` en `gameday.ops_dq_results` y corta el pipeline antes de publicar Gold.
- ¿Lo probaron? ¿Falla si vuelven a aplicar el cambio del viernes? no
- Otras acciones (con dueño y fecha):
  - Revisión obligatoria en los PR que tocan `data/ref/` (por ejemplo, con `CODEOWNERS`). Dueño: [ ... ] · Fecha: [ ... ]
  - Test en CI que compare `data/ref/paises.csv` contra el catálogo esperado antes del merge. Dueño: [ ... ] · Fecha: [ ... ]
  - Definir qué checks bloquean la publicación de Gold y cuáles solo avisan. Dueño: [ ... ] · Fecha: [ ... ]
