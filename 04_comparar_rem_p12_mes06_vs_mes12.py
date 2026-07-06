from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output_comparativo_rem_p12"

SERIE_P = Path(
    os.environ.get(
        "SERIE_P2025_PATH",
        Path(
            r"D:\DATA\REM\REM_2025\Datos\SerieP2025.csv"
        ),
    )
)
ESTABLECIMIENTOS = Path(
    os.environ.get(
        "MAESTRO_ESTABLECIMIENTOS_PATH",
        Path(
            r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\ESTABLECIMIENTOS\establecimientos_20260424.csv"
        ),
    )
)

MESES = ("6", "12")

P12_B1_CODES = {
    "P1220030": "50_54",
    "P1207030": "55_59",
    "P1207040": "60_64",
    "P1207050": "65_69",
}

P12_B1_DESCRIPTIONS = {
    "P1220030": "Mujeres 50 a 54 anos con mamografia vigente (<= 2 anos)",
    "P1207030": "Mujeres 55 a 59 anos con mamografia vigente (<= 2 anos)",
    "P1207040": "Mujeres 60 a 64 anos con mamografia vigente (<= 2 anos)",
    "P1207050": "Mujeres 65 a 69 anos con mamografia vigente (<= 2 anos)",
}


def code_text(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .replace({"nan": "", "None": ""})
    )


def to_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype("int64")


def load_establecimientos() -> pd.DataFrame:
    cols = [
        "EstablecimientoCodigo",
        "EstablecimientoCodigoMadreNuevo",
        "SeremiSaludGlosa_ServicioDeSaludGlosa",
        "TipoEstablecimientoGlosa",
        "EstablecimientoGlosa",
        "DependenciaAdministrativa",
        "ComunaGlosa",
        "EstadoFuncionamiento",
    ]
    df = pd.read_csv(ESTABLECIMIENTOS, sep=";", dtype=str, usecols=cols)
    for col in ["EstablecimientoCodigo", "EstablecimientoCodigoMadreNuevo"]:
        df[col] = code_text(df[col])
    return df.drop_duplicates("EstablecimientoCodigo").rename(
        columns={
            "EstablecimientoCodigo": "IdEstablecimiento",
            "EstablecimientoCodigoMadreNuevo": "codigo_madre_master",
            "SeremiSaludGlosa_ServicioDeSaludGlosa": "servicio_salud_master",
            "TipoEstablecimientoGlosa": "tipo_establecimiento_master",
            "EstablecimientoGlosa": "establecimiento_master",
            "DependenciaAdministrativa": "dependencia_master",
            "ComunaGlosa": "comuna_master",
            "EstadoFuncionamiento": "estado_funcionamiento_master",
        }
    )


def extraer_rem_p12() -> pd.DataFrame:
    usecols = [
        "Mes",
        "IdServicio",
        "Ano",
        "IdEstablecimiento",
        "CodigoPrestacion",
        "IdRegion",
        "IdComuna",
        "Col01",
        "Col02",
        "Col03",
        "Col04",
    ]
    df = pd.read_csv(SERIE_P, sep=";", dtype=str, usecols=usecols)
    df = df[
        (df["IdRegion"] == "13")
        & (df["Ano"] == "2025")
        & (df["Mes"].isin(MESES))
        & (df["CodigoPrestacion"].isin(P12_B1_CODES))
    ].copy()

    df["CodigoPrestacion"] = code_text(df["CodigoPrestacion"])
    df["IdEstablecimiento"] = code_text(df["IdEstablecimiento"])
    df["IdComuna"] = code_text(df["IdComuna"])
    df["IdServicio"] = code_text(df["IdServicio"])
    df["descripcion_prestacion"] = df["CodigoPrestacion"].map(P12_B1_DESCRIPTIONS)
    df["tramo_edad"] = df["CodigoPrestacion"].map(P12_B1_CODES)

    df = df.rename(
        columns={
            "Col01": "mujeres_mamografia_vigente",
            "Col02": "trans_masculino_mamografia_vigente",
            "Col03": "pueblos_originarios",
            "Col04": "migrantes",
        }
    )
    for col in [
        "mujeres_mamografia_vigente",
        "trans_masculino_mamografia_vigente",
        "pueblos_originarios",
        "migrantes",
    ]:
        df[col] = to_int_series(df[col])
    return df


def clasificar_alerta(total_mes_6: float, total_mes_12: float) -> str:
    if total_mes_6 > 0 and total_mes_12 == 0:
        return "Pasa a 0 en mes 12"
    if total_mes_12 < total_mes_6:
        return "Baja de mes 6 a mes 12"
    if total_mes_6 == 0 and total_mes_12 > 0:
        return "Aparece solo en mes 12"
    if total_mes_6 == total_mes_12:
        return "Sin variacion"
    return "Aumento esperado"


def construir_comparativo(df: pd.DataFrame, estab: pd.DataFrame) -> pd.DataFrame:
    resumen = (
        df.pivot_table(
            index=["Ano", "Mes", "IdRegion", "IdServicio", "IdComuna", "IdEstablecimiento"],
            columns="tramo_edad",
            values="mujeres_mamografia_vigente",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    for label in P12_B1_CODES.values():
        if label not in resumen.columns:
            resumen[label] = 0

    age_cols = list(P12_B1_CODES.values())
    resumen["numerador_mujeres_50_69"] = resumen[age_cols].sum(axis=1)

    comparativo = resumen.pivot_table(
        index=["Ano", "IdRegion", "IdServicio", "IdComuna", "IdEstablecimiento"],
        columns="Mes",
        values=age_cols + ["numerador_mujeres_50_69"],
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    comparativo.columns = [
        f"{campo} | Mes {mes}" if mes else campo
        for campo, mes in comparativo.columns.to_flat_index()
    ]

    comparativo = comparativo.merge(estab, on="IdEstablecimiento", how="left")

    base_cols = [
        "Ano",
        "IdRegion",
        "IdServicio",
        "IdComuna",
        "IdEstablecimiento",
        "servicio_salud_master",
        "comuna_master",
        "establecimiento_master",
        "tipo_establecimiento_master",
        "dependencia_master",
        "estado_funcionamiento_master",
        "codigo_madre_master",
    ]

    for tramo in age_cols + ["numerador_mujeres_50_69"]:
        col_6 = f"{tramo} | Mes 6"
        col_12 = f"{tramo} | Mes 12"
        if col_6 not in comparativo.columns:
            comparativo[col_6] = 0
        if col_12 not in comparativo.columns:
            comparativo[col_12] = 0
        comparativo[f"{tramo} | Diferencia"] = comparativo[col_12] - comparativo[col_6]

    comparativo["Total mes 6"] = comparativo["numerador_mujeres_50_69 | Mes 6"]
    comparativo["Total mes 12"] = comparativo["numerador_mujeres_50_69 | Mes 12"]
    comparativo["Diferencia"] = comparativo["Total mes 12"] - comparativo["Total mes 6"]
    comparativo["Variacion %"] = 0.0
    mask = comparativo["Total mes 6"] != 0
    comparativo.loc[mask, "Variacion %"] = (
        comparativo.loc[mask, "Diferencia"] / comparativo.loc[mask, "Total mes 6"] * 100
    ).round(2)
    comparativo["Alerta"] = comparativo.apply(
        lambda fila: clasificar_alerta(fila["Total mes 6"], fila["Total mes 12"]),
        axis=1,
    )

    ordered_cols = base_cols + [
        "50_54 | Mes 6",
        "50_54 | Mes 12",
        "50_54 | Diferencia",
        "55_59 | Mes 6",
        "55_59 | Mes 12",
        "55_59 | Diferencia",
        "60_64 | Mes 6",
        "60_64 | Mes 12",
        "60_64 | Diferencia",
        "65_69 | Mes 6",
        "65_69 | Mes 12",
        "65_69 | Diferencia",
        "numerador_mujeres_50_69 | Mes 6",
        "numerador_mujeres_50_69 | Mes 12",
        "numerador_mujeres_50_69 | Diferencia",
        "Total mes 6",
        "Total mes 12",
        "Diferencia",
        "Variacion %",
        "Alerta",
    ]

    comparativo = comparativo[ordered_cols].sort_values(
        ["servicio_salud_master", "comuna_master", "establecimiento_master", "IdEstablecimiento"],
        kind="stable",
    )
    return comparativo


def construir_alertas(comparativo: pd.DataFrame) -> pd.DataFrame:
    alertas = comparativo[
        comparativo["Alerta"].isin(["Pasa a 0 en mes 12", "Baja de mes 6 a mes 12"])
    ].copy()
    return alertas.sort_values(
        ["Alerta", "Diferencia", "servicio_salud_master", "comuna_master"],
        ascending=[True, True, True, True],
        kind="stable",
    )


def construir_resumen(alertas: pd.DataFrame, comparativo: pd.DataFrame) -> pd.DataFrame:
    conteo = alertas["Alerta"].value_counts()
    resumen = pd.DataFrame(
        [
            {
                "Total establecimientos comparados": len(comparativo),
                "Total alertas": len(alertas),
                "Pasa a 0 en mes 12": int(conteo.get("Pasa a 0 en mes 12", 0)),
                "Baja de mes 6 a mes 12": int(conteo.get("Baja de mes 6 a mes 12", 0)),
                "Aparece solo en mes 12": int((comparativo["Alerta"] == "Aparece solo en mes 12").sum()),
                "Sin variacion": int((comparativo["Alerta"] == "Sin variacion").sum()),
                "Aumento esperado": int((comparativo["Alerta"] == "Aumento esperado").sum()),
            }
        ]
    )
    return resumen


def ajustar_formato_excel(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    ws = writer.book[sheet_name]
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for idx, col_name in enumerate(df.columns, start=1):
        width = min(max(12, len(str(col_name)) + 2), 45)
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    df = extraer_rem_p12()
    estab = load_establecimientos()
    comparativo = construir_comparativo(df, estab)
    alertas = construir_alertas(comparativo)
    resumen = construir_resumen(alertas, comparativo)

    comparativo_csv = OUTPUT / "comparativo_rem_p12_mes06_vs_mes12_establecimiento.csv"
    alertas_csv = OUTPUT / "informe_alertas_rem_p12_mes06_vs_mes12.csv"
    excel_path = OUTPUT / "comparativo_rem_p12_mes06_vs_mes12.xlsx"

    comparativo.to_csv(comparativo_csv, index=False, encoding="utf-8-sig")
    alertas.to_csv(alertas_csv, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        resumen.to_excel(writer, sheet_name="Resumen", index=False)
        comparativo.to_excel(writer, sheet_name="Comparativo", index=False)
        alertas.to_excel(writer, sheet_name="Alertas", index=False)
        ajustar_formato_excel(writer, "Resumen", resumen)
        ajustar_formato_excel(writer, "Comparativo", comparativo)
        ajustar_formato_excel(writer, "Alertas", alertas)

    print(f"Comparativo: {comparativo_csv}")
    print(f"Alertas: {alertas_csv}")
    print(f"Excel: {excel_path}")
    print(f"Establecimientos comparados: {len(comparativo):,}")
    print(f"Alertas detectadas: {len(alertas):,}")


if __name__ == "__main__":
    main()
