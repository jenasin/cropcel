"""
Odrůdy - grafy výnosů podle podniků
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


def show(data_manager, user, auth_manager=None):
    """Zobrazí stránku Odrůdy s grafy výnosů"""
    st.title("📉 Odrůdy - přehled výnosů")

    # Načtení dat
    fields = data_manager.get_fields()
    businesses = data_manager.get_businesses()
    crops = data_manager.get_crops()
    varieties = data_manager.get_varieties_seed()

    if fields.empty:
        st.warning("Žádná data o polích")
        return

    # === SELEKTORY ROKU A PLODINY ===
    col1, col2 = st.columns(2)

    with col1:
        # Výběr roku
        if 'rok_sklizne' in fields.columns:
            years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True)
            if years:
                current_year = datetime.now().year
                default_year = current_year if current_year in years else years[0]
                selected_year = st.selectbox(
                    "Rok:",
                    years,
                    index=years.index(default_year) if default_year in years else 0
                )
            else:
                st.warning("Žádná data o letech")
                return
        else:
            st.warning("Chybí sloupec rok_sklizne")
            return

    # Filtrovat podle roku
    fields_year = fields[fields['rok_sklizne'] == selected_year].copy()

    if fields_year.empty:
        st.info(f"Žádná data pro rok {selected_year}")
        return

    # Filtrování podle přiřazených podniků uživatele
    user_podniky = user.get('podniky', [])
    if user.get('role') != 'admin' and user_podniky:
        fields_year = fields_year[fields_year['podnik_id'].isin(user_podniky)]

    # Připojit názvy podniků
    if not businesses.empty:
        fields_year = fields_year.merge(
            businesses[['id', 'nazev']].rename(columns={'nazev': 'podnik_nazev'}),
            left_on='podnik_id',
            right_on='id',
            how='left',
            suffixes=('', '_business')
        )

    # Připojit názvy plodin
    if not crops.empty:
        fields_year = fields_year.merge(
            crops[['id', 'nazev']].rename(columns={'nazev': 'plodina_nazev'}),
            left_on='plodina_id',
            right_on='id',
            how='left',
            suffixes=('', '_crop')
        )

    with col2:
        # Výběr plodiny - seřazeno podle sloupce 'poradi' z tabulky crops
        if 'plodina_nazev' in fields_year.columns:
            plodiny_v_datech = fields_year['plodina_nazev'].dropna().unique().tolist()

            if plodiny_v_datech:
                # Seřadit plodiny podle 'poradi' z tabulky crops
                if not crops.empty and 'poradi' in crops.columns:
                    # Vytvořit mapování nazev -> poradi
                    crops_sorted = crops.copy()
                    # Nahradit NaN hodnoty vysokým číslem aby byly na konci
                    crops_sorted['poradi'] = pd.to_numeric(crops_sorted['poradi'], errors='coerce').fillna(9999)
                    crops_sorted = crops_sorted.sort_values('poradi')

                    # Seřadit plodiny podle pořadí
                    plodiny_sorted = []
                    for _, row in crops_sorted.iterrows():
                        if row['nazev'] in plodiny_v_datech:
                            plodiny_sorted.append(row['nazev'])

                    # Přidat plodiny které nejsou v tabulce crops na konec
                    for p in plodiny_v_datech:
                        if p not in plodiny_sorted:
                            plodiny_sorted.append(p)

                    plodiny = plodiny_sorted
                else:
                    plodiny = sorted(plodiny_v_datech)

                selected_plodina = st.selectbox(
                    "Plodina:",
                    plodiny,
                    key="plodina_select"
                )
            else:
                st.warning("Žádné plodiny v datech")
                return
        else:
            st.warning("Chybí informace o plodinách")
            return

    # Filtrovat podle plodiny
    fields_filtered = fields_year[fields_year['plodina_nazev'] == selected_plodina]

    if fields_filtered.empty:
        st.info(f"Žádná data pro plodinu {selected_plodina} v roce {selected_year}")
        return

    st.markdown("---")

    # Agregace dat podle podniků
    if 'hruba_vaha' in fields_filtered.columns and 'cista_vaha' in fields_filtered.columns and 'vymera' in fields_filtered.columns:
        agg_data = fields_filtered.groupby('podnik_nazev').agg({
            'hruba_vaha': 'sum',
            'cista_vaha': 'sum',
            'vymera': 'sum'
        }).reset_index()

        # Výpočet výnosů
        agg_data['hruby_vynos'] = agg_data.apply(
            lambda row: round(row['hruba_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
            axis=1
        )
        agg_data['cisty_vynos'] = agg_data.apply(
            lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
            axis=1
        )

        # === 4 GRAFY POD SEBOU ===

        # --- HRUBÁ PRODUKCE ---
        st.subheader("📦 Hrubá produkce")
        fig_hruba_prod = px.bar(
            agg_data.sort_values('hruba_vaha', ascending=False),
            x='podnik_nazev',
            y='hruba_vaha',
            text='hruba_vaha',
            title=f'{selected_plodina} - {selected_year}',
            labels={'podnik_nazev': 'Podnik', 'hruba_vaha': 'Hrubá produkce (t)'},
            color='hruba_vaha',
            color_continuous_scale='Oranges'
        )
        fig_hruba_prod.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_hruba_prod.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, agg_data['hruba_vaha'].max() * 1.15]))
        st.plotly_chart(fig_hruba_prod, use_container_width=True)

        with st.expander("📊 Data"):
            display_df = agg_data[['podnik_nazev', 'hruba_vaha']].copy()
            display_df.columns = ['Podnik', 'Hrubá produkce (t)']
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                       column_config={"Hrubá produkce (t)": st.column_config.NumberColumn(format="%.2f")})

        st.markdown("---")

        # --- ČISTÁ PRODUKCE ---
        st.subheader("📦 Čistá produkce")
        fig_cista_prod = px.bar(
            agg_data.sort_values('cista_vaha', ascending=False),
            x='podnik_nazev',
            y='cista_vaha',
            text='cista_vaha',
            title=f'{selected_plodina} - {selected_year}',
            labels={'podnik_nazev': 'Podnik', 'cista_vaha': 'Čistá produkce (t)'},
            color='cista_vaha',
            color_continuous_scale='Greens'
        )
        fig_cista_prod.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_cista_prod.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, agg_data['cista_vaha'].max() * 1.15]))
        st.plotly_chart(fig_cista_prod, use_container_width=True)

        with st.expander("📊 Data"):
            display_df = agg_data[['podnik_nazev', 'cista_vaha']].copy()
            display_df.columns = ['Podnik', 'Čistá produkce (t)']
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                       column_config={"Čistá produkce (t)": st.column_config.NumberColumn(format="%.2f")})

        st.markdown("---")

        # --- HRUBÝ VÝNOS ---
        st.subheader("📈 Hrubý výnos")
        fig_hruby_vynos = px.bar(
            agg_data.sort_values('hruby_vynos', ascending=False),
            x='podnik_nazev',
            y='hruby_vynos',
            text='hruby_vynos',
            title=f'{selected_plodina} - {selected_year}',
            labels={'podnik_nazev': 'Podnik', 'hruby_vynos': 'Hrubý výnos (t/ha)'},
            color='hruby_vynos',
            color_continuous_scale='Reds'
        )
        fig_hruby_vynos.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_hruby_vynos.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, agg_data['hruby_vynos'].max() * 1.15]))
        st.plotly_chart(fig_hruby_vynos, use_container_width=True)

        with st.expander("📊 Data"):
            display_df = agg_data[['podnik_nazev', 'vymera', 'hruba_vaha', 'hruby_vynos']].copy()
            display_df.columns = ['Podnik', 'Výměra (ha)', 'Hrubá váha (t)', 'Hrubý výnos (t/ha)']
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                       column_config={
                           "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                           "Hrubá váha (t)": st.column_config.NumberColumn(format="%.2f"),
                           "Hrubý výnos (t/ha)": st.column_config.NumberColumn(format="%.2f")
                       })

        st.markdown("---")

        # --- ČISTÝ VÝNOS ---
        st.subheader("📈 Čistý výnos")
        fig_cisty_vynos = px.bar(
            agg_data.sort_values('cisty_vynos', ascending=False),
            x='podnik_nazev',
            y='cisty_vynos',
            text='cisty_vynos',
            title=f'{selected_plodina} - {selected_year}',
            labels={'podnik_nazev': 'Podnik', 'cisty_vynos': 'Čistý výnos (t/ha)'},
            color='cisty_vynos',
            color_continuous_scale='Blues'
        )
        fig_cisty_vynos.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_cisty_vynos.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, agg_data['cisty_vynos'].max() * 1.15]))
        st.plotly_chart(fig_cisty_vynos, use_container_width=True)

        with st.expander("📊 Data"):
            display_df = agg_data[['podnik_nazev', 'vymera', 'cista_vaha', 'cisty_vynos']].copy()
            display_df.columns = ['Podnik', 'Výměra (ha)', 'Čistá váha (t)', 'Čistý výnos (t/ha)']
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                       column_config={
                           "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                           "Čistá váha (t)": st.column_config.NumberColumn(format="%.2f"),
                           "Čistý výnos (t/ha)": st.column_config.NumberColumn(format="%.2f")
                       })

        # === VÝNOSY PODLE ODRŮD ===
        st.markdown("---")
        st.subheader("🌱 Výnosy podle odrůd")

        # Připojit názvy odrůd k filtrovaným polím
        if not varieties.empty and 'odruda_id' in fields_filtered.columns:
            fields_with_varieties = fields_filtered.merge(
                varieties[['id', 'nazev']].rename(columns={'nazev': 'odruda_nazev'}),
                left_on='odruda_id',
                right_on='id',
                how='left',
                suffixes=('', '_variety')
            )

            # Filtrovat pouze záznamy s odrůdou
            fields_with_varieties = fields_with_varieties[fields_with_varieties['odruda_nazev'].notna()]

            if not fields_with_varieties.empty:
                # Agregace podle odrůdy
                odruda_agg = fields_with_varieties.groupby('odruda_nazev').agg({
                    'hruba_vaha': 'sum',
                    'cista_vaha': 'sum',
                    'vymera': 'sum'
                }).reset_index()

                # Výpočet výnosů
                odruda_agg['hruby_vynos'] = odruda_agg.apply(
                    lambda row: round(row['hruba_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
                    axis=1
                )
                odruda_agg['cisty_vynos'] = odruda_agg.apply(
                    lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
                    axis=1
                )

                # Graf čistého výnosu podle odrůd
                fig_odruda = px.bar(
                    odruda_agg.sort_values('cisty_vynos', ascending=False),
                    x='odruda_nazev',
                    y='cisty_vynos',
                    text='cisty_vynos',
                    title=f'Čistý výnos podle odrůd - {selected_plodina} ({selected_year})',
                    labels={'odruda_nazev': 'Odrůda', 'cisty_vynos': 'Čistý výnos (t/ha)'},
                    color='cisty_vynos',
                    color_continuous_scale='Viridis'
                )
                fig_odruda.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_odruda.update_layout(showlegend=False, xaxis_tickangle=-45, yaxis=dict(range=[0, odruda_agg['cisty_vynos'].max() * 1.15]))
                st.plotly_chart(fig_odruda, use_container_width=True)

                with st.expander("📊 Data odrůd"):
                    display_odruda = odruda_agg[['odruda_nazev', 'vymera', 'hruba_vaha', 'cista_vaha', 'hruby_vynos', 'cisty_vynos']].copy()
                    display_odruda.columns = ['Odrůda', 'Výměra (ha)', 'Hrubá produkce (t)', 'Čistá produkce (t)', 'Hrubý výnos (t/ha)', 'Čistý výnos (t/ha)']
                    st.dataframe(display_odruda, use_container_width=True, hide_index=True,
                               column_config={
                                   "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                                   "Hrubá produkce (t)": st.column_config.NumberColumn(format="%.2f"),
                                   "Čistá produkce (t)": st.column_config.NumberColumn(format="%.2f"),
                                   "Hrubý výnos (t/ha)": st.column_config.NumberColumn(format="%.2f"),
                                   "Čistý výnos (t/ha)": st.column_config.NumberColumn(format="%.2f")
                               })
            else:
                st.info(f"Žádné odrůdy pro plodinu {selected_plodina} v roce {selected_year}")
        else:
            st.info("Žádná data o odrůdách")

        # === SOUHRNNÁ TABULKA ===
        st.markdown("---")
        st.subheader("📋 Souhrnná tabulka")

        summary_df = agg_data[['podnik_nazev', 'vymera', 'hruba_vaha', 'cista_vaha', 'hruby_vynos', 'cisty_vynos']].copy()
        summary_df.columns = ['Podnik', 'Výměra (ha)', 'Hrubá produkce (t)', 'Čistá produkce (t)', 'Hrubý výnos (t/ha)', 'Čistý výnos (t/ha)']

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                "Hrubá produkce (t)": st.column_config.NumberColumn(format="%.2f"),
                "Čistá produkce (t)": st.column_config.NumberColumn(format="%.2f"),
                "Hrubý výnos (t/ha)": st.column_config.NumberColumn(format="%.2f"),
                "Čistý výnos (t/ha)": st.column_config.NumberColumn(format="%.2f")
            }
        )

        # Celkové statistiky
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Celková výměra", f"{agg_data['vymera'].sum():.2f} ha")
        with col2:
            st.metric("Hrubá produkce", f"{agg_data['hruba_vaha'].sum():.2f} t")
        with col3:
            st.metric("Čistá produkce", f"{agg_data['cista_vaha'].sum():.2f} t")
        with col4:
            total_vymera = agg_data['vymera'].sum()
            total_cista = agg_data['cista_vaha'].sum()
            avg_vynos = total_cista / total_vymera if total_vymera > 0 else 0
            st.metric("Průměrný čistý výnos", f"{avg_vynos:.2f} t/ha")

    else:
        st.warning("Chybí potřebné sloupce pro výpočet (hruba_vaha, cista_vaha, vymera)")
