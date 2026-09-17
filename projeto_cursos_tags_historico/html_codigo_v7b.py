import pandas as pd
file_path = '/mnt/data/Cursos_EVG_Final_Tags_v7.xlsx'
df = pd.read_excel(file_path, sheet_name='Tabela Principal')
print("Columns:", df.columns.tolist())
print("Non-empty tags_aie_rev count:", (df['tags_aie_rev'] != '').sum())