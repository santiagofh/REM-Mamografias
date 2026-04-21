# REM-Mamografia

Documentacion operativa para preparar la data 2025 de cobertura de mamografia reportada en REM-P12.

## Objetivo

Calcular la cobertura de mamografia vigente en mujeres de 50 a 69 anos de la Region Metropolitana para el ano 2025, usando REM-P12 como numerador y Poblacion Inscrita Validada (PIV) FONASA como denominador.

El calculo trabaja solo con el corte de diciembre: `Mes = 12` del REM-P 2025.

## Salidas generadas

Carpeta autocontenida de trabajo:

raiz del repositorio `REM-Mamografias`.

Programas en la raiz de la carpeta:

1. `01_extraer_numerador_p12.py`
2. `02_calcular_denominador_piv.py`
3. `03_calcular_cobertura_mamografia.py`

Carpeta `output` con el calculo y resultados:

`output/`

Archivos principales:

- `cobertura_mamografia_rm_2025.xlsx`: libro consolidado con comuna diciembre, establecimiento/control, denominador, control y metodologia.
- `visualizacion_paralela_mamografia_dic_2025.xlsx`: libro para revision visual, con comuna principal, establecimiento/control, control de calidad y metodologia.
- `cobertura_mamografia_establecimiento_rm_2025.csv`: cobertura por establecimiento.
- `cobertura_mamografia_comuna_rm_2025.csv`: cobertura por comuna.
- `denominador_piv_mujeres_50_69_rm_base_pago_2025.csv`: PIV mujeres 50-69.
- `numerador_p12_b1_mamografia_rm_2025.csv`: extraccion larga desde REM-P12 B1.
- `numerador_p12_b1_mamografia_rm_2025_resumen_establecimiento.csv`: numerador agregado por establecimiento y tramo de edad.
- `control_calidad_mamografia_rm_2025.csv`: registros que requieren revision.
- `metadata_mamografia_rm_2025.csv`: trazabilidad metodologica.

## Dashboard Streamlit

Se agrego una aplicacion Streamlit para explorar la cobertura comunal y el detalle por establecimiento, siguiendo la linea grafica del dashboard de Influenza 2024.

Archivos:

- `streamlit_dashboard.py`: punto de entrada de la aplicacion.
- `dashboard_mamografia_pages.py`: paginas, tablas, graficos y descargas.
- `.streamlit/config.toml`: configuracion local de Streamlit, puerto `8502`.
- `assets/`: logo lateral institucional.
- `requirements.txt`: dependencias minimas.

Ejecucion:

```powershell
streamlit run .\streamlit_dashboard.py
```

La pagina inicial muestra primero la tabla de cobertura por comuna, seguida de indicadores regionales y un grafico territorial. La pagina `Detalle comunal` permite seleccionar una comuna y revisar la tabla de establecimientos. La pagina `Control y metodologia` muestra la metodologia del calculo en formato de texto.

Criterio comunal aplicado: los establecimientos con numerador REM-P12 se suman al numerador de su comuna. Si un establecimiento no tiene PIV directa, queda en control solo para la cobertura establecimiento; no se excluye de la cobertura comunal.

## Orden de ejecucion

Desde PowerShell:

```powershell
python .\01_extraer_numerador_p12.py
python .\02_calcular_denominador_piv.py
python .\03_calcular_cobertura_mamografia.py
```

Cada programa escribe sus resultados en `output`.

### Programa 1: numerador

`01_extraer_numerador_p12.py`

Lee `SerieP2025.csv`, filtra REM-P12 B1 para Region Metropolitana y extrae mujeres de 50 a 69 anos con mamografia vigente, solo para `Mes = 12`.

Salidas:

- `output\numerador_p12_b1_mamografia_rm_2025.csv`
- `output\numerador_p12_b1_mamografia_rm_2025_resumen_establecimiento.csv`

### Programa 2: denominador

`02_calcular_denominador_piv.py`

Lee la PIV FONASA base pago 2025, filtra mujeres de 50 a 69 anos, aplica el alias `311001 -> 201674` y calcula el denominador por establecimiento.

Salida:

- `output\denominador_piv_mujeres_50_69_rm_base_pago_2025.csv`

### Programa 3: cobertura

`03_calcular_cobertura_mamografia.py`

Lee el numerador y denominador ya calculados desde `output`, calcula cobertura por establecimiento y comuna, genera el control de calidad y arma los Excel de revision.

Salidas:

- `output\cobertura_mamografia_establecimiento_rm_2025.csv`
- `output\cobertura_mamografia_comuna_rm_2025.csv`
- `output\control_calidad_mamografia_rm_2025.csv`
- `output\metadata_mamografia_rm_2025.csv`
- `output\cobertura_mamografia_rm_2025.xlsx`
- `output\visualizacion_paralela_mamografia_dic_2025.xlsx`

## Metodologia

Formula:

```text
Cobertura (%) =
  Mujeres de 50 a 69 anos con mamografia vigente
  / Poblacion Inscrita Validada (PIV) de mujeres de 50 a 69 anos
  * 100
```

### Numerador

Fuente:

Archivo local `SerieP2025.csv`. El script lo busca por defecto en `data/SerieP2025.csv`; tambien se puede indicar otra ubicacion con la variable de entorno `SERIE_P2025_PATH`.

Definicion:

- REM-P12.
- Seccion B1: Mujeres con mamografia vigente en los ultimos 2 anos.
- Region Metropolitana: `IdRegion = 13`.
- Corte principal: mes `12` de 2025.
- Columna utilizada: `Col01`, correspondiente a mujeres con mamografia vigente.

Codigos REM usados:

| CodigoPrestacion | Tramo |
| --- | --- |
| `P1220030` | 50 a 54 anos |
| `P1207030` | 55 a 59 anos |
| `P1207040` | 60 a 64 anos |
| `P1207050` | 65 a 69 anos |

El numerador suma los cuatro tramos anteriores.

### Denominador

Fuente local:

Archivo PIV FONASA base pago 2025. El script lo busca por defecto en `data/T8009_Inscritos_RM.xlsx`; tambien se puede indicar otra ubicacion con la variable de entorno `PIV_MAMOGRAFIA_PATH`.

El maestro de establecimientos se busca por defecto en `data/establecimientos_20260406_oficial.csv`; tambien se puede indicar otra ubicacion con la variable de entorno `MAESTRO_ESTABLECIMIENTOS_PATH`.

Definicion aplicada:

- Poblacion inscrita en centros APS de la Region Metropolitana.
- Base: inscritos 2024, base de pago 2025.
- Fecha de referencia indicada en archivo: septiembre de 2024.
- Sexo: mujeres.
- Edad: 50 a 69 anos.
- Todas las nacionalidades.

### Ajuste aplicado

Se detecto un alias de codigo entre PIV y REM/DEIS:

| Codigo PIV original | Codigo REM/DEIS usado | Establecimiento |
| --- | --- | --- |
| `311001` | `201674` | CESFAM El Abrazo Dr. Salvador Allende |

Este alias fue aplicado en el script para no dejar subcontado el denominador de Maipu ni del establecimiento.

## Resultado regional preliminar

Corte diciembre 2025, Region Metropolitana:

| Indicador | Valor |
| --- | ---: |
| Numerador mujeres 50-69 con mamografia vigente | 236.840 |
| Denominador PIV mujeres 50-69 | 751.298 |
| Cobertura regional | 31,52% |

## Nota sobre cobertura por establecimiento

La cobertura por establecimiento se calcula y se mantiene tal como resulta de la formula. Algunas coberturas pueden superar 100%, especialmente en establecimientos con denominador PIV directo pequeno. Esos casos no se consideran error por si solos.

Para reporte territorial, la salida comunal sigue siendo la mas estable porque numerador y denominador quedan agregados al mismo nivel.

El archivo `control_calidad_mamografia_rm_2025.csv` lista solo casos incompletos:

- establecimientos con numerador REM-P12 sin PIV directa.

## Por que REM-P12 y no REM-A29

El REM-A29 registra produccion, es decir procedimientos o examenes realizados en un periodo. Por eso puede contar mas de una vez a una misma persona si tuvo controles, repeticiones o seguimiento.

El REM-P12 registra personas con tamizaje vigente. Para cobertura interesa saber cuantas mujeres unicas tienen su mamografia al dia, no cuantos examenes fueron informados.

## Pendientes

- Validar con Angelica que la PIV usada (`T8009_Inscritos_RM.xlsx`) corresponde oficialmente al denominador requerido para 2025.
- Confirmar si el indicador debe reportarse solo con corte diciembre o si tambien se requiere corte junio por tratarse de REM semestral.
- Revisar los 5 establecimientos con numerador REM-P12 sin PIV directa:
  - `201353`: CECOSF Union y Esfuerzo Rural, Pudahuel.
  - `110720`: CECOSF Catamarca, Quinta Normal, codigo madre `110320`.
  - `200475`: CECOSF Las Lomas, La Florida, codigo madre `114303`.
  - `201212`: CESFAM Juan Pablo II de Lampa.
  - `109104`: Hospital de Til Til.
- Definir criterio institucional para establecimientos sin PIV directa:
  - mantenerlos en control y no calcular cobertura establecimiento;
  - imputar denominador desde establecimiento madre, si corresponde;
  - agregar solo a comuna;
  - o solicitar correccion/confirmacion a FONASA/DEIS.
- Verificar si la meta IAAPS exige vigencia de 23 meses o si para esta entrega basta con el concepto REM-P12 de "menor o igual a 2 anos".
- Documentar respuesta de Angelica y reemplazar esta nota si entrega una PIV oficial distinta.

## Copia del correo/requerimiento

> Por favor prepara la data para 2025, la poblacion inscrita consultala con Angelica, que dicho sea de paso no la encontre en GEOSITAS y debe estar.
>
> Hable con Lumi y ellos no tienen el dato, tampoco saben calcularlo, asi que indague por otro lado y encontre la forma de calcularlo.
>
> Para calcular la cobertura de mamografia, especificamente la que se reporta en el REM-P12, se utiliza una formula de porcentaje que mide que proporcion de la poblacion objetivo tiene su examen al dia.
>
> La formula tecnica es:
>
> Cobertura (%) = Mujeres de 50 a 69 anos con Mamografia Vigente / Poblacion Inscrita Validada (PIV) de mujeres de 50 a 69 anos * 100.
>
> Componentes de la formula:
>
> 1. Numerador: se extrae de la Serie P12, Seccion B.1. Se considera vigente si el examen se realizo en los ultimos 2 anos, segun estandar ministerial para metas sanitarias, o 3 anos segun periodicidad preventiva general. Para metas de gestion IAAPS suele usarse el corte de 23 meses. Incluye mamografias realizadas en CESFAM, hospitales de la red o clinicas privadas, siempre que el resultado haya sido entregado y registrado en ficha.
>
> 2. Denominador: se utiliza la Poblacion Inscrita Validada (PIV) por FONASA en el establecimiento o comuna. El grupo prioritario para el indicador de salud publica en Chile es el tramo 50 a 69 anos.
>
> El REM-A29 aporta informacion sobre capacidad diagnostica y flujo de pacientes, pero no se utiliza para el calculo oficial de la tasa de cobertura.
>
> El A29 registra cuantos procedimientos se informan en un periodo determinado. Si una paciente se hace dos mamografias en un ano por seguimiento, el A29 marcara dos examenes. Si el A29 registra 100 mamografias, no sabemos si son 100 mujeres distintas o 50 mujeres con dos examenes cada una.
>
> El P12 es de personas y cobertura. Su objetivo es saber cuantas mujeres unicas estan protegidas. En la formula de cobertura, si una mujer se hizo dos mamografias, en el P12 sigue contando como una persona vigente. La cobertura mide personas, no examenes.
