import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# CONFIGURAÇÕES
# ==========================================
CSV_INPUT_PATH = '2.1. evg_programas_e_cursos.csv'
CSV_OUTPUT_PATH = '3.1. evg_programas_e_cursos.csv'

def configurar_driver():
    """Configura o navegador Chrome em modo oculto (headless)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def extrair_informacoes(html_content, url):
    """Analisa o HTML carregado pelo navegador e extrai os dados"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Nome do curso/programa
    titulo_tag = soup.find('h1')
    nome = titulo_tag.text.strip() if titulo_tag else 'Título não encontrado'
    
    # Textos da EV.G costumam estar em blocos de parágrafos após os títulos de seção
    def buscar_texto_secao(palavras_chave):
        texto = ''
        tag_secao = soup.find(lambda tag: tag.name in ['h2', 'h3', 'strong'] and any(p in tag.text.lower() for p in palavras_chave))
        if tag_secao:
            for sibling in tag_secao.find_next_siblings():
                if sibling.name in ['h1', 'h2', 'h3']: 
                    break
                if sibling.name in ['p', 'ul', 'li', 'div', 'span']: 
                    texto += sibling.text.strip() + '\n'
        return texto.strip()

    # 2. Introdução / Apresentação
    intro = buscar_texto_secao(['apresentação', 'sobre', 'introdução', 'objetivo'])
    
    # 3. Público-alvo
    publico = buscar_texto_secao(['público', 'alvo', 'perfil'])
    
    # 4. Conteúdo Programático
    conteudo = buscar_texto_secao(['conteúdo', 'programático', 'ementa', 'módulos'])
            
    return {
        'nome do curso/programa': nome,
        'introdução': intro,
        'público-alvo': publico,
        'conteúdo': conteudo
    }

def main():
    # 1. Leitura inicial dos dados
    try:
        df = pd.read_csv(CSV_INPUT_PATH, sep=';')
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV de entrada: {e}")
        return

    driver = configurar_driver()
    resultados = []

    # 2. Iteração sobre a lista de URLs
    for index, row in df.iterrows():
        url = row['url']
        print(f"[{index+1}/{len(df)}] Extraindo: {url}")
        
        try:
            driver.get(url)
            # Aguarda o JavaScript renderizar o conteúdo (ajuste se necessário)
            time.sleep(4) 
            
            html_content = driver.page_source
            info = extrair_informacoes(html_content, url)
            info['url'] = url
            
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            info = {
                'url': url,
                'nome do curso/programa': 'Erro de acesso',
                'introdução': '',
                'público-alvo': '',
                'conteúdo': ''
            }
            
        resultados.append(info)

    driver.quit()

    # 3. Formatação e salvamento
    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados[['url', 'nome do curso/programa', 'introdução', 'público-alvo', 'conteúdo']]
    df_resultados.to_csv(CSV_OUTPUT_PATH, index=False, sep=';', encoding='utf-8-sig')
    print(f"\nExtração concluída. Dados salvos em: {CSV_OUTPUT_PATH}")

if __name__ == "__main__":
    main()