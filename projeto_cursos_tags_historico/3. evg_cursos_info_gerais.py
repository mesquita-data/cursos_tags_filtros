import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

# ==========================================
# CONFIGURAÇÕES E VARIÁVEIS DO PROJETO
# ==========================================
CSV_INPUT_PATH = '2.1. evg_programas_e_cursos.csv'
CSV_OUTPUT_PATH = 'Cursos_EVG_Extraidos.csv'

# Define se o script rodará em modo de teste (True) ou completo (False)
MODO_TESTE = True
LIMITE_TESTE = 5

def extrair_informacoes(url, headers):
    """Extrai os dados usando a MESMA LÓGICA do script que obteve sucesso."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"  Página ignorada (Erro {response.status_code})")
            return {'nome do curso/programa': f'Erro {response.status_code}', 'introdução': '', 'público-alvo': '', 'conteúdo': ''}
            
        soup = BeautifulSoup(response.content, 'html.parser')

        # ---------------------------------------------------------
        # 1. Nome do curso e Introdução
        # ---------------------------------------------------------
        nome_curso = ""
        curso_intro = ""
        box_intro = soup.find(class_='box-curso-intro')
        
        if box_intro:
            # O nome do curso costuma ser o primeiro elemento (h1 ou h2) na caixa
            h1_h2 = box_intro.find(['h1', 'h2'])
            if h1_h2:
                nome_curso = h1_h2.get_text(strip=True)
            else:
                # Se não houver h1/h2, pega a primeira string solta dentro da div
                textos = list(box_intro.stripped_strings)
                nome_curso = textos[0] if textos else ""

            # Descrição introdutória
            p_fs5 = box_intro.find(class_='fs-5')
            if p_fs5:
                curso_intro = p_fs5.get_text(strip=True)

        # ---------------------------------------------------------
        # 2. Público Alvo
        # ---------------------------------------------------------
        publico_alvo = ""
        pa_tag = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'p', 'div', 'span', 'dt'] and 
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

        # ---------------------------------------------------------
        # 3. Conteúdo Programático
        # ---------------------------------------------------------
        conteudo = ""
        cp_tag = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'p', 'div', 'span', 'dt'] and 
                                       tag.get_text(strip=True).lower().startswith('conteúdo programático'))
        if cp_tag:
            # Procura a primeira tabela que aparece DEPOIS do título
            tabela = cp_tag.find_next('table')
            if tabela:
                celulas = []
                for row in tabela.find_all('tr'):
                    textos_linha = [cel.get_text(strip=True) for cel in row.find_all(['td', 'th']) if cel.get_text(strip=True)]
                    if textos_linha:
                        celulas.append(" - ".join(textos_linha))
                conteudo = " | ".join(celulas)
            else:
                # Fallback: caça listas (ul/ol) ou o próximo texto/dd
                ul = cp_tag.find_next(['ul', 'ol'])
                if ul:
                    # Traz todos os itens da lista, conforme você pediu antes, formatando com quebra de linha
                    itens = [li.get_text(strip=True) for li in ul.find_all('li')]
                    conteudo = '\n'.join(f"- {item}" for item in itens)
                else:
                    irmao = cp_tag.find_next_sibling()
                    if irmao:
                        conteudo = irmao.get_text(separator=" ", strip=True)

        return {
            'nome do curso/programa': nome_curso,
            'introdução': curso_intro,
            'público-alvo': publico_alvo,
            'conteúdo': conteudo
        }
        
    except Exception as e:
        print(f"  Erro no processamento: {e}")
        return {'nome do curso/programa': 'Erro', 'introdução': '', 'público-alvo': '', 'conteúdo': ''}


def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. Leitura inicial dos dados
    try:
        df = pd.read_csv(CSV_INPUT_PATH, sep=';')
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV de entrada: {e}")
        return

    # Aplicação da regra de teste ou execução completa
    if MODO_TESTE:
        print(f"--- MODO TESTE ATIVADO ---")
        print(f"Executando raspagem apenas para as primeiras {LIMITE_TESTE} URLs.\n")
        df = df.head(LIMITE_TESTE)
    else:
        print(f"--- MODO COMPLETO ATIVADO ---")
        print(f"Executando raspagem para todas as {len(df)} URLs.\n")

    resultados = []

    # 2. Iteração sobre a lista de URLs
    for index, row in df.iterrows():
        url = row.get('url')
        if not url or pd.isna(url):
            continue
            
        print(f"[{index+1}/{len(df)}] Raspando: {url}")
        
        info = extrair_informacoes(url, headers)
        info['url'] = url
        resultados.append(info)
        
        time.sleep(1) # Pausa amigável

    # 3. Formatação e salvamento
    df_resultados = pd.DataFrame(resultados)
    
    # Garante a ordem correta das colunas
    colunas_finais = ['url', 'nome do curso/programa', 'introdução', 'público-alvo', 'conteúdo']
    df_resultados = df_resultados[[c for c in colunas_finais if c in df_resultados.columns]]
    
    nome_arquivo_saida = "TESTE_" + CSV_OUTPUT_PATH if MODO_TESTE else CSV_OUTPUT_PATH
    df_resultados.to_csv(nome_arquivo_saida, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"\nExtração concluída. Dados salvos em: {nome_arquivo_saida}")

if __name__ == "__main__":
    main()
    