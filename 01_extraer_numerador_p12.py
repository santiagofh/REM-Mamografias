from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

SERIE_P = Path(os.environ.get("SERIE_P2025_PATH", ROOT / "data" / "SerieP2025.csv"))
TARGET_MONTH = "12"

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


def to_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype("int64")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

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
        & (df["Mes"] == TARGET_MONTH)
        & (df["CodigoPrestacion"].isin(P12_B1_CODES))
    ].copy()

    df.insert(
        df.columns.get_loc("CodigoPrestacion") + 1,
        "descripcion_prestacion",
        df["CodigoPrestacion"].map(P12_B1_DESCRIPTIONS),
    )
    df["tramo_edad"] = df["CodigoPrestacion"].map(P12_B1_CODES)
    df = df.rename(
        columns={
            "Col01": "mujeres_mamografia_vigente",
            "Col02": "trans_masculino_mamografia_vigente",
            "Col03": "pueblos_originarios",
            "Col04": "migrantes",
        }
    )
    value_cols = [
        "mujeres_mamografia_vigente",
        "trans_masculino_mamografia_vigente",
        "pueblos_originarios",
        "migrantes",
    ]
    for col in value_cols:
        df[col] = to_int_series(df[col])

    index_cols = [
        "Ano",
        "Mes",
        "IdRegion",
        "IdServicio",
        "IdComuna",
        "IdEstablecimiento",
    ]
    resumen = (
        df.pivot_table(
            index=index_cols,
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
    resumen = resumen[index_cols + age_cols + ["numerador_mujeres_50_69"]]

    largo_path = OUTPUT / "numerador_p12_b1_mamografia_rm_2025.csv"
    resumen_path = OUTPUT / "numerador_p12_b1_mamografia_rm_2025_resumen_establecimiento.csv"
    df.to_csv(largo_path, index=False, encoding="utf-8-sig")
    resumen.to_csv(resumen_path, index=False, encoding="utf-8-sig")

    print(f"Numerador largo: {largo_path}")
    print(f"Numerador resumen: {resumen_path}")
    print(f"Filas largas: {len(df):,}")
    print(f"Mes REM-P usado: {TARGET_MONTH}")
    print(f"Establecimientos diciembre: {len(resumen):,}")
    print(f"Numerador diciembre RM: {resumen['numerador_mujeres_50_69'].sum():,}")


if __name__ == "__main__":
    main()
