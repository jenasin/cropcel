"""
Dashboard stránka s přehledem - podle logiky Homepage z Nette
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.aggregations import Aggregations


def show(data_manager, user):
    """Zobrazí dashboard podle logiky Homepage::renderShow"""
    st.title("📊 Přehled sklizně")

    # Výběr roku
    fields = data_manager.get_fields()
    if not fields.empty and 'rok_sklizne' in fields.columns:
        years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True)
        if years:
            current_year = datetime.now().year
            default_year = current_year if current_year in years else years[0]
            selected_year = st.selectbox("Rok:", years, index=years.index(default_year) if default_year in years else 0)
        else:
            selected_year = datetime.now().year
            st.warning("Žádná data o letech v polích")
    else:
        selected_year = datetime.now().year

    st.markdown("---")

    # Inicializace agregací
    agg = Aggregations(data_manager)

    # Hlavní agregace podle roku - plodiny v hlavní tabulce (enable_main_table = Y)
    summary_main = agg.get_pole_summary_by_year(selected_year, 'Y')
    summary_podniky_main = agg.get_pole_podniky_summary_by_year(selected_year, 'Y')

    # Plodiny mimo hlavní tabulku (enable_main_table = N)
    summary_not_main = agg.get_pole_summary_by_year(selected_year, 'N')
    summary_podniky_not_main = agg.get_pole_podniky_summary_by_year(selected_year, 'N')

    # Filtrování podle přiřazených podniků uživatele
    user_podniky = user.get('podniky', [])
    if user.get('role') != 'admin' and user_podniky:
        if not summary_podniky_main.empty:
            summary_podniky_main = summary_podniky_main[summary_podniky_main['podnik_id'].isin(user_podniky)]
        if not summary_podniky_not_main.empty:
            summary_podniky_not_main = summary_podniky_not_main[summary_podniky_not_main['podnik_id'].isin(user_podniky)]

    # Statistiky
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_vymera = summary_main['vymera'].sum() if not summary_main.empty and 'vymera' in summary_main.columns else 0
        st.metric("Celková výměra (ha)", f"{total_vymera:.2f}")

    with col2:
        total_sklizeno = summary_main['sklizeno'].sum() if not summary_main.empty and 'sklizeno' in summary_main.columns else 0
        st.metric("Celkem sklizeno (ha)", f"{total_sklizeno:.2f}")

    with col3:
        total_cista_vaha = summary_main['cista_vaha'].sum() if not summary_main.empty and 'cista_vaha' in summary_main.columns else 0
        st.metric("Celková váha (t)", f"{total_cista_vaha:.2f}")

    with col4:
        avg_vynos = agg.calculate_vynos(total_cista_vaha, total_vymera)
        st.metric("Průměrný výnos (t/ha)", f"{avg_vynos:.2f}")

    st.markdown("---")

    # Hlavní tabulka - souhrn podle plodin
    st.subheader("🌾 Hlavní plodiny - souhrn")
    if not summary_main.empty:
        display_df = summary_main[['nazev', 'vymera', 'sklizeno', 'cista_vaha', 'cisty_vynos']].copy()
        display_df.columns = ['Plodina', 'Výměra (ha)', 'Sklizeno (ha)', 'Čistá váha (t)', 'Výnos (t/ha)']

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                "Sklizeno (ha)": st.column_config.NumberColumn(format="%.2f"),
                "Čistá váha (t)": st.column_config.NumberColumn(format="%.2f"),
                "Výnos (t/ha)": st.column_config.NumberColumn(format="%.2f")
            }
        )
    else:
        st.info("Žádná data pro hlavní plodiny")

    st.markdown("---")

    # Tabulka podle podniků a plodin
    st.subheader("🏢 Souhrn podle podniků a plodin")
    if not summary_podniky_main.empty:
        # Pivot tabulka - podniky vs plodiny
        pivot_vymera = summary_podniky_main.pivot_table(
            index='plodina',
            columns='podnik',
            values='vymera',
            fill_value=0,
            aggfunc='sum'
        )

        pivot_vynos = summary_podniky_main.pivot_table(
            index='plodina',
            columns='podnik',
            values='cisty_vynos',
            fill_value=0,
            aggfunc='mean'
        )

        tab1, tab2 = st.tabs(["Výměra (ha)", "Výnos (t/ha)"])

        with tab1:
            st.dataframe(
                pivot_vymera.round(2),
                use_container_width=True
            )

        with tab2:
            st.dataframe(
                pivot_vynos.round(2),
                use_container_width=True
            )
    else:
        st.info("Žádná data podle podniků")

    # Vedlejší plodiny
    if not summary_not_main.empty:
        st.markdown("---")
        with st.expander("📦 Vedlejší plodiny (mimo hlavní tabulku)"):
            display_df = summary_not_main[['nazev', 'vymera', 'sklizeno', 'cista_vaha', 'cisty_vynos']].copy()
            display_df.columns = ['Plodina', 'Výměra (ha)', 'Sklizeno (ha)', 'Čistá váha (t)', 'Výnos (t/ha)']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

    # Grafy
    st.markdown("---")
    st.subheader("📊 Grafy a přehledy")

    if not summary_main.empty:
        # První řada grafů - Výměra a Výnos podle plodin
        col1, col2 = st.columns(2)

        with col1:
            # Koláčový graf výměry podle plodin
            fig_pie = px.pie(
                summary_main,
                values='vymera',
                names='nazev',
                title='Výměra podle plodin',
                hole=0.3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Sloupcový graf výnosů
            fig_bar = px.bar(
                summary_main.sort_values('cisty_vynos', ascending=True),
                x='cisty_vynos',
                y='nazev',
                orientation='h',
                text='cisty_vynos',
                title='Výnos podle plodin (t/ha)',
                labels={'nazev': 'Plodina', 'cisty_vynos': 'Výnos (t/ha)'},
                color='cisty_vynos',
                color_continuous_scale='Greens'
            )
            fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_bar.update_layout(showlegend=False, xaxis=dict(range=[0, summary_main['cisty_vynos'].max() * 1.15]))
            st.plotly_chart(fig_bar, use_container_width=True)

    # Druhá řada - Souhrn podle podniků
    if not summary_podniky_main.empty:
        st.markdown("---")
        st.subheader("🏭 Přehled podle podniků")

        # Agregace podle podniků
        podniky_agg = summary_podniky_main.groupby(['podnik_id', 'podnik']).agg({
            'vymera': 'sum',
            'sklizeno': 'sum',
            'cista_vaha': 'sum'
        }).reset_index()
        podniky_agg['vynos'] = podniky_agg.apply(
            lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
            axis=1
        )

        col1, col2 = st.columns(2)

        with col1:
            # Výměra podle podniků
            fig_podnik_vymera = px.bar(
                podniky_agg.sort_values('vymera', ascending=False),
                x='podnik',
                y='vymera',
                text='vymera',
                title='Výměra podle podniků (ha)',
                labels={'podnik': 'Podnik', 'vymera': 'Výměra (ha)'},
                color='vymera',
                color_continuous_scale='Blues'
            )
            fig_podnik_vymera.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_podnik_vymera.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, podniky_agg['vymera'].max() * 1.15]))
            st.plotly_chart(fig_podnik_vymera, use_container_width=True)

        with col2:
            # Výnos podle podniků
            fig_podnik_vynos = px.bar(
                podniky_agg.sort_values('vynos', ascending=False),
                x='podnik',
                y='vynos',
                text='vynos',
                title='Průměrný výnos podle podniků (t/ha)',
                labels={'podnik': 'Podnik', 'vynos': 'Výnos (t/ha)'},
                color='vynos',
                color_continuous_scale='Oranges'
            )
            fig_podnik_vynos.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_podnik_vynos.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, podniky_agg['vynos'].max() * 1.15]))
            st.plotly_chart(fig_podnik_vynos, use_container_width=True)

        # Tabulka podniků
        st.markdown("##### Detailní přehled podniků")
        podniky_display = podniky_agg[['podnik', 'vymera', 'sklizeno', 'cista_vaha', 'vynos']].copy()
        podniky_display.columns = ['Podnik', 'Výměra (ha)', 'Sklizeno (ha)', 'Čistá váha (t)', 'Výnos (t/ha)']
        st.dataframe(
            podniky_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                "Sklizeno (ha)": st.column_config.NumberColumn(format="%.2f"),
                "Čistá váha (t)": st.column_config.NumberColumn(format="%.2f"),
                "Výnos (t/ha)": st.column_config.NumberColumn(format="%.2f")
            }
        )

    # Třetí řada - Porovnání sklizeno vs výměra
    if not summary_main.empty:
        st.markdown("---")
        st.subheader("📈 Analýza sklizně")

        col1, col2 = st.columns(2)

        with col1:
            # Scatter plot - Výměra vs Váha
            fig_scatter = px.scatter(
                summary_main,
                x='vymera',
                y='cista_vaha',
                size='cisty_vynos',
                color='nazev',
                title='Výměra vs Čistá váha (velikost = výnos)',
                labels={'vymera': 'Výměra (ha)', 'cista_vaha': 'Čistá váha (t)', 'nazev': 'Plodina'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col2:
            # Porovnání sklizeno vs výměra
            compare_df = summary_main[['nazev', 'vymera', 'sklizeno']].melt(
                id_vars='nazev',
                value_vars=['vymera', 'sklizeno'],
                var_name='Typ',
                value_name='Hodnota'
            )
            compare_df['Typ'] = compare_df['Typ'].map({'vymera': 'Výměra', 'sklizeno': 'Sklizeno'})

            fig_compare = px.bar(
                compare_df,
                x='nazev',
                y='Hodnota',
                color='Typ',
                barmode='group',
                text='Hodnota',
                title='Porovnání: Výměra vs Sklizeno (ha)',
                labels={'nazev': 'Plodina', 'Hodnota': 'Plocha (ha)'}
            )
            fig_compare.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_compare.update_layout(xaxis_tickangle=-45, yaxis=dict(range=[0, compare_df['Hodnota'].max() * 1.15]))
            st.plotly_chart(fig_compare, use_container_width=True)

    # Trend výnosů v čase (pokud máme více let)
    if not fields.empty and 'rok_sklizne' in fields.columns:
        all_years = sorted(fields['rok_sklizne'].dropna().unique())
        if len(all_years) > 1:
            st.markdown("---")
            st.subheader("📅 Trend výnosů v čase")

            # Agregace pro všechny roky
            trend_data = []
            for year in all_years:
                year_summary = agg.get_pole_summary_by_year(int(year), 'Y')
                if not year_summary.empty:
                    total_vymera = year_summary['vymera'].sum()
                    total_vaha = year_summary['cista_vaha'].sum()
                    avg_vynos = total_vaha / total_vymera if total_vymera > 0 else 0
                    trend_data.append({
                        'Rok': int(year),
                        'Výměra': total_vymera,
                        'Váha': total_vaha,
                        'Výnos': round(avg_vynos, 2)
                    })

            if trend_data:
                trend_df = pd.DataFrame(trend_data)

                col1, col2 = st.columns(2)

                with col1:
                    fig_trend_vynos = px.line(
                        trend_df,
                        x='Rok',
                        y='Výnos',
                        text='Výnos',
                        title='Průměrný výnos v čase (t/ha)',
                        markers=True
                    )
                    fig_trend_vynos.update_traces(line_color='green', line_width=3, textposition='top center', texttemplate='%{text:.2f}')
                    st.plotly_chart(fig_trend_vynos, use_container_width=True)

                with col2:
                    fig_trend_vymera = px.bar(
                        trend_df,
                        x='Rok',
                        y='Výměra',
                        text='Výměra',
                        title='Celková výměra v čase (ha)',
                        color='Výměra',
                        color_continuous_scale='Viridis'
                    )
                    fig_trend_vymera.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                    fig_trend_vymera.update_layout(yaxis=dict(range=[0, trend_df['Výměra'].max() * 1.15]))
                    st.plotly_chart(fig_trend_vymera, use_container_width=True)

                # === TABULKA: Podniky vs Roky ===
                st.markdown("---")
                st.subheader("📋 Přehled podniků podle let")

                # Načtení podniků
                businesses = data_manager.get_businesses()

                # Agregace dat pro všechny roky a podniky
                podniky_roky_data = []
                for year in all_years:
                    year_fields = fields[fields['rok_sklizne'] == year].copy()
                    if not year_fields.empty and not businesses.empty:
                        # Join s podniky
                        year_fields = year_fields.merge(
                            businesses[['id', 'nazev']].rename(columns={'nazev': 'podnik'}),
                            left_on='podnik_id',
                            right_on='id',
                            how='left'
                        )
                        # Agregace podle podniků
                        podnik_agg = year_fields.groupby('podnik').agg({
                            'vymera': 'sum',
                            'cista_vaha': 'sum'
                        }).reset_index()
                        podnik_agg['cisty_vynos'] = podnik_agg.apply(
                            lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
                            axis=1
                        )
                        podnik_agg['rok'] = int(year)
                        podniky_roky_data.append(podnik_agg)

                if podniky_roky_data:
                    all_podniky_roky = pd.concat(podniky_roky_data, ignore_index=True)

                    # Pivot tabulky pro každou metriku
                    pivot_vymera = all_podniky_roky.pivot_table(
                        index='podnik',
                        columns='rok',
                        values='vymera',
                        fill_value=0
                    )
                    pivot_produkce = all_podniky_roky.pivot_table(
                        index='podnik',
                        columns='rok',
                        values='cista_vaha',
                        fill_value=0
                    )
                    pivot_vynos = all_podniky_roky.pivot_table(
                        index='podnik',
                        columns='rok',
                        values='cisty_vynos',
                        fill_value=0
                    )

                    # Seřadit roky
                    sorted_years = sorted(pivot_vymera.columns)

                    # Vytvořit jednu velkou tabulku s multi-level headers
                    # Přejmenovat sloupce s prefixem pro každou metriku
                    vymera_cols = {y: f"Výměra (ha)|{int(y)}" for y in sorted_years}
                    vynos_cols = {y: f"Výnos (t/ha)|{int(y)}" for y in sorted_years}
                    produkce_cols = {y: f"Produkce (t)|{int(y)}" for y in sorted_years}

                    df_vymera = pivot_vymera[sorted_years].round(2).rename(columns=vymera_cols)
                    df_vynos = pivot_vynos[sorted_years].round(2).rename(columns=vynos_cols)
                    df_produkce = pivot_produkce[sorted_years].round(2).rename(columns=produkce_cols)

                    # Spojit všechny tabulky
                    combined_df = pd.concat([df_vymera, df_vynos, df_produkce], axis=1)

                    # Vytvořit MultiIndex sloupce
                    new_columns = []
                    for col in combined_df.columns:
                        parts = col.split('|')
                        new_columns.append((parts[0], parts[1]))
                    combined_df.columns = pd.MultiIndex.from_tuples(new_columns)

                    st.dataframe(combined_df, use_container_width=True)
