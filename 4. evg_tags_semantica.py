import pandas as pd
import re
import unicodedata
from sentence_transformers import SentenceTransformer, util

BASE_FILE = '3b.1. evg_programas_e_cursos_infos.xlsx'
COMP_FILE = '2.1. evg_programas_e_cursos.csv'
TAGS_FILE = '0. tags_geral e AIE.xlsx'
OUTPUT_FILE = '4.1 evg_programa_e_cursos_infos_e_tags.xlsx'


def normalizar_texto(valor):
    texto = unicodedata.normalize('NFKD', str(valor).lower())
    return ''.join(
        caractere for caractere in texto
        if not unicodedata.combining(caractere)
    )


def termos_complementares(valor):
    return [
        termo.strip()
        for termo in re.split(r'[,;|]', normalizar_texto(valor))
        if termo.strip()
    ]

# ==========================================
# 1. Carregamento dos Arquivos
# ==========================================
print("Carregando bases de dados...")
df_base = pd.read_excel(BASE_FILE, sheet_name=0)
df_comp = pd.read_csv(COMP_FILE, sep=';', encoding='utf-8-sig')

# Carregar o arquivo Excel e suas abas
xls_tags = pd.ExcelFile(TAGS_FILE)
df_tags_geral = pd.read_excel(xls_tags, sheet_name='Tags_Geral')
df_tags_aie = pd.read_excel(xls_tags, sheet_name='Tags_aie')

# ==========================================
# 2. Mesclagem de Dados do Arquivo Complemento
# ==========================================
print("Mesclando informações de 'tipo' e 'painel'...")
df_comp_subset = df_comp[['url', 'tipo', 'painel']].copy()
df_base = df_base.merge(df_comp_subset, left_on='url_curso', right_on='url', how='left')
df_base = df_base.drop(columns=['url'])
df_base['painel'] = df_base['painel'].fillna('Não')

# ==========================================
# 3. Preparação das Tags
# ==========================================
tags_geral = df_tags_geral['Tags'].dropna().astype(str).unique().tolist()
df_tags_aie['aie_secoes'] = df_tags_aie['aie_secoes'].fillna('').astype(str).str.strip()
df_tags_aie['aie_complemento'] = df_tags_aie['aie_complemento'].fillna('').astype(str).str.strip()
tags_aie = df_tags_aie.loc[
    df_tags_aie['aie_secoes'].ne(''),
    'aie_secoes',
].drop_duplicates().tolist()
complementos_aie = {
    row['aie_secoes']: row['aie_complemento']
    for _, row in df_tags_aie.iterrows()
    if row['aie_secoes']
}

# Unificar todas as tags removendo duplicatas
textos_tags_aie = [
    f"{tag}. {complementos_aie.get(tag, '')}".strip()
    for tag in tags_aie
]
termos_aie = {
    tag: termos_complementares(complementos_aie.get(tag, ''))
    for tag in tags_aie
}
todas_tags = list(dict.fromkeys(tags_geral + textos_tags_aie))

# ==========================================
# 4. Configuração do Modelo Semântico
# ==========================================
print("Carregando modelo de linguagem...")
# Modelo multilingue otimizado para similaridade semântica
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Gerar embeddings para as tags
print("Gerando embeddings das tags...")
tags_embeddings = model.encode(todas_tags, convert_to_tensor=True)

# ==========================================
# 5. Processamento e Pesquisa Semântica
# ==========================================
colunas_busca = [
    'nome_curso',
    'curso-intro',
    'Público Alvo',
    'Conteúdo Programático',
]
df_base['texto_busca'] = df_base[colunas_busca].fillna('').astype(str).agg(' '.join, axis=1)

print("Gerando embeddings dos textos base...")
textos_embeddings = model.encode(df_base['texto_busca'].tolist(), convert_to_tensor=True)

print("Calculando similaridade semântica...")
# Calcula a pontuação de similaridade do cosseno entre os textos e as tags
cosine_scores = util.cos_sim(textos_embeddings, tags_embeddings)

# Definir o limiar de aceitação da similaridade (0.0 a 1.0)
# 0.65 é um valor de partida recomendado para evitar falsos positivos mantendo a flexibilidade semântica
limiar_similaridade = 0.65

print("Consolidando tags identificadas...")
similaridades = cosine_scores.cpu().numpy()
total_tags_geral = len(tags_geral)
textos_busca_normalizados = df_base['texto_busca'].map(normalizar_texto).tolist()


def aie_tem_termo_explicito(texto, tag):
    return any(
        re.search(rf'\b{re.escape(termo)}\b', texto)
        for termo in termos_aie.get(tag, [])
    )

df_base['tags_geral'] = [
    ', '.join(
        tag
        for indice, tag in enumerate(tags_geral)
        if similaridades[linha, indice] >= limiar_similaridade
    )
    for linha in range(len(df_base))
]
df_base['tag_aie'] = [
    ', '.join(
        tag
        for indice, tag in enumerate(tags_aie, start=total_tags_geral)
        if (
            similaridades[linha, indice] >= limiar_similaridade
            or aie_tem_termo_explicito(textos_busca_normalizados[linha], tag)
        )
    )
    for linha in range(len(df_base))
]

# ==========================================
# 6. Exportação do Resultado
# ==========================================
# Remover a coluna auxiliar de busca, se desejar
df_base = df_base.drop(columns=['texto_busca'])

df_base.to_excel(OUTPUT_FILE, index=False)
print(f"Processo concluído. Arquivo salvo como: {OUTPUT_FILE}")