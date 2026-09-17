import json
from pathlib import Path

import pandas as pd

# ==========================================
# CONFIGURAÇÕES E VARIÁVEIS DO PROJETO
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
EXCEL_INPUT_PATH = BASE_DIR / '4.1 evg_programa_e_cursos_infos_e_tags.xlsx'
HTML_OUTPUT_PATH = BASE_DIR / '5. Cursos_Filtro_EVG.html'

# 1. Leitura e tratamento inicial dos dados
xls = pd.ExcelFile(EXCEL_INPUT_PATH)
print(f"Planilhas disponíveis no arquivo: {xls.sheet_names}")

df = pd.read_excel(xls, sheet_name=0)
df = df.fillna('')  # Substitui valores vazios por strings em branco para evitar erros no JS
df['matriz'] = df['painel'].map(
    lambda value: (
        'Mapeado na Matriz de Competência'
        if str(value).strip().lower() == 'sim'
        else ''
    )
)
df['tag_aie'] = df['tag_aie'].astype(str)
df['tags_geral'] = df['tags_geral'].astype(str)
df = df.drop(columns=['tipo', 'painel'], errors='ignore')
courses = df.to_dict('records')
courses_json = json.dumps(courses, ensure_ascii=False)

# 2. Template HTML com estilização e interatividade embutidas
html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            .badge-matriz {{ background: #fff3cd; color: #7a5700; }}
        
        
    </style>
</head>
<body>
    <div class="container">
        <h1>Painel de cursos da EV.G filtrados por Temas</h1>
        <p class="description"> Selecionados os cursos da Escola Virtual de Governo da ENAP já identificados como aderentes aos perfis de capacitação em IA, esta página tem como objetivo testar e aplicar a filtragem de acordo com os temas do AIE e outras tags gerais. Foi elaborado com IA (Gemini Pro) e com revisão humana, de maneira recursiva, e o correlacionamento das tags foi aplicado sobre título, descrição e conteúdo programático de cada curso. Trata-se de exercício para análise e revisão.</p>
        
        <div class="filters">
            <div class="filter-group">
                <label for="filterAIE">Filtro por tema do AIE:</label>
                <select id="filterAIE">
                    <option value="">Selecione...</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filterGeral">Filtro por Tópico Geral:</label>
                <select id="filterGeral">
                    <option value="">Selecione...</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filterMatriz">Matriz de Competências:</label>
                <select id="filterMatriz">
                    <option value="">Todos</option>
                </select>
            </div>
            <button id="btnClear" class="btn-clear">Limpar as seleções</button>
        </div>

        <div class="summary" id="summaryText"></div>
        <div id="courseList"></div>
    </div>

    <script>
        const courses = {courses_json};
        
        const aieTags = new Set();
        const geralTags = new Set();
        const matrizes = new Set();

        courses.forEach(c => {{
            if (c.tag_aie) {{
                c.tag_aie.split(',').forEach(t => aieTags.add(t.trim()));
            }}
            if (c.tags_geral) {{
                c.tags_geral.split(',').forEach(t => geralTags.add(t.trim()));
            }}
            if (c.matriz) matrizes.add(c.matriz);
        }});

        const filterAIE = document.getElementById('filterAIE');
        const filterGeral = document.getElementById('filterGeral');
        const filterMatriz = document.getElementById('filterMatriz');
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

        Array.from(matrizes).filter(t => t).sort().forEach(matriz => {{
            let opt = document.createElement('option');
            opt.value = matriz; opt.textContent = matriz;
            filterMatriz.appendChild(opt);
        }});

        function setFilter(type, value) {{
            if (type === 'aie') {{
                filterAIE.value = value;
            }} else if (type === 'geral') {{
                filterGeral.value = value;
            }} else if (type === 'matriz') {{
                filterMatriz.value = value;
            }}
            updateView();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function updateView() {{
            const valAIE = filterAIE.value;
            const valGeral = filterGeral.value;
            const valMatriz = filterMatriz.value;

            const filtered = courses.filter(c => {{
                const matchAIE = valAIE === "" || (c.tag_aie && c.tag_aie.split(',').map(t=>t.trim()).includes(valAIE));
                const matchGeral = valGeral === "" || (c.tags_geral && c.tags_geral.split(',').map(t=>t.trim()).includes(valGeral));
                const matchMatriz = valMatriz === "" || c.matriz === valMatriz;
                return matchAIE && matchGeral && matchMatriz;
            }});

            let summary = "";
            if (!valAIE && !valGeral && !valMatriz) {{
                summary = `Nenhum curso filtrado, total: ${{courses.length}}`;
            }} else {{
                let filters = [];
                if (valAIE) filters.push(`o Tema da AIE: <strong>${{valAIE}}</strong>`);
                if (valGeral) filters.push(`temas: <strong>${{valGeral}}</strong>`);
                if (valMatriz) filters.push(`Matriz de Competências: <strong>${{valMatriz}}</strong>`);
                summary = `${{filtered.length}} cursos filtrados do total de ${{courses.length}} com ${{filters.join(' e ')}}.`;
            }}
            document.getElementById('summaryText').innerHTML = summary;

            const listContainer = document.getElementById('courseList');
            listContainer.innerHTML = "";
            
            filtered.forEach(c => {{
                const div = document.createElement('div');
                div.className = 'course-card';
                
                let desc = c['curso-intro'] || c['Descrição'] || 'Sem descrição disponível.';
                let matrizHTML = c.matriz
                    ? `<span class="badge badge-matriz" title="Mapeado na Matriz de Competência">★ ${{c.matriz}}</span>`
                    : '';
                
                let tagsHTML = '';
                if (c.tag_aie) {{
                    c.tag_aie.split(',').forEach(t => {{
                        let tag = t.trim();
                        if(tag) tagsHTML += `<span class="tag tag-aie" onclick="setFilter('aie', '${{tag}}')" title="Filtrar por ${{tag}}">${{tag}}</span>`;
                    }});
                }}
                if (c.tags_geral) {{
                    c.tags_geral.split(',').forEach(t => {{
                        let tag = t.trim();
                        if(tag) tagsHTML += `<span class="tag" onclick="setFilter('geral', '${{tag}}')" title="Filtrar por ${{tag}}">${{tag}}</span>`;
                    }});
                }}

                div.innerHTML = `
                    <div class="meta-row">${{matrizHTML}}</div>
                    <h3 class="course-title"><a href="${{c.url_curso}}" target="_blank">${{c.nome_curso}}</a></h3>
                    <div class="course-desc">${{desc}}</div>
                    <div class="course-tags">${{tagsHTML}}</div>
                `;
                listContainer.appendChild(div);
            }});
        }}

        filterAIE.addEventListener('change', updateView);
        filterGeral.addEventListener('change', updateView);
        filterMatriz.addEventListener('change', updateView);
        
        btnClear.addEventListener('click', () => {{
            filterAIE.value = "";
            filterGeral.value = "";
            filterMatriz.value = "";
            updateView();
        }});

        updateView();
    </script>
</body>
</html>
"""

# 3. Escrita do arquivo HTML resultante
with open(HTML_OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Painel gerado com sucesso em: {HTML_OUTPUT_PATH}")