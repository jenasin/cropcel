"""
Modul pro zobrazení přehledu srážek všech podniků po měsících
"""
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    render(data_manager, user)


def render(data_manager, user):
    """Vykreslí stránku s přehledem srážek"""

    # Načtení dat
    businesses = data_manager.get_businesses()
    sbernasrazky = data_manager.get_sbernasrazky()

    if sbernasrazky.empty:
        st.warning("Nejsou k dispozici žádná data o srážkách.")
        return

    # Převést datum na datetime
    sbernasrazky['Datum'] = pd.to_datetime(sbernasrazky['Datum'], errors='coerce')
    sbernasrazky['rok'] = sbernasrazky['Datum'].dt.year
    sbernasrazky['mesic'] = sbernasrazky['Datum'].dt.month
    sbernasrazky['den'] = sbernasrazky['Datum'].dt.day

    # Získat všechny roky
    all_years = sorted(sbernasrazky['rok'].dropna().unique(), reverse=True)
    all_years = [int(y) for y in all_years]

    if not all_years:
        st.warning("Nejsou k dispozici žádné roky.")
        return

    # Výběr roku
    selected_year = st.selectbox("Rok:", all_years, index=0)

    # Názvy měsíců
    mesice_nazvy = {
        1: 'Leden', 2: 'Únor', 3: 'Březen', 4: 'Duben',
        5: 'Květen', 6: 'Červen', 7: 'Červenec', 8: 'Srpen',
        9: 'Září', 10: 'Říjen', 11: 'Listopad', 12: 'Prosinec'
    }

    # Session state pro detail
    if 'srazky_detail_podnik' not in st.session_state:
        st.session_state.srazky_detail_podnik = None
    if 'srazky_detail_mesic' not in st.session_state:
        st.session_state.srazky_detail_mesic = None

    # Sloučit s názvy podniků
    if not businesses.empty:
        sbernasrazky = sbernasrazky.merge(
            businesses[['id', 'nazev', 'poradi']],
            left_on='PodnikID',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
        sbernasrazky['podnik_nazev'] = sbernasrazky['nazev'].fillna('Neznámý')
    else:
        sbernasrazky['podnik_nazev'] = 'Neznámý'
        sbernasrazky['poradi'] = 0

    # Filtrovat data pro vybraný rok
    year_data = sbernasrazky[sbernasrazky['rok'] == selected_year]

    # Pokud je vybrán detail
    if st.session_state.srazky_detail_podnik and st.session_state.srazky_detail_mesic:
        render_detail(data_manager, user, year_data, selected_year,
                     st.session_state.srazky_detail_podnik,
                     st.session_state.srazky_detail_mesic,
                     mesice_nazvy, businesses)
        return

    st.header(f"Srážky {selected_year}")

    if year_data.empty:
        st.info(f"Pro rok {selected_year} nejsou k dispozici žádná data.")
        return

    # Agregace podle podniků a měsíců
    pivot_data = year_data.groupby(['podnik_nazev', 'PodnikID', 'mesic']).agg({
        'Objem': 'sum'
    }).reset_index()

    # Seřadit podniky podle pořadí
    if not businesses.empty and 'poradi' in businesses.columns:
        podnik_order = businesses.sort_values('poradi')[['id', 'nazev']].values.tolist()
    else:
        podnik_order = [[None, name] for name in sorted(year_data['podnik_nazev'].unique())]

    # Vytvořit tabulku
    data_rows = []
    podnik_info = []

    for podnik_id, podnik_nazev in podnik_order:
        if podnik_id:
            podnik_data = pivot_data[pivot_data['PodnikID'] == podnik_id]
        else:
            podnik_data = pivot_data[pivot_data['podnik_nazev'] == podnik_nazev]

        if podnik_data.empty:
            continue

        row = {'Podnik': podnik_nazev}
        celkem = 0

        for mesic_num, mesic_nazev in mesice_nazvy.items():
            mesic_hodnota = podnik_data[podnik_data['mesic'] == mesic_num]['Objem'].sum()
            col_name = f"{mesic_nazev[:3]} [mm]"
            row[col_name] = int(mesic_hodnota)
            celkem += mesic_hodnota

        row['Celkem [mm]'] = int(celkem)
        data_rows.append(row)
        podnik_info.append((podnik_id, podnik_nazev))

    if not data_rows:
        st.info("Žádná data pro zobrazení.")
        return

    df = pd.DataFrame(data_rows)

    # Styling - zelený první sloupec, modrý Celkem sloupec
    def highlight_rows(row):
        styles = []
        for col in row.index:
            if col == 'Podnik':
                styles.append('background-color: #28a745; color: white; font-weight: bold; cursor: pointer')
            elif col == 'Celkem [mm]':
                styles.append('background-color: #2E86AB; color: white; font-weight: bold')
            else:
                styles.append('')
        return styles

    styled_df = df.style.apply(highlight_rows, axis=1)

    # Výška podle počtu řádků
    table_height = len(df) * 35 + 38

    st.info("👆 Klikněte na řádek v tabulce pro přechod na detail podniku")

    # Použít on_select pro interaktivní výběr - automaticky přejde na detail
    selection = st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=table_height,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Automatický proklik po výběru řádku
    if selection and selection.selection and selection.selection.rows:
        selected_idx = selection.selection.rows[0]
        podnik_id, podnik_nazev = podnik_info[selected_idx]
        # Použít aktuální měsíc
        current_month = datetime.now().month
        st.session_state.srazky_detail_podnik = podnik_id if podnik_id else podnik_nazev
        st.session_state.srazky_detail_mesic = current_month
        st.rerun()


def render_detail(data_manager, user, year_data, selected_year, podnik_id, mesic_num, mesice_nazvy, businesses):
    """Zobrazí detail denních srážek pro podnik a měsíc"""

    # Tlačítko zpět
    if st.button("← Zpět na přehled"):
        st.session_state.srazky_detail_podnik = None
        st.session_state.srazky_detail_mesic = None
        st.rerun()

    # Získat název podniku
    if isinstance(podnik_id, (int, float)):
        podnik_nazev = businesses[businesses['id'] == podnik_id]['nazev'].iloc[0] if not businesses.empty else 'Neznámý'
        detail_data = year_data[(year_data['PodnikID'] == podnik_id) & (year_data['mesic'] == mesic_num)]
    else:
        podnik_nazev = podnik_id
        detail_data = year_data[(year_data['podnik_nazev'] == podnik_id) & (year_data['mesic'] == mesic_num)]

    mesic_nazev = mesice_nazvy[mesic_num]

    st.header(f"Srážky - {podnik_nazev} - {mesic_nazev}")

    # Počet dnů v měsíci
    dni_v_mesici = calendar.monthrange(selected_year, mesic_num)[1]

    # Vytvořit tabulku pro dny
    data_rows = []

    # Agregace podle míst (pokud existuje)
    if 'Misto' in detail_data.columns:
        mista = detail_data['Misto'].unique()
    else:
        mista = [podnik_nazev]

    for misto in mista:
        if 'Misto' in detail_data.columns:
            misto_data = detail_data[detail_data['Misto'] == misto]
        else:
            misto_data = detail_data

        row = {'Místo': misto if pd.notna(misto) else podnik_nazev}

        for den in range(1, dni_v_mesici + 1):
            den_hodnota = misto_data[misto_data['den'] == den]['Objem'].sum()
            row[str(den)] = int(den_hodnota)

        data_rows.append(row)

    if not data_rows:
        # Prázdná tabulka
        row = {'Místo': podnik_nazev}
        for den in range(1, dni_v_mesici + 1):
            row[str(den)] = 0
        data_rows.append(row)

    df = pd.DataFrame(data_rows)

    # Styling
    def highlight_rows(row):
        styles = []
        for col in row.index:
            if col == 'Místo':
                styles.append('background-color: #28a745; color: white; font-weight: bold')
            else:
                styles.append('')
        return styles

    styled_df = df.style.apply(highlight_rows, axis=1)

    table_height = len(df) * 35 + 38

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )

    # Možnost zadávání dat (pro editora/admina)
    if user['role'] in ['admin', 'editor']:
        st.markdown("---")

        # Tlačítko pro stažení z meteostanice (pokud má podnik sensor_addr)
        actual_podnik_id = podnik_id if isinstance(podnik_id, (int, float)) else businesses[businesses['nazev'] == podnik_id]['id'].iloc[0]
        podnik_row = businesses[businesses['id'] == actual_podnik_id]

        if not podnik_row.empty and 'sensor_addr' in businesses.columns:
            sensor_addr = podnik_row.iloc[0].get('sensor_addr')
            if sensor_addr and pd.notna(sensor_addr) and sensor_addr != '':
                st.subheader("Stáhnout z meteostanice")
                if st.button("Stáhnout srážky za dnešek", key="fetch_api_rain"):
                    from utils.agdata_api import get_api_token, get_today_weather

                    if not get_api_token():
                        st.error("API token není nastaven!")
                    else:
                        with st.spinner("Stahuji dnešní data z meteostanice..."):
                            weather = get_today_weather(sensor_addr, fallback_yesterday=False)

                        if 'error' in weather:
                            st.error(f"Chyba: {weather['error']}")
                        else:
                            rain = weather.get('rain_mm')
                            api_date = weather.get('date')
                            temp = weather.get('temp_c')

                            if rain is None:
                                rain = 0.0

                            # Uložit do databáze
                            misto_mapping = {1: 30, 2: 29, 3: 28, 4: 27, 5: 26, 6: 25, 8: 42, 9: 43}
                            misto_id = misto_mapping.get(int(actual_podnik_id), 30)

                            srazky_df = data_manager.get_sbernasrazky()

                            # Zkontrolovat existující záznam
                            existing = srazky_df[
                                (srazky_df['PodnikID'] == actual_podnik_id) &
                                (srazky_df['Datum'].astype(str) == api_date)
                            ]

                            if not existing.empty:
                                idx = existing.index[0]
                                srazky_df.loc[idx, 'Objem'] = rain
                                msg = f"Aktualizováno: {api_date} - {rain:.1f} mm"
                            else:
                                new_id = srazky_df['id'].max() + 1 if not srazky_df.empty else 1
                                new_row = {
                                    'id': new_id,
                                    'MistoID': misto_id,
                                    'PodnikID': actual_podnik_id,
                                    'Datum': api_date,
                                    'Objem': rain
                                }
                                srazky_df = pd.concat([srazky_df, pd.DataFrame([new_row])], ignore_index=True)
                                msg = f"Uloženo: {api_date} - {rain:.1f} mm"

                            data_manager.save_sbernasrazky(srazky_df)

                            if temp is not None:
                                st.success(f"{msg} (teplota: {temp:.1f}°C)")
                            else:
                                st.success(msg)

                            import time
                            time.sleep(2)
                            st.rerun()

                st.markdown("---")

        st.subheader("Zadat novou srážku")

        col1, col2, col3 = st.columns(3)

        # Výchozí den = dnešek (pokud je v aktuálním měsíci)
        today = datetime.now()
        default_day = today.day if (today.month == mesic_num and today.year == selected_year) else 1
        default_day = min(default_day, dni_v_mesici)  # Zajistit, že nepřesáhne počet dnů

        with col1:
            den = st.number_input("Den:", min_value=1, max_value=dni_v_mesici, value=default_day)

        with col2:
            objem = st.number_input("Objem [mm]:", min_value=0, value=0)

        with col3:
            if st.button("Přidat srážku"):
                # Vytvořit datum
                datum = date(selected_year, mesic_num, den)

                # Zjistit PodnikID
                actual_podnik_id = podnik_id if isinstance(podnik_id, (int, float)) else businesses[businesses['nazev'] == podnik_id]['id'].iloc[0]

                # Výchozí MistoID pro podniky
                misto_mapping = {1: 30, 2: 29, 3: 28, 4: 27, 5: 26, 6: 25, 8: 42, 9: 43}
                misto_id = misto_mapping.get(int(actual_podnik_id), 30)

                # Přidat do CSV
                new_row = {
                    'id': data_manager.get_sbernasrazky()['id'].max() + 1 if not data_manager.get_sbernasrazky().empty else 1,
                    'MistoID': misto_id,
                    'PodnikID': actual_podnik_id,
                    'Datum': datum.strftime('%Y-%m-%d'),
                    'Objem': objem
                }

                srazky_df = data_manager.get_sbernasrazky()
                srazky_df = pd.concat([srazky_df, pd.DataFrame([new_row])], ignore_index=True)
                data_manager.save_sbernasrazky(srazky_df)

                st.success(f"Srážka {objem} mm pro {datum} byla přidána.")
                st.rerun()
