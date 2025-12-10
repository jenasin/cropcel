"""
AI Agent - Samostatná Streamlit aplikace
Tahá data z API endpointu každou hodinu
Spuštění: streamlit run agent_app.py --server.port 8502
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import os

# Konfigurace
st.set_page_config(
    page_title="AI Agent - Tekro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL - konfigurovatelná přes environment variable nebo sidebar
DEFAULT_API_URL = os.environ.get("TEKRO_API_URL", "http://localhost:8888")


@st.cache_data(ttl=3600)  # Cache na 1 hodinu (3600 sekund)
def fetch_all_data(api_url: str) -> dict:
    """Načte všechna data z API a rozdělí podle typu"""
    try:
        response = requests.get(f"{api_url}/data", timeout=30)
        response.raise_for_status()
        all_records = response.json()

        # Rozdělit podle _type
        data = {
            "businesses": [],
            "crops": [],
            "fields": [],
            "pozemky": [],
            "varieties_seed": [],
            "sbernamista": [],
            "sbernasrazky": [],
            "typpozemek": [],
            "roky": [],
            "sumplodiny": [],
            "userpodniky": [],
            "odpisy": []
        }

        for record in all_records:
            record_type = record.pop("_type", None)
            if record_type and record_type in data:
                data[record_type].append(record)

        # Konvertovat na DataFrame
        result = {}
        for key, records in data.items():
            if records:
                result[key] = pd.DataFrame(records)
            else:
                result[key] = pd.DataFrame()

        result["_last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["_status"] = "ok"
        return result

    except requests.exceptions.RequestException as e:
        return {
            "_status": "error",
            "_error": str(e),
            "_last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def main():
    st.title("🤖 AI Decision-Support Agent")
    st.caption("Inteligentní podpora rozhodování pro zemědělství")

    # Sidebar - konfigurace
    with st.sidebar:
        st.header("Konfigurace")
        api_url = st.text_input("API URL", value=DEFAULT_API_URL)

        if st.button("🔄 Obnovit data"):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        # Načtení dat
        data = fetch_all_data(api_url)

        if data.get("_status") == "error":
            st.error(f"Chyba: {data.get('_error')}")
            st.stop()

        st.success(f"Data načtena: {data.get('_last_update')}")
        st.caption("Automatická aktualizace každou hodinu")

        # Statistiky
        st.divider()
        st.subheader("📊 Statistiky dat")

        fields = data.get("fields", pd.DataFrame())
        if not fields.empty:
            st.metric("Záznamů polí", len(fields))
            if 'rok_sklizne' in fields.columns:
                years = sorted(fields['rok_sklizne'].dropna().unique())
                st.metric("Roky", f"{int(min(years))} - {int(max(years))}")

    # Hlavní obsah - taby
    tabs = st.tabs([
        "📋 Přehled",
        "📈 Analýza výnosů",
        "🔮 Předpověď trendů",
        "⚠️ Stabilita výnosů",
        "💬 Chat s agentem"
    ])

    with tabs[0]:
        render_overview(data)

    with tabs[1]:
        render_yield_analysis(data)

    with tabs[2]:
        render_trend_forecast(data)

    with tabs[3]:
        render_stability_analysis(data)

    with tabs[4]:
        render_chat(data)


def render_overview(data: dict):
    """Přehled dat a systému"""
    st.header("Přehled")

    fields = data.get("fields", pd.DataFrame())
    businesses = data.get("businesses", pd.DataFrame())
    crops = data.get("crops", pd.DataFrame())

    # Metriky
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Podniků", len(businesses) if not businesses.empty else 0)

    with col2:
        st.metric("Plodin", len(crops) if not crops.empty else 0)

    with col3:
        if not fields.empty and 'vymera' in fields.columns:
            st.metric("Celková výměra (ha)", f"{fields['vymera'].sum():,.0f}")
        else:
            st.metric("Celková výměra (ha)", "N/A")

    with col4:
        if not fields.empty and 'cista_vaha' in fields.columns:
            st.metric("Celková produkce (t)", f"{fields['cista_vaha'].sum():,.0f}")
        else:
            st.metric("Celková produkce (t)", "N/A")

    st.divider()

    # Info o systému
    st.subheader("O AI agentovi")
    st.markdown("""
    Tento AI agent poskytuje:
    - **Analýzu historických výnosů** - trendy a statistiky
    - **Předpověď budoucích výnosů** - lineární regrese s intervalem spolehlivosti
    - **Identifikaci nestabilních polí** - pole s vysokou variabilitou
    - **Konverzační rozhraní** - dotazy v přirozeném jazyce

    Data se automaticky aktualizují **každou hodinu** z API.
    """)


def render_yield_analysis(data: dict):
    """Analýza výnosů"""
    st.header("Analýza výnosů")

    fields = data.get("fields", pd.DataFrame())
    crops = data.get("crops", pd.DataFrame())
    businesses = data.get("businesses", pd.DataFrame())

    if fields.empty:
        st.warning("Žádná data k dispozici")
        return

    # Filtry
    col1, col2 = st.columns(2)

    with col1:
        if not businesses.empty:
            business_options = ["Všechny"] + businesses['nazev'].tolist()
            selected_business = st.selectbox("Podnik", business_options, key="yield_business")

    with col2:
        if not crops.empty:
            crop_options = ["Všechny"] + crops['nazev'].tolist()
            selected_crop = st.selectbox("Plodina", crop_options, key="yield_crop")

    # Filtrování
    filtered = fields.copy()

    if selected_business != "Všechny" and not businesses.empty:
        business_id = businesses[businesses['nazev'] == selected_business]['id'].iloc[0]
        filtered = filtered[filtered['podnik_id'] == business_id]

    if selected_crop != "Všechny" and not crops.empty:
        crop_id = crops[crops['nazev'] == selected_crop]['id'].iloc[0]
        filtered = filtered[filtered['plodina_id'] == crop_id]

    if filtered.empty or 'rok_sklizne' not in filtered.columns:
        st.info("Žádná data pro vybrané filtry")
        return

    # Agregace podle roku
    yearly = filtered.groupby('rok_sklizne').agg({
        'vymera': 'sum',
        'cista_vaha': 'sum'
    }).reset_index()
    yearly['vynos'] = yearly['cista_vaha'] / yearly['vymera']
    yearly['rok_sklizne'] = yearly['rok_sklizne'].astype(int)

    # Grafy
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yearly['rok_sklizne'],
            y=yearly['vynos'],
            mode='lines+markers+text',
            text=yearly['vynos'].round(2),
            textposition='top center',
            line=dict(color='#2E86AB', width=3)
        ))
        fig.update_layout(title='Průměrný výnos (t/ha)', xaxis_title='Rok', yaxis_title='Výnos')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=yearly['rok_sklizne'],
            y=yearly['cista_vaha'],
            marker_color='#A23B72',
            text=yearly['cista_vaha'].round(0),
            textposition='outside'
        ))
        fig.update_layout(title='Celková produkce (t)', xaxis_title='Rok', yaxis_title='Produkce')
        st.plotly_chart(fig, use_container_width=True)

    # Statistiky
    st.subheader("Statistiky")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Průměrný výnos", f"{yearly['vynos'].mean():.2f} t/ha")
    with col2:
        st.metric("Max výnos", f"{yearly['vynos'].max():.2f} t/ha")
    with col3:
        st.metric("Min výnos", f"{yearly['vynos'].min():.2f} t/ha")
    with col4:
        cv = (yearly['vynos'].std() / yearly['vynos'].mean() * 100) if yearly['vynos'].mean() > 0 else 0
        st.metric("Variabilita (CV)", f"{cv:.1f}%")


def render_trend_forecast(data: dict):
    """Předpověď trendů"""
    st.header("Předpověď trendů")

    fields = data.get("fields", pd.DataFrame())
    crops = data.get("crops", pd.DataFrame())

    if fields.empty or crops.empty:
        st.warning("Žádná data k dispozici")
        return

    col1, col2 = st.columns(2)

    with col1:
        selected_crop = st.selectbox("Plodina", crops['nazev'].tolist(), key="forecast_crop")

    with col2:
        forecast_years = st.slider("Roky predikce", 1, 5, 2)

    # Data pro plodinu
    crop_id = crops[crops['nazev'] == selected_crop]['id'].iloc[0]
    crop_fields = fields[fields['plodina_id'] == crop_id].copy()

    if crop_fields.empty or 'rok_sklizne' not in crop_fields.columns:
        st.info("Žádná data pro vybranou plodinu")
        return

    # Agregace
    yearly = crop_fields.groupby('rok_sklizne').agg({
        'vymera': 'sum',
        'cista_vaha': 'sum'
    }).reset_index()
    yearly['vynos'] = yearly['cista_vaha'] / yearly['vymera']
    yearly = yearly.sort_values('rok_sklizne')

    if len(yearly) < 2:
        st.warning("Nedostatek dat pro predikci (potřeba min. 2 roky)")
        return

    # Lineární regrese
    x = yearly['rok_sklizne'].values
    y = yearly['vynos'].values

    x_mean, y_mean = np.mean(x), np.mean(y)
    slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    intercept = y_mean - slope * x_mean

    # Predikce
    last_year = int(max(x))
    future_years = np.array([last_year + i for i in range(1, forecast_years + 1)])
    future_values = slope * future_years + intercept

    residuals = y - (slope * x + intercept)
    std_error = np.std(residuals)

    # Graf
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=yearly['rok_sklizne'], y=yearly['vynos'],
        mode='markers+lines', name='Historická data',
        line=dict(color='#2E86AB', width=2), marker=dict(size=10)
    ))

    trend_x = np.concatenate([x, future_years])
    trend_y = slope * trend_x + intercept
    fig.add_trace(go.Scatter(
        x=trend_x, y=trend_y,
        mode='lines', name='Trend',
        line=dict(color='#F18F01', width=2, dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=future_years, y=future_values,
        mode='markers+text', name='Predikce',
        text=[f"{v:.2f}" for v in future_values],
        textposition='top center',
        marker=dict(size=12, color='#C73E1D', symbol='star')
    ))

    # Interval spolehlivosti
    fig.add_trace(go.Scatter(
        x=np.concatenate([future_years, future_years[::-1]]),
        y=np.concatenate([future_values + 1.96*std_error, (future_values - 1.96*std_error)[::-1]]),
        fill='toself', fillcolor='rgba(199, 62, 29, 0.2)',
        line=dict(color='rgba(255,255,255,0)'), name='95% interval'
    ))

    fig.update_layout(
        title=f'Predikce výnosu: {selected_crop}',
        xaxis_title='Rok', yaxis_title='Výnos (t/ha)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Výsledky
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Směr trendu", "Rostoucí" if slope > 0 else "Klesající" if slope < 0 else "Stabilní")
    with col2:
        st.metric("Změna za rok", f"{slope:+.3f} t/ha")
    with col3:
        r_sq = 1 - (np.sum(residuals**2) / np.sum((y - y_mean)**2)) if np.sum((y - y_mean)**2) > 0 else 0
        st.metric("R²", f"{r_sq:.2%}")

    # Tabulka
    pred_df = pd.DataFrame({
        'Rok': future_years.astype(int),
        'Predikce (t/ha)': future_values.round(2),
        'Min (95%)': (future_values - 1.96*std_error).round(2),
        'Max (95%)': (future_values + 1.96*std_error).round(2)
    })
    st.dataframe(pred_df, use_container_width=True, hide_index=True)


def render_stability_analysis(data: dict):
    """Analýza stability výnosů"""
    st.header("Stabilita výnosů")

    fields = data.get("fields", pd.DataFrame())
    crops = data.get("crops", pd.DataFrame())

    if fields.empty:
        st.warning("Žádná data k dispozici")
        return

    # Příprava dat
    df = fields.copy()
    if 'nazev_honu' in df.columns:
        df['pole'] = df['nazev_honu'].fillna('Pole ' + df['id'].astype(str))
    else:
        df['pole'] = 'Pole ' + df['id'].astype(str)

    if not crops.empty:
        df = df.merge(crops[['id', 'nazev']], left_on='plodina_id', right_on='id', how='left', suffixes=('', '_crop'))
        df['plodina'] = df['nazev'].fillna('Neznámá')
    else:
        df['plodina'] = 'Neznámá'

    df['vynos'] = df['cista_vaha'] / df['vymera']

    # Výpočet stability
    stability = []
    for (pole, plodina), group in df.groupby(['pole', 'plodina']):
        yields = group['vynos'].dropna()
        if len(yields) >= 2:
            mean_y = yields.mean()
            cv = (yields.std() / mean_y * 100) if mean_y > 0 else 0
            stability.append({
                'Pole': pole, 'Plodina': plodina, 'Roky': len(yields),
                'Průměr': mean_y, 'CV (%)': cv,
                'Min': yields.min(), 'Max': yields.max()
            })

    if not stability:
        st.info("Nedostatek dat pro analýzu stability")
        return

    stab_df = pd.DataFrame(stability).sort_values('CV (%)', ascending=False)

    # Filtry
    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider("Zobrazit TOP", 5, 20, 10)
    with col2:
        cv_threshold = st.slider("Práh variability (%)", 0, 50, 20)

    # Graf
    top = stab_df.head(top_n)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[f"{r['Pole']}<br>({r['Plodina']})" for _, r in top.iterrows()],
        x=top['CV (%)'],
        orientation='h',
        marker_color=['#C73E1D' if cv > cv_threshold else '#2E86AB' for cv in top['CV (%)']],
        text=top['CV (%)'].round(1),
        textposition='outside'
    ))
    fig.add_vline(x=cv_threshold, line_dash="dash", line_color="orange")
    fig.update_layout(title=f'TOP {top_n} nejnestabilnějších polí', xaxis_title='CV (%)')
    st.plotly_chart(fig, use_container_width=True)

    # Statistiky
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vysoce variabilní", len(stab_df[stab_df['CV (%)'] > cv_threshold]))
    with col2:
        st.metric("Průměrná variabilita", f"{stab_df['CV (%)'].mean():.1f}%")
    with col3:
        st.metric("Stabilní (CV<15%)", len(stab_df[stab_df['CV (%)'] < 15]))

    # Tabulka
    st.subheader("Detailní přehled")
    display = stab_df.copy()
    display['Průměr'] = display['Průměr'].round(2)
    display['CV (%)'] = display['CV (%)'].round(1)
    display['Min'] = display['Min'].round(2)
    display['Max'] = display['Max'].round(2)
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_chat(data: dict):
    """Chat s AI agentem"""
    st.header("Chat s AI agentem")

    st.info("Prototyp konverzačního rozhraní. V produkci bude napojeno na ChatGPT/Claude API.")

    # Historie
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Zobrazení historie
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # Vstup
    if prompt := st.chat_input("Zadejte dotaz..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Generování odpovědi
        response = generate_response(prompt, data)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # Rychlé dotazy
    st.divider()
    st.markdown("**Rychlé dotazy:**")
    cols = st.columns(4)

    queries = [
        "Průměrný výnos?",
        "Nejlepší pole?",
        "Trend výnosů?",
        "Doporuč odrůdy"
    ]

    for i, q in enumerate(queries):
        if cols[i].button(q):
            st.session_state.chat_history.append({"role": "user", "content": q})
            response = generate_response(q, data)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

    if st.button("Vymazat historii"):
        st.session_state.chat_history = []
        st.rerun()


def generate_response(query: str, data: dict) -> str:
    """Generuje odpověď na dotaz"""
    fields = data.get("fields", pd.DataFrame())
    q = query.lower()

    if "průměr" in q or "vynos" in q or "výnos" in q:
        if not fields.empty and 'vymera' in fields.columns and 'cista_vaha' in fields.columns:
            area = fields['vymera'].sum()
            prod = fields['cista_vaha'].sum()
            avg = prod / area if area > 0 else 0
            return f"**Průměrný výnos:** {avg:.2f} t/ha\n\nCelková výměra: {area:,.0f} ha\nCelková produkce: {prod:,.0f} t"

    elif "nejlep" in q or "top" in q:
        if not fields.empty:
            df = fields.copy()
            df['vynos'] = df['cista_vaha'] / df['vymera']
            top = df.nlargest(5, 'vynos')
            result = "**TOP 5 polí podle výnosu:**\n\n"
            for i, (_, r) in enumerate(top.iterrows(), 1):
                name = r.get('nazev_honu', f"Pole {r['id']}")
                result += f"{i}. {name} - {r['vynos']:.2f} t/ha\n"
            return result

    elif "trend" in q:
        if not fields.empty and 'rok_sklizne' in fields.columns:
            yearly = fields.groupby('rok_sklizne').agg({'vymera': 'sum', 'cista_vaha': 'sum'}).reset_index()
            yearly['vynos'] = yearly['cista_vaha'] / yearly['vymera']
            if len(yearly) >= 2:
                first, last = yearly.iloc[0], yearly.iloc[-1]
                change = last['vynos'] - first['vynos']
                trend = "rostoucí" if change > 0 else "klesající" if change < 0 else "stabilní"
                return f"**Trend výnosů:** {trend}\n\n{int(first['rok_sklizne'])}: {first['vynos']:.2f} t/ha\n{int(last['rok_sklizne'])}: {last['vynos']:.2f} t/ha\nZměna: {change:+.2f} t/ha"

    elif "doporuč" in q or "odrůd" in q:
        return "**Doporučení:**\n\n1. Analyzujte historická data v záložce 'Analýza výnosů'\n2. Identifikujte stabilní pole v 'Stabilita výnosů'\n3. Používejte predikce pro plánování"

    return f"Rozumím dotazu: *{query}*\n\nZkuste:\n- Průměrný výnos?\n- Nejlepší pole?\n- Trend výnosů?\n- Doporuč odrůdy"


if __name__ == "__main__":
    main()
