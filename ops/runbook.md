# Runbook: <nombre del incidente>

> Un runbook es lo que haría cualquier persona del equipo si esto vuelve a
> pasar a las 3 a. m. Escríbanlo para alguien que no estuvo hoy.

## Cómo me doy cuenta

- ¿Qué señal o alerta lo muestra? ¿Qué query o tabla revisan primero?
- country_mapping_conflicts en la tabla ops_dq_results

## Contener (que no empeore)

- ¿Qué apagan o retienen para no publicar más datos malos? ¿Cómo lo hacen?
- Se detiene el procesamiento de nuevos lotes y no se publica gold

## Recuperar

1. Código: Se revierte el restore 3915bc884dd5e46e8780758c5808ab6ea01c0ce8 y se restaura la tabla gameday.silver_customers_v2 hasta antes de procesar el lote del viernes
2. Datos: Se restaura a una version anterior de gameday.silver_customers_v2, cuando el lote del viernes aun no era procesado, con el comando `RESTORE TABLE gameday.silver_customers_v2 TO VERSION AS OF 1`
3. Reproceso: Se reprocesa ref_paises y silver_customers_v2 y se validan los duplicados por el customer_id
4. Pendientes: Se procesa recien el lote customers_lunes.csv

## Cómo confirmo que volvimos a un estado bueno

- Se revisa la tabla ops_dq_results, las metricas country_mapping_conflicts (=0) y duplicate_customer_id_count (=0) 

## A quién aviso

| Momento | A quién | Qué le digo |
| --- | --- | --- |
| Al detectar | Valeria de Marketing | Los datos no son correctos |
| Al recuperar | Valeria de Marketing | La data ya ha sido publicada correctamente |
