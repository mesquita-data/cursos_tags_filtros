import csv
import re
import time
import urllib.parse
import urllib.request

import pandas as pd


def incluir_coluna_painel(
    nome_arquivo_csv="evg_programas_e_cursos.csv",
    nome_arquivo_painel="cursos_painel.xlsx",
):
    """Compara as URLs do CSV com a lista do painel e adiciona a coluna 'painel'."""
    try:
        painel_df = pd.read_excel(nome_arquivo_painel)
    except FileNotFoundError:
        print(f"Arquivo de painel não encontrado: {nome_arquivo_painel}")
        return

    url_cols = [col for col in painel_df.columns if "url" in str(col).lower()]
    if not url_cols:
        print(f"Nenhuma coluna de URL encontrada em {nome_arquivo_painel}.")
        return

    painel_urls = set()
    for col in url_cols:
        painel_urls.update(
            str(valor).strip().lower()
            for valor in painel_df[col].dropna()
            if str(valor).strip()
        )

    with open(nome_arquivo_csv, mode="r", newline="", encoding="utf-8-sig") as csv_file:
        leitor = csv.DictReader(csv_file, delimiter=";")
        colunas = list(leitor.fieldnames or [])
        linhas = list(leitor)

    if not colunas:
        print("CSV sem cabeçalho, impossível adicionar coluna 'painel'.")
        return

    if "painel" not in colunas:
        colunas.append("painel")

    for linha in linhas:
        url_atual = str(linha.get("url", "")).strip().lower()
        linha["painel"] = "Sim" if url_atual in painel_urls else "Não"

    with open(nome_arquivo_csv, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        escritor = csv.DictWriter(csv_file, fieldnames=colunas, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)

    total_sim = sum(1 for linha in linhas if linha.get("painel") == "Sim")
    total_nao = sum(1 for linha in linhas if linha.get("painel") == "Não")

    print("\n" + "=" * 60)
    print(" BATIMENTO COM O PAINEL")
    print("=" * 60)
    print(f"• URLs encontradas no painel: {total_sim}")
    print(f"• URLs ausentes no painel  : {total_nao}")
    print(f"• CSV atualizado com coluna 'painel': {nome_arquivo_csv}")
    print("=" * 60)


def extrair_links(url_base_secao, tipo_rotulo, padrao_regex, base_url):
    """Percorre a paginação de uma seção (programas ou catálogo) e retorna a lista de links encontrados."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resultados = []
    links_vistos = set()
    pagina = 1

    print(
        f"\n=== Iniciando busca em: {url_base_secao} (Tipo: {tipo_rotulo}) ==="
    )

    while True:
        url_pagina = f"{url_base_secao}?page={pagina}"
        print(f"Acessando Página {pagina}: {url_pagina}")

        try:
            req = urllib.request.Request(
                url_pagina, headers=headers
            )
            with urllib.request.urlopen(req) as response:
                html = response.read().decode("utf-8")

            # Busca os links correspondentes ao padrão regex especificado
            matches = re.findall(padrao_regex, html)
            novos_na_pagina = 0

            for match in matches:
                url_completa = urllib.parse.urljoin(
                    base_url, match
                )

                if url_completa not in links_vistos:
                    links_vistos.add(url_completa)
                    novos_na_pagina += 1

                    # Extrai o ID numérico ao final da URL
                    item_id = url_completa.split("/")[-1]

                    resultados.append(
                        {
                            "tipo": tipo_rotulo,
                            "id": item_id,
                            "url": url_completa,
                            "pagina_origem": pagina,
                        }
                    )

            print(
                f"   └─ {novos_na_pagina} novos links ({tipo_rotulo}) encontrados nesta página."
            )

            # Se não houver novos links, encerra a paginação dessa seção
            if novos_na_pagina == 0:
                print(
                    f"Fim da paginação para a seção '{tipo_rotulo}'."
                )
                break

            pagina += 1
            time.sleep(1)  # Intervalo de cortesia ao servidor

        except Exception as e:
            print(f"Erro ao acessar página {pagina}: {e}")
            break

    return resultados


def extrair_evg_completo(
    nome_arquivo_csv="evg_programas_e_cursos.csv",
):
    base_url = "https://www.escolavirtual.gov.br"

    # Configuração das duas buscas requeridas
    configuracoes_busca = [
        {
            "url": f"{base_url}/programas",
            "tipo": "programa",
            # Padrão para capturar links de programas (/programa/123)
            "regex": r'href=["\'](/programa/\d+|https://www\.escolavirtual\.gov\.br/programa/\d+)["\']',
        },
        {
            "url": f"{base_url}/catalogo",
            "tipo": "curso",
            # Padrão para capturar links de cursos do catálogo (/curso/123)
            "regex": r'href=["\'](/curso/\d+|https://www\.escolavirtual\.gov\.br/curso/\d+)["\']',
        },
    ]

    todos_resultados = []

    # Executa a raspagem para cada uma das duas origens
    for config in configuracoes_busca:
        itens = extrair_links(
            url_base_secao=config["url"],
            tipo_rotulo=config["tipo"],
            padrao_regex=config["regex"],
            base_url=base_url,
        )
        todos_resultados.extend(itens)

    # Geração do arquivo CSV consolidado
    if todos_resultados:
        campos = ["tipo", "id", "url", "pagina_origem"]

        with open(
            nome_arquivo_csv,
            mode="w",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=campos,
                delimiter=";",  # Separador por ponto e vírgula para compatibilidade com Excel em PT-BR
            )

            writer.writeheader()
            writer.writerows(todos_resultados)

        total_programas = sum(
            1 for r in todos_resultados if r["tipo"] == "programa"
        )
        total_cursos = sum(
            1 for r in todos_resultados if r["tipo"] == "curso"
        )

        print("\n" + "=" * 60)
        print(" RESUMO DA EXTRAÇÃO CONSOLIDADA")
        print("=" * 60)
        print(f"• Total de Programas encontrados : {total_programas}")
        print(f"• Total de Cursos encontrados    : {total_cursos}")
        print(
            f"• TOTAL GERAL                    : {len(todos_resultados)}"
        )
        print(f"\nArquivo CSV gerado com sucesso: {nome_arquivo_csv}")
        print("=" * 60)
    else:
        print("Nenhum dado foi extraído.")


if __name__ == "__main__":
    extrair_evg_completo()
    incluir_coluna_painel()