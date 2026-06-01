import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="MarginAnalyzer - Break-even Analysis", layout="wide")
st.write("# MarginAnalyzer: Análisis de Punto de Equilibrio")

archivo_cargado = st.file_uploader(
    label="Sube tu archivo CSV", type=".csv", accept_multiple_files=False
)


@st.cache_data
def cargar_archivo_csv(fichero):
    df = pd.read_csv(fichero, delimiter=",", encoding="utf-8")
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df


def calcular_costo_variable_unitario(row, precio_venta):
    try:
        valor = float(row["Valor"])
        consumo = float(row["Consumo_Unitario"])
        if str(row["Base_Referencia"]).lower() == "precio_venta":
            return valor * precio_venta * consumo
        else:
            base = float(row["Base_Referencia"])
            return (valor / base) * consumo
    except (ValueError, ZeroDivisionError):
        return 0.0


def generar_grafico_punto_equilibrio(
    costo_variable_unitario,
    costos_fijos,
    precio_venta,
    cantidad_equilibrio,
    punto_cierre,
    cantidad_objetivo,
    key_grafico,
):
    # Definir limite X
    # Asegurarnos de que el límite del eje X sea suficiente para ver todos los puntos
    puntos_importantes = [cantidad_equilibrio]
    if cantidad_objetivo: puntos_importantes.append(cantidad_objetivo)
    if punto_cierre: puntos_importantes.append(punto_cierre)
    
    lim_ref = max(puntos_importantes) if puntos_importantes else 0
    limite_superior_eje_x = max(300, int(lim_ref * 1.5) if lim_ref > 0 else 300)
    rango_cantidades = np.arange(1, limite_superior_eje_x, 1)

    figura = go.Figure()

    # 1. Costo Variable Total (Pedido por usuario)
    figura.add_trace(
        go.Scatter(
            x=rango_cantidades,
            y=rango_cantidades * costo_variable_unitario,
            name="Costo Variable Total",
            mode="lines",
            line=dict(color="orange"),
        )
    )

    # 2. Costo Fijo
    figura.add_trace(
        go.Scatter(
            x=rango_cantidades,
            y=np.full_like(rango_cantidades, costos_fijos),
            name="Costo Fijo",
            mode="lines",
            line=dict(dash="dash", color="gray"),
        )
    )

    # 3. Costo Total
    figura.add_trace(
        go.Scatter(
            x=rango_cantidades,
            y=costos_fijos + (rango_cantidades * costo_variable_unitario),
            name="Costo Total",
            mode="lines",
            line=dict(color="red"),
        )
    )

    # 4. Ingreso Total
    figura.add_trace(
        go.Scatter(
            x=rango_cantidades,
            y=rango_cantidades * precio_venta,
            name="Ingreso Total",
            mode="lines",
            line=dict(color="green"),
            fill='tonexty', # Sombreado entre Ingreso y Costo Total
            fillcolor='rgba(0, 255, 0, 0.1)', # Verde muy transparente para ganancias
        )
    )
    
    # Agregar sombreado para zona de pérdidas (donde Costo Total > Ingreso)
    # Para hacer esto en Plotly de forma limpia, añadimos una traza invisible
    # que represente el área de pérdida.
    figura.add_trace(
        go.Scatter(
            x=rango_cantidades,
            y=np.maximum(costos_fijos + (rango_cantidades * costo_variable_unitario), rango_cantidades * precio_venta),
            fill='tonexty',
            fillcolor='rgba(255, 0, 0, 0.1)', # Rojo muy transparente para pérdidas
            mode='none',
            name='Zona de Pérdidas/Ganancias',
            showlegend=False
        )
    )

    # Puntos destacados
    if cantidad_equilibrio > 0:
        figura.add_trace(
            go.Scatter(
                x=[cantidad_equilibrio],
                y=[cantidad_equilibrio * precio_venta],
                name="Punto de Equilibrio",
                mode="markers",
                marker=dict(size=12, color="blue"),
            )
        )

    if punto_cierre > 0:
        figura.add_trace(
            go.Scatter(
                x=[punto_cierre],
                y=[punto_cierre * precio_venta],
                name="Punto de Cierre",
                mode="markers",
                marker=dict(size=10, color="black", symbol="x"),
            )
        )

    if cantidad_objetivo and cantidad_objetivo > 0:
        figura.add_trace(
            go.Scatter(
                x=[cantidad_objetivo],
                y=[cantidad_objetivo * precio_venta],
                name="Cantidad Objetivo",
                mode="markers",
                marker=dict(size=12, color="gold", symbol="star"),
            )
        )

    figura.update_layout(
        title="Análisis Gráfico",
        xaxis_title="Unidades",
        yaxis_title="Dinero ($)",
        hovermode="x unified",
    )
    st.plotly_chart(figura, use_container_width=True, key=key_grafico)


def mostrar_verificacion_numerica(q, pv, cvu, cf):
    ingresos = q * pv
    costos_v = q * cvu
    margen_c = ingresos - costos_v
    resultado = margen_c - cf

    data = {
        "Concepto": [
            "(+) Ventas Totales",
            "(-) Costos Variables Totales",
            "(=) Margen de Contribución Total",
            "(-) Costos Fijos Totales",
            "(=) Resultado Operativo",
        ],
        "Valor ($)": [
            f"{ingresos:,.2f}",
            f"{costos_v:,.2f}",
            f"{margen_c:,.2f}",
            f"{cf:,.2f}",
            f"{resultado:,.2f}",
        ],
    }
    st.table(pd.DataFrame(data))


if archivo_cargado is not None:
    df = cargar_archivo_csv(archivo_cargado)
    with st.expander("Vista previa de los datos"):
        st.dataframe(df, use_container_width=True)

    try:
        precio_venta_base = float(df[df["Tipo"] == "Ingreso"]["Valor"].iloc[0])
        df_variables = df[df["Tipo"] == "Variable"].copy()
        df_variables["Costo_Unitario"] = df_variables.apply(
            lambda r: calcular_costo_variable_unitario(r, precio_venta_base), axis=1
        )
        cvu_total_base = df_variables["Costo_Unitario"].sum()
        df_fijos = df[df["Tipo"] == "Fijo"].copy()
        cf_base = df_fijos["Valor"].sum()
        cf_erogable_base = df_fijos[df_fijos["Es_Erogable"] == "Si"]["Valor"].sum()
        contrib_base = precio_venta_base - cvu_total_base
    except Exception as e:
        st.error(f"Error al procesar el CSV: {e}")
        st.stop()

    tab1, tab2 = st.tabs(["Análisis de Situación", "Simulador"])

    with tab1:
        st.subheader("Indicadores de Gestión")

        # Cálculos de Gestión
        cantidad_equilibrio_base = cf_base / contrib_base
        cantidad_cierre_base = cf_erogable_base / contrib_base
        # Meta de utilidad de 700.000
        utilidad_meta_valor = 700000
        cantidad_meta_valor_base = (cf_base + utilidad_meta_valor) / contrib_base
        # Meta de utilidad 20% sobre costos
        margen_meta_porcentaje = 0.20
        denominador_meta = precio_venta_base - (cvu_total_base * (1 + margen_meta_porcentaje))
        if denominador_meta > 0:
            cantidad_meta_porcentaje_base = (cf_base * (1 + margen_meta_porcentaje)) / denominador_meta
        else:
            cantidad_meta_porcentaje_base = None

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Punto de Equilibrio", f"{cantidad_equilibrio_base:.2f} u.")
        col1.write(f"${cantidad_equilibrio_base * precio_venta_base:,.2f}")

        col2.metric("Punto de Cierre", f"{cantidad_cierre_base:.2f} u.")
        col2.write(f"${cantidad_cierre_base * precio_venta_base:,.2f}")

        col3.metric(f"Meta de ${utilidad_meta_valor:,.0f}", f"{cantidad_meta_valor_base:.2f} u.")
        col3.write(f"${cantidad_meta_valor_base * precio_venta_base:,.2f}")

        if cantidad_meta_porcentaje_base:
            col4.metric("Meta 20% utilidad", f"{cantidad_meta_porcentaje_base:.2f} u.")
            col4.write(f"${cantidad_meta_porcentaje_base * precio_venta_base:,.2f}")
        else:
            st.error(
                "⚠️ La utilidad del 20% sobre costos es inalcanzable."
            )

        # Gráfico
        generar_grafico_punto_equilibrio(
            cvu_total_base,
            cf_base,
            precio_venta_base,
            cantidad_equilibrio_base,
            cantidad_cierre_base,
            cantidad_meta_valor_base,
            "graph_base",
        )

        # Verificación Numérica (Escenario: 180 remeras)
        st.divider()
        st.subheader("Verificación Operativa (Ventas Presupuestadas: 180 remeras)")
        mostrar_verificacion_numerica(180, precio_venta_base, cvu_total_base, cf_base)

        margen_seguridad_porcentaje = (180 - cantidad_equilibrio_base) / 180
        st.info(f"**Margen de Seguridad:** {margen_seguridad_porcentaje * 100:.2f}%")

    with tab2:
        st.subheader("Simulador Dinámico")
        col_sim1, col_sim2 = st.columns(2)

        with col_sim1:
            sim_precio_venta = st.number_input(
                "Precio de Venta", value=float(precio_venta_base), step=100.0
            )
            sim_costos_fijos = st.number_input(
                "Costos Fijos Totales", value=float(cf_base), step=1000.0
            )
            
        with col_sim2:
            tipo_objetivo = st.selectbox(
                "Tipo de Meta de Utilidad",
                ["Valor Nominal ($)", "Porcentaje sobre Costos (%)"]
            )
            
            if tipo_objetivo == "Valor Nominal ($)":
                sim_utilidad_meta = st.number_input("Utilidad Deseada ($)", value=0.0, step=10000.0)
                sim_margen_meta = 0.0
            else:
                sim_margen_meta = st.slider("Utilidad Deseada sobre Costos (%)", 0, 100, 20, key="slider_utilidad") / 100.0
                sim_utilidad_meta = 0.0

            # Recalcular CVU para impuestos % PV
            df_variables_sim = df[df["Tipo"] == "Variable"].copy()
            sim_cvu_total = df_variables_sim.apply(
                lambda r: calcular_costo_variable_unitario(r, sim_precio_venta), axis=1
            ).sum()
            sim_contribucion_marginal = sim_precio_venta - sim_cvu_total

        if sim_contribucion_marginal <= 0:
            st.error("Margen de contribución negativo.")
        else:
            sim_cantidad_equilibrio = sim_costos_fijos / sim_contribucion_marginal
            sim_cantidad_meta_valor = (sim_costos_fijos + sim_utilidad_meta) / sim_contribucion_marginal

            denominador_sim = sim_precio_venta - (sim_cvu_total * (1 + sim_margen_meta))
            sim_cantidad_meta_porcentaje = (sim_costos_fijos * (1 + sim_margen_meta)) / denominador_sim if denominador_sim > 0 else None

            # Definir qué punto objetivo mostrar en el gráfico según el selectbox
            if tipo_objetivo == "Valor Nominal ($)":
                sim_cantidad_grafico_objetivo = sim_cantidad_meta_valor if sim_utilidad_meta > 0 else 0
            else:
                sim_cantidad_grafico_objetivo = sim_cantidad_meta_porcentaje if sim_margen_meta > 0 else 0

            st.write(f"**Equilibrio:** {sim_cantidad_equilibrio:.2f} u. | ${sim_cantidad_equilibrio * sim_precio_venta:,.2f}")
            
            if tipo_objetivo == "Valor Nominal ($)":
                st.write(
                    f"**Con Utilidad \$:** {sim_cantidad_meta_valor:.2f} u. | ${sim_cantidad_meta_valor * sim_precio_venta:,.2f}"
                )
            else:
                if sim_cantidad_meta_porcentaje:
                    st.write(
                        f"**Cantidad para {sim_margen_meta * 100:.0f}% utilidad:** {sim_cantidad_meta_porcentaje:.2f} unidades | ${sim_cantidad_meta_porcentaje * sim_precio_venta:,.2f}"
                    )
                else:
                    st.warning(
                        f"La utilidad del {sim_margen_meta * 100:.0f}% es inalcanzable."
                    )

            generar_grafico_punto_equilibrio(
                sim_cvu_total, sim_costos_fijos, sim_precio_venta, sim_cantidad_equilibrio, 0, sim_cantidad_grafico_objetivo, "graph_sim_din"
            )

            if st.checkbox("Mostrar Verificación de Simulación"):
                sim_cantidad_verificar = st.number_input("Cantidad a verificar", value=float(sim_cantidad_equilibrio))
                mostrar_verificacion_numerica(sim_cantidad_verificar, sim_precio_venta, sim_cvu_total, sim_costos_fijos)
