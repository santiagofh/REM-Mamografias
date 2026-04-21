from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

PIV = Path(os.environ.get("PIV_MAMOGRAFIA_PATH", ROOT / "data" / "T8009_Inscritos_RM.xlsx"))
ESTABLECIMIENTOS = Path(
    os.environ.get(
        "MAESTRO_ESTABLECIMIENTOS_PATH",
        ROOT / "data" / "establecimientos_20260406_oficial.csv",
    )
)

# Alias observado entre la PIV FONASA 2024/base pago 2025 y el maestro REM.
# La PIV codifica este CESFAM como 311001, pero REM/DEIS lo registra como 201674.
PIV_CODE_ALIASES = {
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

    piv = pd.read_excel(PIV, sheet_name="Respuesta", header=3)
    piv = piv.rename(
        columns={
            "Servicio de Salud": "servicio_salud_piv",
            "Dependencia": "dependencia_piv",
            "Comuna": "comuna_piv",
            "Código Centro": "IdEstablecimiento",
            "Nombre Centro": "establecimiento_piv",
            "Nacionalidad": "nacionalidad",
            "Sexo": "sexo",
            "Edad": "edad",
            "Inscritos": "inscritos",
        }
    )
    piv["IdEstablecimiento_piv_original"] = code_text(piv["IdEstablecimiento"])
    piv["IdEstablecimiento"] = piv["IdEstablecimiento_piv_original"].replace(PIV_CODE_ALIASES)
    piv["edad"] = pd.to_numeric(piv["edad"], errors="coerce")
    piv["inscritos"] = to_int_series(piv["inscritos"])

    piv = piv[
        piv["sexo"].astype(str).str.strip().eq("Mujeres")
        & piv["edad"].between(50, 69, inclusive="both")
    ].copy()

    group_cols = [
        "IdEstablecimiento",
        "IdEstablecimiento_piv_original",
        "servicio_salud_piv",
        "dependencia_piv",
        "comuna_piv",
        "establecimiento_piv",
    ]
    denom = (
        piv.groupby(group_cols, dropna=False, as_index=False)["inscritos"]
        .sum()
        .rename(columns={"inscritos": "denominador_piv_mujeres_50_69"})
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

    output_path = OUTPUT / "denominador_piv_mujeres_50_69_rm_base_pago_2025.csv"
    denom.to_csv(output_path, index=False, encoding="utf-8-sig")

    sin_master = denom["IdComuna_master"].isna().sum()
    print(f"Denominador: {output_path}")
    print(f"Establecimientos con denominador: {len(denom):,}")
    print(f"Denominador RM mujeres 50-69: {denom['denominador_piv_mujeres_50_69'].sum():,}")
    print(f"Registros sin match en maestro: {sin_master:,}")


if __name__ == "__main__":
    main()
