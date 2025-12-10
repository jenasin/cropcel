"""
Import dat z Excel souborů pro rok 2025 do fields.csv
"""
import pandas as pd
import os
from datetime import datetime

# Cesty
DATA_DIR = '/Users/jansaro/croptekro/data'
IMPORT_DIR = '/Users/jansaro/croptekro/2025-data'

# Načtení existujících dat
fields_df = pd.read_csv(f'{DATA_DIR}/fields.csv')
crops_df = pd.read_csv(f'{DATA_DIR}/crops.csv')
varieties_df = pd.read_csv(f'{DATA_DIR}/varieties_seed.csv')
businesses_df = pd.read_csv(f'{DATA_DIR}/businesses.csv')

print("=== NAČTENÁ DATA ===")
print(f"Fields: {len(fields_df)} záznamů")
print(f"Crops: {len(crops_df)} záznamů")
print(f"Varieties: {len(varieties_df)} záznamů")
print(f"Businesses: {len(businesses_df)} záznamů")

# Mapování podniků
BUSINESS_MAP = {
    'osek': 5,
    'zbiroh': 1,
    'stahlavy': 2,
    'šťáhlavy': 2,
    'humburky': 3,
    'zichlice': 4,
    'žichlice': 4,
    'zichlice-konv': 4,
    'zichlice-eko': 9,
    'horni-olesnice': 6,
    'horní-olešnice': 6,
    'kratonohy': 8,
}

# Mapování plodin (case insensitive)
crops_df['nazev_lower'] = crops_df['nazev'].str.lower().str.strip()
CROP_MAP = {row['nazev_lower']: int(row['id']) for _, row in crops_df.iterrows() if pd.notna(row['id'])}

# Mapování odrůd (case insensitive)
varieties_df['nazev_lower'] = varieties_df['nazev'].str.lower().str.strip()
VARIETY_MAP = {row['nazev_lower']: int(row['id']) for _, row in varieties_df.iterrows() if pd.notna(row['id'])}

print("\n=== MAPOVÁNÍ PLODIN ===")
print(f"Počet plodin: {len(CROP_MAP)}")

print("\n=== MAPOVÁNÍ ODRŮD ===")
print(f"Počet odrůd: {len(VARIETY_MAP)}")

def get_crop_id(crop_name):
    """Najde ID plodiny podle názvu"""
    if pd.isna(crop_name) or crop_name == '':
        return None
    name = str(crop_name).lower().strip()

    # Přímé mapování
    if name in CROP_MAP:
        return CROP_MAP[name]

    # Zkusit částečnou shodu
    for key, val in CROP_MAP.items():
        if name in key or key in name:
            return val

    return None

def get_variety_id(variety_name):
    """Najde ID odrůdy podle názvu"""
    if pd.isna(variety_name) or variety_name == '':
        return None
    name = str(variety_name).lower().strip()

    # Přímé mapování
    if name in VARIETY_MAP:
        return VARIETY_MAP[name]

    # Zkusit částečnou shodu
    for key, val in VARIETY_MAP.items():
        if name == key:
            return val

    # Zkusit začátek
    for key, val in VARIETY_MAP.items():
        if name.startswith(key) or key.startswith(name):
            return val

    return None

def get_next_id():
    """Získá další volné ID"""
    global fields_df
    return int(fields_df['id'].max()) + 1 if not fields_df.empty else 1

# Mapování názvů souborů na podniky
FILE_BUSINESS_MAP = {
    'Osek-export.xlsx': 5,
    'zbiroh-2025-excel.xlsx': 1,
    'stahlavy-export.xlsx': 2,
    'humburky-export.xlsx': 3,
    'zichlice-2025-konv.xlsx': 4,
    'zichlice-eko.xlsx': 9,
    'horni-olesnice.xlsx': 6,
    'kratonohy-export.xlsx': 8,
}

# Smazat existující záznamy pro rok 2025
print("\n=== MAZÁNÍ EXISTUJÍCÍCH DAT PRO ROK 2025 ===")
before_count = len(fields_df)
fields_df = fields_df[fields_df['rok_sklizne'] != 2025]
after_count = len(fields_df)
print(f"Smazáno {before_count - after_count} záznamů pro rok 2025")

# Import souborů
new_records = []
unmapped_crops = set()
unmapped_varieties = set()

for filename, business_id in FILE_BUSINESS_MAP.items():
    filepath = os.path.join(IMPORT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"CHYBÍ: {filename}")
        continue

    print(f"\n=== IMPORTUJI: {filename} (podnik ID: {business_id}) ===")

    try:
        # Načíst Excel - zkusit první sheet, přeskočit header row s "Tekro excel export"
        xl = pd.ExcelFile(filepath)
        print(f"  Sheets: {xl.sheet_names}")

        # Zkusit najít správný sheet
        df = None
        for sheet in xl.sheet_names:
            # Načíst bez headeru nejdříve, abychom zjistili strukturu
            temp_df = pd.read_excel(filepath, sheet_name=sheet, header=None)
            if len(temp_df) > 0:
                # Najít řádek s hlavičkou (obsahuje "Plodina")
                header_row = 0
                for i, row in temp_df.iterrows():
                    if any('Plodina' in str(cell) for cell in row.values):
                        header_row = i
                        break

                # Načíst znovu s korektním headerem
                df = pd.read_excel(filepath, sheet_name=sheet, header=header_row)
                print(f"  Používám sheet: {sheet}, header row: {header_row}")
                break

        if df is None or df.empty:
            print(f"  PRÁZDNÝ SOUBOR")
            continue

        print(f"  Sloupce: {list(df.columns)}")
        print(f"  Řádků: {len(df)}")

        # Zobrazit první řádky
        print(f"  Prvních 3 řádků:")
        print(df.head(3))

        # Najít relevantní sloupce - Tekro export má specifické názvy
        col_map = {}
        for col in df.columns:
            col_str = str(col)
            col_lower = col_str.lower()

            # Plodina
            if col_str == 'Plodina' or 'plodina' in col_lower:
                col_map['plodina'] = col
            # Název honu
            elif col_str == 'Název honu' or 'název honu' in col_lower:
                col_map['nazev_honu'] = col
            # Odrůda
            elif 'odrůda' in col_lower or 'odruda' in col_lower:
                col_map['odruda'] = col
            # Výměra [ha]
            elif 'výměra' in col_lower or 'vymera' in col_lower:
                col_map['vymera'] = col
            # Sklizeno [ha]
            elif 'sklizeno' in col_lower:
                col_map['sklizeno'] = col
            # Hrubá váha [t]
            elif 'hrubá váha' in col_lower or 'hruba vaha' in col_lower:
                col_map['hruba_vaha'] = col
            # Čistá váha [t]
            elif 'čistá váha' in col_lower or 'cista vaha' in col_lower:
                col_map['cista_vaha'] = col

        print(f"  Mapování sloupců: {col_map}")

        # Zpracovat řádky
        for idx, row in df.iterrows():
            # Získat hodnoty
            plodina = row.get(col_map.get('plodina', ''), '') if 'plodina' in col_map else ''
            odruda = row.get(col_map.get('odruda', ''), '') if 'odruda' in col_map else ''
            vymera = row.get(col_map.get('vymera', ''), 0) if 'vymera' in col_map else 0
            sklizeno = row.get(col_map.get('sklizeno', ''), 0) if 'sklizeno' in col_map else 0
            cista_vaha = row.get(col_map.get('cista_vaha', ''), 0) if 'cista_vaha' in col_map else 0
            hruba_vaha = row.get(col_map.get('hruba_vaha', ''), 0) if 'hruba_vaha' in col_map else 0
            nazev_honu = row.get(col_map.get('nazev_honu', ''), '') if 'nazev_honu' in col_map else ''

            # Přeskočit prázdné řádky nebo řádky bez plodiny
            if pd.isna(plodina) or plodina == '' or str(plodina).strip() == '':
                continue

            # Převést na čísla
            try:
                vymera = float(vymera) if not pd.isna(vymera) and vymera != '' else 0
                sklizeno = float(sklizeno) if not pd.isna(sklizeno) and sklizeno != '' else 0
                cista_vaha = float(cista_vaha) if not pd.isna(cista_vaha) and cista_vaha != '' else 0
                hruba_vaha = float(hruba_vaha) if not pd.isna(hruba_vaha) and hruba_vaha != '' else 0
            except:
                vymera = 0
                sklizeno = 0
                cista_vaha = 0
                hruba_vaha = 0

            # Najít ID plodiny a odrůdy
            plodina_id = get_crop_id(plodina)
            odruda_id = get_variety_id(odruda)

            if plodina and not plodina_id:
                unmapped_crops.add(str(plodina))
            if odruda and not odruda_id:
                unmapped_varieties.add(str(odruda))

            # Vytvořit záznam
            new_id = get_next_id()
            record = {
                'id': new_id,
                'vymera': vymera,
                'sklizeno': sklizeno if sklizeno > 0 else vymera,
                'cista_vaha': cista_vaha,
                'hruba_vaha': hruba_vaha,
                'plodina_id': plodina_id,
                'podnik_id': business_id,
                'datum_upravy': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'operation': 'insert',
                'datum_vznik': datetime.now().strftime('%Y-%m-%d'),
                'cislo_honu': '',
                'nazev_honu': str(nazev_honu) if not pd.isna(nazev_honu) else '',
                'odruda_id': odruda_id,
                'stmn': '',
                'datum_seti': '',
                'rok_sklizne': 2025
            }

            new_records.append(record)

            # Update next ID
            fields_df = pd.concat([fields_df, pd.DataFrame([record])], ignore_index=True)

        print(f"  Importováno {len([r for r in new_records if r['podnik_id'] == business_id])} záznamů")

    except Exception as e:
        print(f"  CHYBA: {e}")
        import traceback
        traceback.print_exc()

print(f"\n=== CELKEM IMPORTOVÁNO: {len(new_records)} záznamů ===")

if unmapped_crops:
    print(f"\n=== NENAMAPOVANÉ PLODINY ({len(unmapped_crops)}) ===")
    for crop in sorted(unmapped_crops):
        print(f"  - {crop}")

if unmapped_varieties:
    print(f"\n=== NENAMAPOVANÉ ODRŮDY ({len(unmapped_varieties)}) ===")
    for variety in sorted(unmapped_varieties):
        print(f"  - {variety}")

# Uložit
print(f"\n=== UKLÁDÁM DO fields.csv ===")
fields_df.to_csv(f'{DATA_DIR}/fields.csv', index=False)
print(f"Celkem záznamů: {len(fields_df)}")
print("HOTOVO!")
