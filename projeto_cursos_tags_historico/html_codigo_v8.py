import json
from pathlib import Path

import pandas as pd

# ==========================================
# CONFIGURAÇÕES E VARIÁVEIS DO PROJETO
# ==========================================
EXCEL_INPUT_PATH = Path('Cursos_EVG_Final_Tags_v7.xlsx')
HTML_OUTPUT_PATH = Path('Cursos_Filtro_EVG_v8.html')
SECOES_INPUT_PATH = Path('seções e recomendações.xlsx')
SHEET_NAME_PRINCIPAL = 'Tabela Principal'


def carregar_secoes_aie(caminho: Path):
    """Lê a primeira coluna da tabela aie_secoes do arquivo de seções."""
    if not caminho.exists():
        raise FileNotFoundError(f'Arquivo de seções não encontrado: {caminho}')

    xls = pd.ExcelFile(caminho)

    for nome_planilha in xls.sheet_names:
        df = pd.read_excel(caminho, sheet_name=nome_planilha)
        colunas = {str(col).strip().lower(): col for col in df.columns}

        if 'aie_secoes' in colunas:
            coluna = colunas['aie_secoes']
            valores = df[coluna].dropna().astype(str).str.strip()
            return [valor for valor in valores if valor and valor.lower() != 'aie_secoes']

    # Fallback: usa a primeira coluna da primeira aba quando a tabela não for encontrada
    primeira_planilha = xls.sheet_names[0]
    df = pd.read_excel(caminho, sheet_name=primeira_planilha)
    primeira_coluna = df.iloc[:, 0].dropna().astype(str).str.strip()
    return [valor for valor in primeira_coluna if valor]


# 1. Leitura e tratamento inicial dos dados
if not EXCEL_INPUT_PATH.exists():
    raise FileNotFoundError(f'Arquivo de cursos não encontrado: {EXCEL_INPUT_PATH}')

xls = pd.ExcelFile(EXCEL_INPUT_PATH)
print(f'Planilhas disponíveis no arquivo: {xls.sheet_names}')

df = pd.read_excel(xls, sheet_name=SHEET_NAME_PRINCIPAL)
df = df.fillna('')

# 2. Carrega a listagem de seções do documento de referência
sections = carregar_secoes_aie(SECOES_INPUT_PATH)
print(f'Quantidade de seções AIE carregadas: {len(sections)}')
print('Primeiras seções:', sections[:10])

courses = df.to_dict('records')
courses_json = json.dumps(courses, ensure_ascii=False)
aie_sections_json = json.dumps(sections, ensure_ascii=False)

# 3. Template HTML com estilização e interatividade embutidas
html_content = f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Painel de cursos da EV.G filtrados por Temas</title>
    <style>
        :root {{
            --primary-color: #00427a;
            --secondary-color: #f4f6f8;
            --text-color: #333;
            --border-color: #ccc;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--secondary-color);
            color: var(--text-color);
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
        }}
        .description {{
            font-size: 1.1em;
            color: #555;
            line-height: 1.5;
            margin-bottom: 25px;
        }}
        .filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
            background: #eef2f5;
            padding: 20px;
            border-radius: 6px;
            align-items: flex-end;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            flex: 1;
            min-width: 250px;
        }}
        label {{
            font-weight: bold;
            margin-bottom: 8px;
            color: var(--primary-color);
        }}
        select {{
            padding: 10px;
            font-size: 16px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background-color: #fff;
        }}
        .btn-clear {{
            padding: 10px 20px;
            font-size: 16px;
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
            height: 40px;
        }}
        .btn-clear:hover {{
            background-color: #c82333;
        }}
        .summary {{
            font-size: 1.1em;
            font-weight: 500;
            margin-bottom: 20px;
            padding: 10px;
            background-color: #e8f4fd;
            border-left: 4px solid var(--primary-color);
            color: #00335e;
        }}
        .course-card {{
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 15px;
            background: #fff;
            transition: box-shadow 0.2s;
        }}
        .course-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .course-title {{
            margin-top: 0;
            font-size: 1.4em;
        }}
        .course-title a {{
            color: var(--primary-color);
            text-decoration: none;
        }}
        .course-title a:hover {{
            text-decoration: underline;
        }}
        .course-desc {{
            margin-top: 12px;
            line-height: 1.6;
            color: #555;
        }}
        .course-tags {{
            margin-top: 15px;
            font-size: 0.85em;
            color: #666;
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }}
        .tag {{
            background: #e1e8ed;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }}
        .tag:hover {{
            opacity: 0.8;
            transform: scale(1.02);
        }}
        .tag-aie {{
            background: #d4edda;
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Painel de cursos da EV.G filtrados por Temas</h1>
        <p class=\"description\"> Selecionados os cursos da Escola Virtual de Governo da ENAP já identificados como aderentes aos perfis de capacitação em IA, esta página tem como objetivo testar e aplicar a filtragem de acordo com os temas do AIE e outras tags gerais. Foi elaborado com IA (Gemini Pro) e com revisão humana, de maneira recursiva, e o correlacionamento das tags foi aplicado sobre título, descrição e conteúdo programático de cada curso. Trata-se de exercício para análise e revisão.</p>
        
        <div class=\"filters\">
            <div class=\"filter-group\">
                <label for=\"filterAIE\">Tema da AIE:</label>
                <select id=\"filterAIE\">
                    <option value=\"\">Selecione...</option>
                </select>
            </div>
            <div class=\"filter-group\">
                <label for=\"filterGeral\">Tags Gerais:</label>
                <select id=\"filterGeral\">
                    <option value=\"\">Selecione...</option>
                </select>
            </div>
            <button id=\"btnClear\" class=\"btn-clear\">Limpar as seleções</button>
        </div>

        <div class=\"summary\" id=\"summaryText\"></div>
        <div id=\"courseList\"></div>
    </div>

    <script>
        const courses = {courses_json};
        const aieSections = {aie_sections_json};
        
        const aieTags = new Set(aieSections.filter(Boolean));
        const geralTags = new Set();

        courses.forEach(c => {{
            if (c.tags_ampliadas) {{
                c.tags_ampliadas.split(',').forEach(t => geralTags.add(t.trim()));
            }}
        }});

        const filterAIE = document.getElementById('filterAIE');
        const filterGeral = document.getElementById('filterGeral');
        const btnClear = document.getElementById('btnClear');

        Array.from(aieTags).filter(t => t).sort().forEach(tag => {{
            let opt = document.createElement('option');
            opt.value = tag; opt.textContent = tag;
            filterAIE.appendChild(opt);
        }});

        Array.from(geralTags).filter(t => t).sort().forEach(tag => {{
            let opt = document.createElement('option');
            opt.value = tag; opt.textContent = tag;
            filterGeral.appendChild(opt);
        }});

        function setFilter(type, value) {{
            if (type === 'aie') {{
                filterAIE.value = value;
            }} else if (type === 'geral') {{
                filterGeral.value = value;
            }}
            updateView();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function updateView() {{
            const valAIE = filterAIE.value;
            const valGeral = filterGeral.value;

            const filtered = courses.filter(c => {{
                const matchAIE = valAIE === "" || (c.tags_aie_rev && c.tags_aie_rev.split(',').map(t => t.trim()).includes(valAIE));
                const matchGeral = valGeral === "" || (c.tags_ampliadas && c.tags_ampliadas.split(',').map(t => t.trim()).includes(valGeral));
                return matchAIE && matchGeral;
            }});

            let summary = \"\";
            if (!valAIE && !valGeral) {{
                summary = `Nenhum curso filtrado, total: ${{courses.length}}`;
            }} else {{
                let filters = [];
                if (valAIE) filters.push(`o Tema da AIE: <strong>${{valAIE}}</strong>`);
                if (valGeral) filters.push(`temas: <strong>${{valGeral}}</strong>`);
                summary = `${{filtered.length}} cursos filtrados do total de ${{courses.length}} com ${{filters.join(' e ')}}.`;
            }}
            document.getElementById('summaryText').innerHTML = summary;

            const listContainer = document.getElementById('courseList');
            listContainer.innerHTML = \"\";
            
            filtered.forEach(c => {{
                const div = document.createElement('div');
                div.className = 'course-card';
                
                let desc = c['curso-intro'] || c['Descrição'] || 'Sem descrição disponível.';
                
                let tagsHTML = '';
                if (c.tags_aie_rev) {{
                    c.tags_aie_rev.split(',').forEach(t => {{
                        let tag = t.trim();
                        if(tag) tagsHTML += `<span class=\"tag tag-aie\" onclick=\"setFilter('aie', '${{tag}}')\" title=\"Filtrar por ${{tag}}\">${{tag}}</span>`;
                    }});
                }}
                if (c.tags_ampliadas) {{
                    c.tags_ampliadas.split(',').forEach(t => {{
                        let tag = t.trim();
                        if(tag) tagsHTML += `<span class=\"tag\" onclick=\"setFilter('geral', '${{tag}}')\" title=\"Filtrar por ${{tag}}\">${{tag}}</span>`;
                    }});
                }}

                div.innerHTML = `
                    <h3 class=\"course-title\"><a href=\"${{c.url_curso}}\" target=\"_blank\">${{c.nome_curso}}</a></h3>
                    <div class=\"course-desc\">${{desc}}</div>
                    <div class=\"course-tags\">${{tagsHTML}}</div>
                `;
                listContainer.appendChild(div);
            }});
        }}

        filterAIE.addEventListener('change', updateView);
        filterGeral.addEventListener('change', updateView);
        
        btnClear.addEventListener('click', () => {{
            filterAIE.value = \"\";
            filterGeral.value = \"\";
            updateView();
        }});
        updateView();
    </script>
</body>
</html>
"""

# 4. Salvando no arquivo HTML
HTML_OUTPUT_PATH.write_text(html_content, encoding='utf-8')
print(f'Arquivo HTML gerado: {HTML_OUTPUT_PATH}')
