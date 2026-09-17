from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MAIN_FILE = BASE_DIR / '1.1. evg_programas_e_cursos.csv'
PANEL_FILE = BASE_DIR / '0. cursos_painel.xlsx'
PANEL_SHEET = 'Planilha1'
OUTPUT_FILE = BASE_DIR / '2.1. evg_programas_e_cursos.csv'


def normalize_url(value):
    if pd.isna(value):
        return ''
    return str(value).strip().lower().rstrip('/')


main_df = pd.read_csv(MAIN_FILE, sep=';', encoding='utf-8-sig')
panel_df = pd.read_excel(PANEL_FILE, sheet_name=PANEL_SHEET)

# usa a coluna de URL de cada base; se não existir, tenta a coluna que contém 'url'
main_url_col = next((c for c in main_df.columns if 'url' in str(c).lower()), 'url_curso')
panel_url_col = next((c for c in panel_df.columns if 'url' in str(c).lower()), 'url_curso')

panel_urls = {
    url for url in panel_df[panel_url_col].map(normalize_url)
    if url
}

main_df['painel'] = main_df[main_url_col].map(lambda url: 'Sim' if normalize_url(url) in panel_urls else 'Não')

main_df.to_csv(OUTPUT_FILE, sep=';', encoding='utf-8-sig', index=False)

print(f'Arquivo de saída gerado: {OUTPUT_FILE}')
print(f'Linhas com painel = Sim: {(main_df["painel"] == "Sim").sum()}')
print(f'Linhas com painel = Não: {(main_df["painel"] == "Não").sum()}')
print(f'Colunas: {list(main_df.columns)}')
