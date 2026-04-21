from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

POBLACION_INSCRITA_VALIDADA = Path(
    os.environ.get(
        "POBLACION_INSCRITA_VALIDADA_PATH",
        ROOT / "data" / "T8009_Inscritos_RM.xlsx",
    )
)
ESTABLECIMIENTOS = Path(
    os.environ.get(
        "MAESTRO_ESTABLECIMIENTOS_PATH",
        ROOT / "data" / "establecimientos_20260406_oficial.csv",
    )
)

# Alias observado entre la población inscrita y validada FONASA 2024/base pago
# 2025 y el maestro REM. FONASA codifica este CESFAM como 311001, pero
# REM/DEIS lo registra como 201674.
DENOMINATOR_CODE_ALIASES = {
    "311001": "201674",
}


def to_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype("int64")


def code_text(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .replace({"nan": "", "None": ""})
    )


def load_establecimientos() -> pd.DataFrame:
    cols = [
        "EstablecimientoCodigo",
        "EstablecimientoCodigoAntiguo",
        "EstablecimientoCodigoMadreNuevo",
        "RegionCodigo",
        "SeremiSaludCodigo_ServicioDeSaludCodigo",
        "SeremiSaludGlosa_ServicioDeSaludGlosa",
        "TipoEstablecimientoGlosa",
        "EstablecimientoGlosa",
        "DependenciaAdministrativa",
        "ComunaCodigo",
        "ComunaGlosa",
        "EstadoFuncionamiento",
    ]
    df = pd.read_csv(ESTABLECIMIENTOS, sep=";", dtype=str, usecols=cols)
    for col in [
        "EstablecimientoCodigo",
        "EstablecimientoCodigoMadreNuevo",
        "RegionCodigo",
        "SeremiSaludCodigo_ServicioDeSaludCodigo",
        "ComunaCodigo",
    ]:
        df[col] = code_text(df[col])
    return df.drop_duplicates("EstablecimientoCodigo")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    inscritos = pd.read_excel(POBLACION_INSCRITA_VALIDADA, sheet_name="Respuesta", header=3)
    inscritos = inscritos.rename(
        columns={
            "Servicio de Salud": "servicio_salud_denominador",
            "Dependencia": "dependencia_denominador",
            "Comuna": "comuna_denominador",
            "Código Centro": "IdEstablecimiento",
            "Nombre Centro": "establecimiento_denominador",
            "Nacionalidad": "nacionalidad",
            "Sexo": "sexo",
            "Edad": "edad",
            "Inscritos": "inscritos",
        }
    )
    inscritos["IdEstablecimiento_denominador_original"] = code_text(inscritos["IdEstablecimiento"])
    inscritos["IdEstablecimiento"] = inscritos["IdEstablecimiento_denominador_original"].replace(DENOMINATOR_CODE_ALIASES)
    inscritos["edad"] = pd.to_numeric(inscritos["edad"], errors="coerce")
    inscritos["inscritos"] = to_int_series(inscritos["inscritos"])

    inscritos = inscritos[
        inscritos["sexo"].astype(str).str.strip().eq("Mujeres")
        & inscritos["edad"].between(50, 69, inclusive="both")
    ].copy()

    group_cols = [
        "IdEstablecimiento",
        "IdEstablecimiento_denominador_original",
        "servicio_salud_denominador",
        "dependencia_denominador",
        "comuna_denominador",
        "establecimiento_denominador",
    ]
    denom = (
        inscritos.groupby(group_cols, dropna=False, as_index=False)["inscritos"]
        .sum()
        .rename(columns={"inscritos": "denominador_poblacion_inscrita_validada_mujeres_50_69"})
    )

    estab = load_establecimientos()
    denom = denom.merge(
        estab[
            [
                "EstablecimientoCodigo",
                "EstablecimientoCodigoMadreNuevo",
                "SeremiSaludCodigo_ServicioDeSaludCodigo",
                "SeremiSaludGlosa_ServicioDeSaludGlosa",
                "TipoEstablecimientoGlosa",
                "EstablecimientoGlosa",
                "DependenciaAdministrativa",
                "ComunaCodigo",
                "ComunaGlosa",
                "EstadoFuncionamiento",
            ]
        ],
        left_on="IdEstablecimiento",
        right_on="EstablecimientoCodigo",
        how="left",
    ).drop(columns=["EstablecimientoCodigo"])

    denom = denom.rename(
        columns={
            "EstablecimientoCodigoMadreNuevo": "codigo_madre_master",
            "SeremiSaludCodigo_ServicioDeSaludCodigo": "IdServicio_master",
            "SeremiSaludGlosa_ServicioDeSaludGlosa": "servicio_salud_master",
            "TipoEstablecimientoGlosa": "tipo_establecimiento_master",
            "EstablecimientoGlosa": "establecimiento_master",
            "DependenciaAdministrativa": "dependencia_master",
            "ComunaCodigo": "IdComuna_master",
            "ComunaGlosa": "comuna_master",
            "EstadoFuncionamiento": "estado_funcionamiento_master",
        }
    )

    output_path = OUTPUT / "denominador_poblacion_inscrita_validada_mujeres_50_69_rm_base_pago_2025.csv"
    denom.to_csv(output_path, index=False, encoding="utf-8-sig")

    sin_master = denom["IdComuna_master"].isna().sum()
    print(f"Denominador: {output_path}")
    print(f"Establecimientos con denominador: {len(denom):,}")
    print(f"Denominador RM mujeres 50-69: {denom['denominador_poblacion_inscrita_validada_mujeres_50_69'].sum():,}")
    print(f"Registros sin match en maestro: {sin_master:,}")


if __name__ == "__main__":
    main()
