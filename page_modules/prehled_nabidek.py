"""
Přehled nabídek - pouze pro čtení
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def show(data_manager, user, auth_manager):
    """Zobrazí přehled nabídek (read-only)"""
    st.title("🏷️ Přehled nabídek")
    st.markdown("---")

    # Načtení dat
    businesses = data_manager.get_businesses()
    odpisy = data_manager.load_csv('odpisy.csv', force_reload=True)
    nabidky = data_manager.load_csv('nabidky.csv', force_reload=True)

    # Zajistit správné datové typy
    if not odpisy.empty:
        for col in ['castka_kc', 'nabidka_kc', 'prodano_t']:
            if col in odpisy.columns:
                odpisy[col] = pd.to_numeric(odpisy[col], errors='coerce').fillna(0)

    if not nabidky.empty:
        nabidky['nabidka_kc'] = pd.to_numeric(nabidky['nabidka_kc'], errors='coerce').fillna(0)

    # Filtrovat podniky podle přiřazení uživatele
    user_podniky = user.get('podniky', [])
    if user.get('role') != 'admin' and user_podniky:
        businesses_filtered = businesses[businesses['id'].isin(user_podniky)]
    else:
        businesses_filtered = businesses

    if businesses_filtered.empty:
        st.warning("Nemáte přiřazený žádný podnik.")
        return

    # === FILTRY ===
    col1, col2 = st.columns(2)

    with col1:
        podnik_options = {row['id']: row['nazev'] for _, row in businesses_filtered.iterrows()}
        selected_podnik = st.selectbox(
            "Podnik:",
            options=list(podnik_options.keys()),
            format_func=lambda x: podnik_options[x],
            key="prehled_nabidek_podnik"
        )

    with col2:
        # Získat dostupné roky z odpisů
        if not odpisy.empty and 'rok' in odpisy.columns:
            years = sorted(odpisy['rok'].dropna().unique(), reverse=True)
            if years:
                current_year = datetime.now().year
                default_year = current_year if current_year in years else years[0]
                selected_year = st.selectbox(
                    "Rok:",
                    years,
                    index=years.index(default_year) if default_year in years else 0,
                    key="prehled_nabidek_rok"
                )
            else:
                selected_year = datetime.now().year
        else:
            selected_year = datetime.now().year

    st.markdown("---")

    # Filtrovat odpisy pro podnik a rok
    odpisy_filtered = odpisy[
        (odpisy['podnik_id'] == selected_podnik) &
        (odpisy['rok'] == selected_year)
    ] if not odpisy.empty else pd.DataFrame()

    if odpisy_filtered.empty:
        st.info(f"Žádné prodeje pro rok {selected_year}")
        return

    # Získat ID odpisů pro filtrování nabídek
    odpis_ids = odpisy_filtered['id'].tolist() if 'id' in odpisy_filtered.columns else []

    # Filtrovat nabídky
    nabidky_filtered = nabidky[nabidky['odpis_id'].isin(odpis_ids)].copy() if not nabidky.empty else pd.DataFrame()

    if nabidky_filtered.empty:
        st.info(f"Žádné nabídky pro rok {selected_year}")
        return

    # Přidat info o plodině z odpisu
    odpis_info = odpisy_filtered[['id', 'poznamka', 'castka_kc', 'datum_smlouvy', 'prodano_t']].copy()
    odpis_info.columns = ['odpis_id', 'plodina_raw', 'finalni_cena', 'datum_prodeje', 'prodano_t']
    nabidky_filtered = nabidky_filtered.merge(odpis_info, on='odpis_id', how='left')

    # Extrahovat typ plodiny
    def extract_crop_type(poznamka):
        if pd.isna(poznamka) or poznamka == '':
            return 'Ostatní'
        poznamka_lower = str(poznamka).lower()
        if 'pšenic' in poznamka_lower:
            return 'Pšenice'
        elif 'ječmen' in poznamka_lower:
            return 'Ječmen'
        elif 'řepk' in poznamka_lower:
            return 'Řepka'
        elif 'kukuřic' in poznamka_lower:
            return 'Kukuřice'
        elif 'oves' in poznamka_lower:
            return 'Oves'
        elif 'žit' in poznamka_lower:
            return 'Žito'
        else:
            return 'Ostatní'

    nabidky_filtered['plodina'] = nabidky_filtered['plodina_raw'].apply(extract_crop_type)

    # === FILTR PLODINY ===
    plodiny_list = ['Všechny'] + sorted(nabidky_filtered['plodina'].unique().tolist())
    selected_plodina = st.selectbox(
        "Plodina:",
        options=plodiny_list,
        key="prehled_nabidek_plodina"
    )

    # Filtrovat podle plodiny
    if selected_plodina != 'Všechny':
        nabidky_display = nabidky_filtered[nabidky_filtered['plodina'] == selected_plodina].copy()
    else:
        nabidky_display = nabidky_filtered.copy()

    if nabidky_display.empty:
        st.info(f"Žádné nabídky pro plodinu {selected_plodina}")
        return

    st.markdown("---")

    # === METRIKY ===
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Počet nabídek", len(nabidky_display))

    with col2:
        st.metric("Počet odběratelů", nabidky_display['odberatel'].nunique())

    with col3:
        avg_nabidka = nabidky_display['nabidka_kc'].mean()
        st.metric("Průměrná nabídka", f"{avg_nabidka:,.0f} Kč")

    with col4:
        max_nabidka = nabidky_display['nabidka_kc'].max()
        st.metric("Nejvyšší nabídka", f"{max_nabidka:,.0f} Kč")

    st.markdown("---")

    # === SLOUPCOVÝ GRAF - NABÍDKY PODLE ODBĚRATELŮ ===
    st.subheader(f"📊 Nabídky podle odběratelů - {selected_plodina if selected_plodina != 'Všechny' else 'všechny plodiny'}")

    # Seskupit nabídky podle odběratele - vzít nejvyšší nabídku od každého
    grouped_odberatele = nabidky_display.groupby('odberatel').agg({
        'nabidka_kc': 'max',
        'plodina': 'first'
    }).reset_index()
    grouped_odberatele.columns = ['Odběratel', 'Nabídka (Kč)', 'Plodina']
    grouped_odberatele = grouped_odberatele.sort_values('Nabídka (Kč)', ascending=True)

    # Sloupcový graf
    fig_bar = px.bar(
        grouped_odberatele,
        x='Nabídka (Kč)',
        y='Odběratel',
        orientation='h',
        color='Plodina' if selected_plodina == 'Všechny' else None,
        text='Nabídka (Kč)',
        title=f'Nejvyšší nabídky podle odběratelů ({selected_year})',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_bar.update_traces(texttemplate='%{text:,.0f} Kč', textposition='outside')
    fig_bar.update_layout(
        xaxis_title='Nabídka (Kč)',
        yaxis_title='',
        showlegend=True if selected_plodina == 'Všechny' else False,
        height=max(400, len(grouped_odberatele) * 50)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # === GRAF VÝVOJE NABÍDEK V ČASE ===
    st.subheader("📈 Vývoj nabídek v čase")

    nabidky_sorted = nabidky_display.sort_values('datum_nabidky').copy()
    nabidky_sorted['datum_nabidky'] = pd.to_datetime(nabidky_sorted['datum_nabidky'])

    fig_line = px.line(
        nabidky_sorted,
        x='datum_nabidky',
        y='nabidka_kc',
        color='odberatel',
        markers=True,
        title='Vývoj nabídek podle odběratelů',
        labels={'datum_nabidky': 'Datum', 'nabidka_kc': 'Nabídka (Kč)', 'odberatel': 'Odběratel'}
    )
    fig_line.update_layout(
        xaxis_title='Datum',
        yaxis_title='Nabídka (Kč)',
        yaxis=dict(tickformat=',d'),
        hovermode='x unified'
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # === POROVNÁNÍ NABÍDKA VS FINÁLNÍ CENA ===
    st.subheader("💰 Porovnání nabídek a finálních cen")

    # Seskupit podle odpisu - první a poslední nabídka
    comparison_data = []
    for odpis_id in nabidky_display['odpis_id'].unique():
        odpis_nabidky = nabidky_display[nabidky_display['odpis_id'] == odpis_id].sort_values('datum_nabidky')
        if not odpis_nabidky.empty:
            first_row = odpis_nabidky.iloc[0]
            last_row = odpis_nabidky.iloc[-1]
            comparison_data.append({
                'Plodina': first_row['plodina'],
                'Odběratel': first_row['odberatel'],
                'První nabídka': first_row['nabidka_kc'],
                'Poslední nabídka': last_row['nabidka_kc'],
                'Finální cena': first_row['finalni_cena'],
                'Vyjednáno navíc': first_row['finalni_cena'] - first_row['nabidka_kc']
            })

    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)

        # Sloupcový graf porovnání
        fig_compare = go.Figure()

        fig_compare.add_trace(go.Bar(
            name='První nabídka',
            x=comparison_df['Plodina'] + ' - ' + comparison_df['Odběratel'],
            y=comparison_df['První nabídka'],
            marker_color='#E74C3C',
            text=comparison_df['První nabídka'].apply(lambda x: f'{x:,.0f}'),
            textposition='outside'
        ))

        fig_compare.add_trace(go.Bar(
            name='Finální cena',
            x=comparison_df['Plodina'] + ' - ' + comparison_df['Odběratel'],
            y=comparison_df['Finální cena'],
            marker_color='#2ECC71',
            text=comparison_df['Finální cena'].apply(lambda x: f'{x:,.0f}'),
            textposition='outside'
        ))

        fig_compare.update_layout(
            barmode='group',
            title='První nabídka vs Finální cena',
            xaxis_title='',
            yaxis_title='Částka (Kč)',
            yaxis=dict(tickformat=',d'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        # Souhrn vyjednávání
        total_vyjednano = comparison_df['Vyjednáno navíc'].sum()
        st.success(f"✅ Celkem vyjednáno navíc: **{total_vyjednano:+,.0f} Kč**")

    st.markdown("---")

    # === TABULKA NABÍDEK ===
    st.subheader(f"📋 Seznam nabídek - {selected_plodina if selected_plodina != 'Všechny' else 'všechny plodiny'}")

    # Připravit data pro zobrazení
    display_cols = ['datum_nabidky', 'plodina', 'odberatel', 'nabidka_kc', 'finalni_cena', 'poznamka']
    display_cols = [c for c in display_cols if c in nabidky_display.columns]
    table_df = nabidky_display[display_cols].copy()
    table_df = table_df.sort_values('datum_nabidky', ascending=False)

    # Vypočítat rozdíl
    if 'nabidka_kc' in table_df.columns and 'finalni_cena' in table_df.columns:
        table_df['rozdil'] = table_df['finalni_cena'] - table_df['nabidka_kc']

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "datum_nabidky": st.column_config.DateColumn("Datum", format="YYYY-MM-DD"),
            "plodina": st.column_config.TextColumn("Plodina"),
            "odberatel": st.column_config.TextColumn("Odběratel"),
            "nabidka_kc": st.column_config.NumberColumn("Nabídka (Kč)", format="%,.0f"),
            "finalni_cena": st.column_config.NumberColumn("Finální cena (Kč)", format="%,.0f"),
            "rozdil": st.column_config.NumberColumn("Rozdíl (Kč)", format="%+,.0f"),
            "poznamka": st.column_config.TextColumn("Poznámka"),
        }
    )

    # Souhrn
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Počet nabídek: {len(table_df)}")
    with col2:
        st.caption(f"Průměrná nabídka: {table_df['nabidka_kc'].mean():,.0f} Kč")
    with col3:
        if 'rozdil' in table_df.columns:
            st.caption(f"Průměrně vyjednáno: {table_df['rozdil'].mean():+,.0f} Kč")