import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Lista com os IDs dos cursos
ids_cursos = [
    107, 153, 270, 290, 343, 367, 373, 377, 406, 419, 529, 534, 536, 
    629, 724, 787, 797, 802, 815, 861, 956, 976, 1073, 1088, 1090, 
    1091, 1139, 1153, 1167, 810, 1263, 1304, 1305, 1328, 1395
]

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

        # ---------------------------------------------------------
        # 1. Nome do curso e curso-intro
        # ---------------------------------------------------------
        nome_curso = ""
        curso_intro = ""
        box_intro = soup.find(class_='box-curso-intro')
        
        if box_intro:
            # O nome do curso costuma ser o primeiro elemento (h1 ou h2) na caixa
            h1 = box_intro.find(['h1', 'h2'])
            if h1:
                nome_curso = h1.get_text(strip=True)
            else:
                # Se não houver h1, pega a primeira string solta dentro da div
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
        # Caça qualquer tag que contenha o texto começando com "público alvo"
        pa_tag = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'p', 'div', 'span'] and 
                                       tag.get_text(strip=True).lower().startswith('público alvo'))
        if pa_tag:
            # Pega o texto da tag mãe se for uma tag de formatação (strong/b), caso contrário da própria tag
            texto_completo = pa_tag.parent.get_text(separator=" ", strip=True) if pa_tag.name in ['strong', 'b', 'span'] else pa_tag.get_text(separator=" ", strip=True)
            
            # Remove a expressão "Público Alvo:" para sobrar apenas o conteúdo
            texto_limpo = re.sub(r'(?i)público[- ]alvo:?\s*', '', texto_completo).strip()
            
            if texto_limpo:
                publico_alvo = texto_limpo
            else:
                # Se a tag era APENAS o título, o conteúdo estará no próximo elemento (irmão)
                irmao = pa_tag.find_next_sibling()
                if irmao:
                    publico_alvo = irmao.get_text(separator=" ", strip=True)

        # ---------------------------------------------------------
        # 3. Conteúdo Programático (Tabela)
        # ---------------------------------------------------------
        conteudo = ""
        cp_tag = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong', 'b', 'p', 'div', 'span'] and 
                                       tag.get_text(strip=True).lower().startswith('conteúdo programático'))
        if cp_tag:
            # Procura a primeira tabela que aparece DEPOIS do título
            tabela = cp_tag.find_next('table')
            if tabela:
                celulas = []
                # Varre todas as linhas (tr)
                for row in tabela.find_all('tr'):
                    # Extrai o texto de todas as células daquela linha (td ou th)
                    textos_linha = [cel.get_text(strip=True) for cel in row.find_all(['td', 'th']) if cel.get_text(strip=True)]
                    if textos_linha:
                        celulas.append(" - ".join(textos_linha))
                
                # Junta todas as linhas separadas por " | "
                conteudo = " | ".join(celulas)
            else:
                # Fallback: Se não encontrar tabela, caça listas (ul/ol) ou o próximo texto
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

# Transforma os dados numa tabela do pandas e salva em Excel
df_final = pd.DataFrame(dados_extraidos)
nome_arquivo = "3.1. evg_proCursos_EVG_Completo.xlsx"
df_final.to_excel(nome_arquivo, index=False)
print(f"Pronto! Arquivo '{nome_arquivo}' atualizado com sucesso.")