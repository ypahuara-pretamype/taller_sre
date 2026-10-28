# Prompts opcionales: la IA como copiloto del incidente

Úsenlos con cualquier asistente que pueda leer su repo. La IA sugiere; el
equipo decide, ejecuta y verifica. Antes de correr algo que la IA proponga,
el Operador lo lee y el Comandante lo aprueba.

## 1. Entender qué cambió

```
Lee el historial de git de este repo desde el jueves 22 de octubre.
Para cada commit dime en una línea qué cambió y qué tablas del schema
gameday podría afectar. No propongas arreglos todavía.
```

## 2. Revisar el impacto en los datos

```
Escríbeme queries de Databricks SQL (solo lectura) para comparar la
versión actual de gameday.silver_customers_v2 y de
gameday.gold_contactables_por_pais con sus versiones anteriores.
Quiero saber qué filas cambiaron y desde qué versión.
```

## 3. Elegir cómo recuperar

```
Tenemos que dejar Silver y Gold en un estado bueno sin duplicar registros.
Compárame dos caminos: Corregir ref_paises reprocesar el lote del viernes, actualizado las filas ya procesadas por el customer_id y Corregir ref_paises, borrar todo y reprocesar los lotes del jueves y viernes. Para cada uno dime
qué riesgos tiene, qué pasa con el lote que llegó después y cuánto
reproceso implica. No ejecutes nada.
```

## 4. Redactar el postmortem

```
Con esta línea de tiempo y esta causa raíz "alguien modifico el ref_paises, cambiando el country_name de Chile a Peru", ayúdame a redactar
ops/postmortem.md sin culpables. Mantén la estructura de la plantilla.
```

## 5. Proponer el check

```
Propón un check para framework/validation/validate_silver.py que habría
fallado con el cambio del viernes. Debe seguir el estilo del archivo y
escribir su resultado en gameday.ops_dq_results.
```

## 6. Estimar costos

```
Con estas duraciones por stage [pegar] y estas tarifas supuestas [pegar],
calcula el costo por corrida y por mes. Después lee el workflow
dataops-pipeline.yml y dime qué partes cuestan sin agregar valor.
```
