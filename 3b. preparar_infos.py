from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / '3.1. evg_programas_e_cursos_infos.xlsx'
OUTPUT_FILE = BASE_DIR / '3b.1. evg_programas_e_cursos_infos.xlsx'


def tem_informacao(valor):
    return pd.notna(valor) and str(valor).strip() != ''


def consolidar_linha(linha, indice_f, indice_g):
    if not tem_informacao(linha.iloc[indice_g]):
        return linha

    indices_preenchidos = [
        indice
        for indice in range(indice_f, len(linha))
        if tem_informacao(linha.iloc[indice])
    ]
    if not indices_preenchidos:
        return linha

    ultimo_indice = max(indices_preenchidos)
    valores = [
        str(linha.iloc[indice]).strip()
        for indice in range(indice_f, ultimo_indice + 1)
        if tem_informacao(linha.iloc[indice])
    ]
    linha.iloc[indice_f] = ' | '.join(valores)
    linha.iloc[indice_f + 1:ultimo_indice + 1] = pd.NA
    return linha


print(f'Lendo: {INPUT_FILE.name}')
df = pd.read_excel(INPUT_FILE, sheet_name=0)

if df.empty:
    raise ValueError('A planilha de origem está vazia.')

coluna_a = df.columns[0]
linhas_antes_filtro_numerico = len(df)
valores_numericos = pd.to_numeric(df[coluna_a], errors='coerce')
df = df[valores_numericos.notna()].copy()
linhas_excluidas_nao_numericas = linhas_antes_filtro_numerico - len(df)

if 'nome_curso' not in df.columns:
    raise KeyError("A coluna 'nome_curso' não foi encontrada na planilha de origem.")

indice_f = 5
indice_g = 6
if len(df.columns) <= indice_g:
    raise ValueError('A planilha não possui as colunas F e G necessárias.')

linhas_iniciais = len(df)
df = df[df['nome_curso'].map(tem_informacao)].copy()
linhas_excluidas = linhas_iniciais - len(df)

linhas_com_g = int(df.iloc[:, indice_g].map(tem_informacao).sum())
if linhas_com_g:
    df = df.apply(
        consolidar_linha,
        axis=1,
        indice_f=indice_f,
        indice_g=indice_g,
    )

df = df.loc[:, ~df.columns.astype(str).str.startswith('Unnamed')]
df.to_excel(OUTPUT_FILE, index=False)

print(f'Arquivo gerado: {OUTPUT_FILE}')
print(f'Linhas iniciais: {linhas_iniciais}')
print(f'Linhas excluídas com coluna A não numérica: {linhas_excluidas_nao_numericas}')
print(f'Linhas excluídas sem nome_curso: {linhas_excluidas}')
print(f'Linhas consolidadas a partir de G: {linhas_com_g}')
print(f'Linhas finais: {len(df)}')
