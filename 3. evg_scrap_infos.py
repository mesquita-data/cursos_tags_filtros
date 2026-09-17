import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Configuração de modo de teste
MODO_TESTE = False  # Mude para False para rodar todos os cursos do arquivo
LIMITE_TESTE = 5

# ---------------------------------------------------------
# 1. Carregar IDs dos cursos a partir do arquivo CSV
# ---------------------------------------------------------
try:
    # sep=None e engine='python' forçam o pandas a identificar se o separador é ',' ou ';'
    try:
        df_input = pd.read_csv("2.1. evg_programas_e_cursos.csv", sep=None, engine='python', encoding='utf-8')
    except UnicodeDecodeError:
        # Fallback caso o arquivo tenha sido salvo no Excel padrão do Windows (latin1)
        df_input = pd.read_csv("2.1. evg_programas_e_cursos.csv", sep=None, engine='python', encoding='latin1')
        
    # Padroniza os nomes das colunas: remove espaços em branco nas pontas e deixa minúsculo
    df_input.columns = df_input.columns.str.strip().str.lower()
    
    if 'id' in df_input.columns:
        # Converte forçadamente para número (ignorando textos acidentais) e joga numa lista
        ids_cursos = pd.to_numeric(df_input['id'], errors='coerce').dropna().astype(int).tolist()
        print(f"Sucesso: {len(ids_cursos)} IDs encontrados no arquivo de origem.")
    else:
        print(f"ERRO: A coluna 'id' não foi encontrada. Colunas lidas pelo script: {df_input.columns.tolist()}")
        ids_cursos = []

except FileNotFoundError:
    print("ERRO: Arquivo '2.1. evg_programas_e_cursos.csv' não encontrado. Verifique a pasta onde o script está rodando.")
    ids_cursos = []
except Exception as e:
    print(f"ERRO inesperado ao tentar ler o arquivo: {e}")
    ids_cursos = []

# Se estiver em modo de teste, pega apenas os primeiros itens
if MODO_TESTE and len(ids_cursos) > 0:
    ids_cursos = ids_cursos[:LIMITE_TESTE]
    print(f"--- MODO TESTE ATIVADO: Rodando apenas {LIMITE_TESTE} itens ---")

# ---------------------------------------------------------
# 2. Extração dos dados da Escola Virtual
# ---------------------------------------------------------
dados_extraidos = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for id_curso in ids_cursos:
    url = f"https://www.escolavirtual.gov.br/curso/{id_curso}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Página ignorada (Erro {response.status_code}): {id_curso}")
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')

        # 2.1 Nome do curso e curso-intro
        nome_curso = ""
        curso_intro = ""
        box_intro = soup.find(class_='box-curso-intro')
        
        if box_intro:
            h1 = box_intro.find(['h1', 'h2'])
            if h1:
                nome_curso = h1.get_text(strip=True)
            else:
                textos = list(box_intro.stripped_strings)
                nome_curso = textos[0] if textos else ""

            p_fs5 = box_intro.find(class_='fs-5')
            if p_fs5:
                curso_intro = p_fs5.get_text(strip=True)

        # 2.2 Público Alvo
        publico_alvo = ""
        pa_tag = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'p', 'div', 'span'] and 
                                       tag.get_text(strip=True).lower().startswith('público alvo'))
        if pa_tag:
            texto_completo = pa_tag.parent.get_text(separator=" ", strip=True) if pa_tag.name in ['strong', 'b', 'span'] else pa_tag.get_text(separator=" ", strip=True)
            texto_limpo = re.sub(r'(?i)público[- ]alvo:?\s*', '', texto_completo).strip()
            
            if texto_limpo:
                publico_alvo = texto_limpo
            else:
                irmao = pa_tag.find_next_sibling()
                if irmao:
                    publico_alvo = irmao.get_text(separator=" ", strip=True)

        # 2.3 Conteúdo Programático (Tabela ou Lista)
        conteudo = ""
        cp_tag = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'p', 'div', 'span'] and 
                                       tag.get_text(strip=True).lower().startswith('conteúdo programático'))
        if cp_tag:
            tabela = cp_tag.find_next('table')
            if tabela:
                celulas = []
                for row in tabela.find_all('tr'):
                    textos_linha = [cel.get_text(strip=True) for cel in row.find_all(['td', 'th']) if cel.get_text(strip=True)]
                    if textos_linha:
                        celulas.append(" - ".join(textos_linha))
                conteudo = " | ".join(celulas)
            else:
                ul = cp_tag.find_next(['ul', 'ol'])
                if ul:
                    conteudo = ul.get_text(separator=" | ", strip=True)
                else:
                    irmao = cp_tag.find_next_sibling()
                    if irmao:
                        conteudo = irmao.get_text(separator=" ", strip=True)

        dados_extraidos.append({
            "id_curso": id_curso,
            "url_curso": url,
            "nome_curso": nome_curso,
            "curso-intro": curso_intro,
            "Público Alvo": publico_alvo,
            "Conteúdo Programático": conteudo
        })
        print(f"Lido com sucesso: {id_curso} - {nome_curso[:40]}")
        
    except Exception as e:
        print(f"Erro no curso {id_curso}: {e}")

# ---------------------------------------------------------
# 3. Exportação para CSV
# ---------------------------------------------------------
df_final = pd.DataFrame(dados_extraidos)
nome_arquivo = "3.1. evg_programas_e_cursos_infos.csv"

if not df_final.empty:
    df_final.to_csv(nome_arquivo, index=False, encoding='utf-8')
    print(f"\nPronto! Arquivo '{nome_arquivo}' atualizado com sucesso.")
else:
    print("\nNenhum dado foi extraído. O arquivo CSV não foi gerado.")