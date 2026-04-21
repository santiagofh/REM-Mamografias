from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
COMMUNE_PATH = OUTPUT_DIR / "cobertura_mamografia_comuna_rm_2025.csv"
ESTABLISHMENT_PATH = OUTPUT_DIR / "cobertura_mamografia_establecimiento_rm_2025.csv"
CONTROL_PATH = OUTPUT_DIR / "control_calidad_mamografia_rm_2025.csv"
METADATA_PATH = OUTPUT_DIR / "metadata_mamografia_rm_2025.csv"

ACCENT_REPLACEMENTS = str.maketrans(
    {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "ñ": "n",
        "Ñ": "N",
    }
)


def slugify(text: str) -> str:
    return (
        text.lower()
        .translate(ACCENT_REPLACEMENTS)
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


@st.cache_data(show_spinner=False)
def load_communes() -> pd.DataFrame:
    if not COMMUNE_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {COMMUNE_PATH}")

    df = pd.read_csv(COMMUNE_PATH)
    required = {
        "Ano",
        "Mes",
        "IdComuna",
        "comuna_master",
        "numerador_mujeres_50_69",
        "denominador_poblacion_inscrita_validada_mujeres_50_69",
        "cobertura_mamografia_pct",
    }
    missing = required.difference(df.columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Faltan columnas requeridas: {missing_str}")

    out = df.rename(
        columns={
            "Ano": "Año",
            "comuna_master": "Comuna",
            "numerador_mujeres_50_69": "Numerador",
            "denominador_poblacion_inscrita_validada_mujeres_50_69": "Denominador",
            "cobertura_mamografia_pct": "Cobertura",
        }
    ).copy()
    for col in ["Año", "Mes", "IdComuna", "Numerador", "Denominador", "Cobertura"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["IdComuna"] = out["IdComuna"].astype("Int64").astype(str)
    out["Comuna"] = out["Comuna"].fillna("Sin comuna")
    out = out.sort_values("Cobertura", ascending=False).reset_index(drop=True)
    out.insert(0, "Ranking", range(1, len(out) + 1))
    return out


@st.cache_data(show_spinner=False)
def load_establishments() -> pd.DataFrame:
    if not ESTABLISHMENT_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {ESTABLISHMENT_PATH}")

    df = pd.read_csv(ESTABLISHMENT_PATH)
    required = {
        "IdComuna",
        "IdEstablecimiento",
        "establecimiento_master",
        "tipo_establecimiento_master",
        "comuna_master",
        "servicio_salud_master",
        "numerador_mujeres_50_69",
        "denominador_poblacion_inscrita_validada_mujeres_50_69",
        "cobertura_mamografia_pct",
        "denominador_disponible",
        "50_54",
        "55_59",
        "60_64",
        "65_69",
    }
    missing = required.difference(df.columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Faltan columnas requeridas: {missing_str}")

    out = df.rename(
        columns={
            "comuna_master": "Comuna",
            "establecimiento_master": "Establecimiento",
            "tipo_establecimiento_master": "Tipo establecimiento",
            "servicio_salud_master": "Servicio de salud",
            "numerador_mujeres_50_69": "Numerador",
            "denominador_poblacion_inscrita_validada_mujeres_50_69": "Denominador",
            "cobertura_mamografia_pct": "Cobertura",
            "denominador_disponible": "Denominador disponible",
        }
    ).copy()
    numeric_cols = [
        "IdComuna",
        "IdEstablecimiento",
        "Numerador",
        "Denominador",
        "Cobertura",
        "50_54",
        "55_59",
        "60_64",
        "65_69",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["IdComuna"] = out["IdComuna"].astype("Int64").astype(str)
    out["IdEstablecimiento"] = out["IdEstablecimiento"].astype("Int64").astype(str)
    out["Comuna"] = out["Comuna"].fillna("Sin comuna")
    out["Establecimiento"] = out["Establecimiento"].fillna("Sin nombre")
    out["Denominador disponible"] = out["Denominador disponible"].astype(str).str.lower().eq("true")
    return out


@st.cache_data(show_spinner=False)
def load_control() -> pd.DataFrame:
    if not CONTROL_PATH.exists():
        return pd.DataFrame({"tipo_control": ["Sin archivo de control"]})
    return pd.read_csv(CONTROL_PATH)


@st.cache_data(show_spinner=False)
def load_metadata() -> pd.DataFrame:
    if not METADATA_PATH.exists():
        return pd.DataFrame({"campo": ["fuente"], "valor": ["Metadata no disponible"]})
    return pd.read_csv(METADATA_PATH)


def dataframe_to_excel_bytes(
    df: pd.DataFrame,
    data_sheet_name: str = "Datos",
    prepend_sheets: dict[str, pd.DataFrame] | None = None,
    extra_sheets: dict[str, pd.DataFrame] | None = None,
) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        if prepend_sheets:
            for sheet_name, sheet_df in prepend_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        df.to_excel(writer, sheet_name=data_sheet_name[:31], index=False)
        if extra_sheets:
            for sheet_name, sheet_df in extra_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buffer.getvalue()


def format_int(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(value)):,}".replace(",", ".")


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.2f}%"


def render_provisional_badge() -> None:
    st.markdown(
        """
        <div class="provisional-badge">Datos Provisorios</div>
        """,
        unsafe_allow_html=True,
    )


def regional_summary(communes: pd.DataFrame) -> dict[str, float]:
    numerator = communes["Numerador"].sum()
    denominator = communes["Denominador"].sum()
    coverage = (numerator / denominator * 100) if denominator else 0
    return {
        "numerator": numerator,
        "denominator": denominator,
        "coverage": coverage,
        "communes": communes["Comuna"].nunique(),
        "above_regional": (communes["Cobertura"] >= coverage).sum(),
    }


def build_commune_table(communes: pd.DataFrame) -> pd.DataFrame:
    table = communes[
        ["Ranking", "Comuna", "Cobertura", "Denominador", "Numerador"]
    ].rename(
        columns={
            "Cobertura": "Cobertura (%)",
            "Denominador": "Población inscrita y validada mujeres 50-69",
            "Numerador": "Mujeres con mamografía vigente",
        }
    )
    return table.reset_index(drop=True)


def build_establishment_table(establishments: pd.DataFrame) -> pd.DataFrame:
    table = establishments[
        [
            "IdEstablecimiento",
            "Establecimiento",
            "Tipo establecimiento",
            "Servicio de salud",
            "Cobertura",
            "Denominador",
            "Numerador",
            "Denominador disponible",
        ]
    ].rename(
        columns={
            "Cobertura": "Cobertura (%)",
            "Denominador": "Población inscrita y validada mujeres 50-69",
            "Numerador": "Mujeres con mamografía vigente",
        }
    )
    return table.sort_values("Cobertura (%)", ascending=False, na_position="last").reset_index(drop=True)


def build_commune_bar_chart(communes: pd.DataFrame, regional_coverage: float) -> go.Figure:
    chart_df = communes.sort_values("Cobertura", ascending=True)
    fig = px.bar(
        chart_df,
        x="Cobertura",
        y="Comuna",
        orientation="h",
        text="Cobertura",
        color="Cobertura",
        color_continuous_scale=["#A7D3F3", "#2E75B6", "#1F4E79"],
        hover_data={
            "Cobertura": ":.2f",
            "Numerador": ":,.0f",
            "Denominador": ":,.0f",
            "Comuna": False,
        },
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.add_vline(
        x=regional_coverage,
        line_width=2,
        line_dash="dash",
        line_color="#FE6565",
        annotation_text=f"RM {regional_coverage:.2f}%",
        annotation_position="top right",
    )
    fig.update_layout(
        height=920,
        margin=dict(l=20, r=35, t=20, b=20),
        coloraxis_showscale=False,
        xaxis_title="Cobertura (%)",
        yaxis_title="Comuna",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#D9E6F2")
    fig.update_yaxes(showgrid=False)
    return fig


def build_priority_chart(communes: pd.DataFrame, regional_coverage: float) -> go.Figure:
    chart_df = communes.sort_values("Cobertura", ascending=True).head(12).copy()
    chart_df["Brecha a RM"] = regional_coverage - chart_df["Cobertura"]
    fig = px.bar(
        chart_df,
        x="Brecha a RM",
        y="Comuna",
        orientation="h",
        text="Brecha a RM",
        color="Brecha a RM",
        color_continuous_scale=["#F8C7C7", "#FE6565", "#9E2F2F"],
    )
    fig.update_traces(texttemplate="%{text:.2f} pp", textposition="outside")
    fig.update_layout(
        height=440,
        margin=dict(l=20, r=30, t=20, b=20),
        coloraxis_showscale=False,
        xaxis_title="Puntos porcentuales bajo cobertura regional",
        yaxis_title="Comuna",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F1D4D4")
    fig.update_yaxes(showgrid=False, categoryorder="total ascending")
    return fig


def build_establishment_chart(establishments: pd.DataFrame) -> go.Figure:
    chart_df = establishments.dropna(subset=["Cobertura"]).sort_values("Cobertura", ascending=True)
    if len(chart_df) > 24:
        low = chart_df.head(12)
        high = chart_df.tail(12)
        chart_df = pd.concat([low, high], ignore_index=True)
    fig = px.bar(
        chart_df,
        x="Cobertura",
        y="Establecimiento",
        orientation="h",
        text="Cobertura",
        color="Cobertura",
        color_continuous_scale=["#A7D3F3", "#2E75B6", "#1F4E79"],
        hover_data={
            "Numerador": ":,.0f",
            "Denominador": ":,.0f",
            "Cobertura": ":.2f",
            "Establecimiento": False,
        },
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(
        height=max(420, min(780, 34 * len(chart_df) + 120)),
        margin=dict(l=20, r=35, t=20, b=20),
        coloraxis_showscale=False,
        xaxis_title="Cobertura (%)",
        yaxis_title="Establecimiento",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#D9E6F2")
    fig.update_yaxes(showgrid=False)
    return fig


def build_age_chart(establishments: pd.DataFrame) -> go.Figure:
    age_totals = pd.DataFrame(
        {
            "Tramo": ["50-54", "55-59", "60-64", "65-69"],
            "Mujeres con mamografía vigente": [
                establishments["50_54"].sum(),
                establishments["55_59"].sum(),
                establishments["60_64"].sum(),
                establishments["65_69"].sum(),
            ],
        }
    )
    fig = px.bar(
        age_totals,
        x="Tramo",
        y="Mujeres con mamografía vigente",
        text="Mujeres con mamografía vigente",
        color="Tramo",
        color_discrete_sequence=["#A7D3F3", "#2E75B6", "#1F4E79", "#FE6565"],
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(
        height=390,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        xaxis_title="Tramo de edad",
        yaxis_title="Personas",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_yaxes(showgrid=True, gridcolor="#D9E6F2")
    return fig


def render_metadata_markdown(metadata: pd.DataFrame) -> None:
    values = dict(zip(metadata["campo"].astype(str), metadata["valor"].astype(str)))
    st.markdown(
        f"""
### Metodología

**Año:** {values.get("anio", "No disponible")}

**Región:** {values.get("region", "No disponible")}

**Numerador:** {values.get("numerador", "No disponible")}

**Denominador:** {values.get("denominador", "No disponible")}

**Corte principal:** {values.get("corte_principal", "No disponible")}

**Fórmula:** `{values.get("formula", "No disponible")}`

### Criterio de inclusión comunal

Los establecimientos con numerador REM-P12 se suman al numerador de su comuna. Si un establecimiento no tiene población inscrita y validada directa, queda en revisión metodológica solo para su cálculo propio; no se excluye de la cobertura comunal.

**Uso recomendado:** {values.get("uso_recomendado", "No disponible")}

**Nota:** {values.get("nota", "No disponible")}
        """
    )


def render_method_card() -> None:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-title">Lectura del indicador</div>
            <p class="soft-note"><strong>Numerador:</strong> mujeres de 50 a 69 años con mamografía vigente informadas en REM-P12 B1, Col01, corte diciembre 2025.</p>
            <p class="soft-note"><strong>Denominador:</strong> población inscrita y validada FONASA mujeres de 50 a 69 años, inscritos 2024 base de pago 2025.</p>
            <p class="soft-note"><strong>Regla comunal:</strong> todo establecimiento con numerador aporta a la cobertura de su comuna, aunque no tenga población inscrita y validada directa para calcular cobertura propia.</p>
            <p class="soft-note"><strong>Uso recomendado:</strong> cobertura comunal como salida principal; establecimiento como apoyo referencial y control.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page() -> None:
    communes = load_communes()
    establishments = load_establishments()
    control = load_control()
    summary = regional_summary(communes)
    table_df = build_commune_table(communes)

    st.title("Dashboard Cobertura Mamografía 2025")
    render_provisional_badge()
    st.caption("Cobertura vigente en mujeres de 50 a 69 años por comuna de la Región Metropolitana.")

    st.markdown("### Tabla de cobertura por comuna")
    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        height=430,
        column_config={
            "Ranking": st.column_config.NumberColumn(format="%d", width="small"),
            "Comuna": st.column_config.TextColumn(width="medium"),
            "Cobertura (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Población inscrita y validada mujeres 50-69": st.column_config.NumberColumn(format="%d"),
            "Mujeres con mamografía vigente": st.column_config.NumberColumn(format="%d"),
        },
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Cobertura regional", format_pct(summary["coverage"]))
    col2.metric("Mujeres con mamografía vigente", format_int(summary["numerator"]))
    col3.metric("Población inscrita y validada mujeres 50-69", format_int(summary["denominator"]))

    st.markdown("### Cobertura comunal")
    st.plotly_chart(build_commune_bar_chart(communes, summary["coverage"]), width="stretch")

    method_col, highlights_col = st.columns([1, 1])
    with method_col:
        render_method_card()
        st.markdown("")
    with highlights_col:
        top_row = communes.iloc[0]
        bottom_row = communes.iloc[-1]
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-card-title">Puntos destacados</div>
                <p class="soft-note"><strong>Mayor cobertura:</strong> {top_row["Comuna"]} ({format_pct(top_row["Cobertura"])}).</p>
                <p class="soft-note"><strong>Menor cobertura:</strong> {bottom_row["Comuna"]} ({format_pct(bottom_row["Cobertura"])}).</p>
                <p class="soft-note"><strong>Establecimientos en análisis:</strong> {format_int(len(establishments))} registros.</p>
                <p class="soft-note"><strong>Controles pendientes:</strong> {format_int(len(control))} registros sin población inscrita y validada directa, incluidos en el numerador comunal.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    excel_bytes = dataframe_to_excel_bytes(
        table_df,
        data_sheet_name="Cobertura comunal",
        prepend_sheets={
            "Indicadores": pd.DataFrame(
                [
                    {"Indicador": "Cobertura regional", "Valor": round(summary["coverage"], 2)},
                    {"Indicador": "Mujeres con mamografía vigente", "Valor": int(round(summary["numerator"]))},
                    {"Indicador": "Población inscrita y validada mujeres 50-69", "Valor": int(round(summary["denominator"]))},
                    {"Indicador": "Comunas sobre cobertura regional", "Valor": int(summary["above_regional"])},
                ]
            )
        },
        extra_sheets={
            "Establecimientos": build_establishment_table(establishments),
            "Control calidad": control,
            "Metadata": load_metadata(),
        },
    )
    st.download_button(
        label="Descargar resumen en Excel",
        data=excel_bytes,
        file_name="mamografia_2025_resumen_comunal.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_detail_page() -> None:
    communes = load_communes()
    establishments = load_establishments()

    st.title("Detalle comunal")
    render_provisional_badge()
    st.caption("Exploración de cobertura, establecimientos y composición por tramo de edad.")

    commune_names = communes["Comuna"].sort_values().tolist()
    selected_commune = st.selectbox("Comuna", commune_names, index=0)
    commune_row = communes[communes["Comuna"] == selected_commune].iloc[0]
    commune_establishments = establishments[establishments["Comuna"] == selected_commune].copy()

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Cobertura comunal", format_pct(commune_row["Cobertura"]))
    metric2.metric("Mujeres con mamografía vigente", format_int(commune_row["Numerador"]))
    metric3.metric("Población inscrita y validada mujeres 50-69", format_int(commune_row["Denominador"]))
    metric4.metric("Establecimientos", format_int(len(commune_establishments)))

    st.markdown("### Establecimientos")
    establishment_table = build_establishment_table(commune_establishments)
    st.dataframe(
        establishment_table,
        width="stretch",
        hide_index=True,
        height=430,
        column_config={
            "IdEstablecimiento": st.column_config.TextColumn("Código", width="small"),
            "Establecimiento": st.column_config.TextColumn(width="large"),
            "Tipo establecimiento": st.column_config.TextColumn(width="medium"),
            "Servicio de salud": st.column_config.TextColumn(width="medium"),
            "Cobertura (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Población inscrita y validada mujeres 50-69": st.column_config.NumberColumn(format="%d"),
            "Mujeres con mamografía vigente": st.column_config.NumberColumn(format="%d"),
            "Denominador disponible": st.column_config.CheckboxColumn(width="small"),
        },
    )

    if commune_establishments.empty:
        st.warning("No hay establecimientos disponibles para esta comuna.")
        return

    commune_excel = dataframe_to_excel_bytes(
        establishment_table,
        data_sheet_name="Establecimientos",
        prepend_sheets={
            "Indicadores": pd.DataFrame(
                [
                    {"Indicador": "Comuna", "Valor": selected_commune},
                    {"Indicador": "Cobertura comunal", "Valor": round(float(commune_row["Cobertura"]), 2)},
                    {"Indicador": "Mujeres con mamografía vigente", "Valor": int(round(commune_row["Numerador"]))},
                    {"Indicador": "Población inscrita y validada mujeres 50-69", "Valor": int(round(commune_row["Denominador"]))},
                ]
            )
        },
    )
    st.download_button(
        label="Descargar detalle comunal en Excel",
        data=commune_excel,
        file_name=f"mamografia_2025_{slugify(selected_commune)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_quality_page() -> None:
    metadata = load_metadata()
    rem_section_image = BASE_DIR / "assets" / "rem_p12_b1_mamografia.svg"

    st.title("Control y metodología")
    render_provisional_badge()
    st.caption("Trazabilidad metodológica del cálculo.")

    if rem_section_image.exists():
        st.markdown("### Sección REM utilizada")
        st.image(
            str(rem_section_image),
            caption="REM-P12, sección B1: mujeres con mamografía vigente en los últimos 2 años.",
        )

    render_metadata_markdown(metadata)

    metadata_excel = dataframe_to_excel_bytes(
        metadata,
        data_sheet_name="Metadata",
    )
    st.download_button(
        label="Descargar metadata",
        data=metadata_excel,
        file_name="mamografia_2025_metadata.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def get_navigation_pages():
    return [
        st.Page(render_home_page, title="Inicio", icon=":material/home:", default=True),
        st.Page(render_detail_page, title="Detalle comunal", icon=":material/location_city:", url_path="detalle-comunal"),
        st.Page(render_quality_page, title="Control y metodología", icon=":material/fact_check:", url_path="control-metodologia"),
    ]
