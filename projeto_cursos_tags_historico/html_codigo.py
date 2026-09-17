import pandas as pd
import json

file_cursos = '/mnt/data/Cursos_EVG_AIE_Enriquecido.xlsx'
df = pd.read_excel(file_cursos)

# Fill NaNs with empty strings to avoid JSON serialization issues
df = df.fillna('')

# Convert dataframe to dictionary records
courses = df.to_dict('records')
courses_json = json.dumps(courses)

# HTML Template
html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Cursos EV.G - Temas AIE</title>
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
        .filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
            background: #eef2f5;
            padding: 20px;
            border-radius: 6px;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            flex: 1;
            min-width: 300px;
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
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .tag-aie {{
            background: #d4edda;
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Painel de Cursos EV.G</h1>
        
        <div class="filters">
            <div class="filter-group">
                <label for="filterAIE">Tema da AIE:</label>
                <select id="filterAIE">
                    <option value="">Selecione...</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filterGeral">Tags Gerais:</label>
                <select id="filterGeral">
                    <option value="">Selecione...</option>
                </select>
            </div>
        </div>

        <div class="summary" id="summaryText"></div>
        <div id="courseList"></div>
    </div>

    <script>
        const courses = {courses_json};
        
        // Extrair e popular as tags nos filtros
        const aieTags = new Set();
        const geralTags = new Set();

        courses.forEach(c => {{
            if (c.tags_aie_rev) {{
                c.tags_aie_rev.split(',').forEach(t => aieTags.add(t.trim()));
            }}
            if (c.tags_ampliadas) {{
                c.tags_ampliadas.split(',').forEach(t => geralTags.add(t.trim()));
            }}
        }});

        const filterAIE = document.getElementById('filterAIE');
        const filterGeral = document.getElementById('filterGeral');

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

        // Função de atualização da lista
        function updateView() {{
            const valAIE = filterAIE.value;
            const valGeral = filterGeral.value;

            // Filtragem
            const filtered = courses.filter(c => {{
                const matchAIE = valAIE === "" || (c.tags_aie_rev && c.tags_aie_rev.split(',').map(t=>t.trim()).includes(valAIE));
                const matchGeral = valGeral === "" || (c.tags_ampliadas && c.tags_ampliadas.split(',').map(t=>t.trim()).includes(valGeral));
                return matchAIE && matchGeral;
            }});

            // Atualização do texto de resumo
            let summary = `${{filtered.length}} cursos filtrados do total de ${{courses.length}}`;
            if (valAIE || valGeral) {{
                let filters = [];
                if (valAIE) filters.push(`o Tema da AIE: <strong>${{valAIE}}</strong>`);
                if (valGeral) filters.push(`temas: <strong>${{valGeral}}</strong>`);
                summary += ` com ${{filters.join(' e ')}}`;
            }}
            summary += ".";
            document.getElementById('summaryText').innerHTML = summary;

            // Renderização dos cards
            const listContainer = document.getElementById('courseList');
            listContainer.innerHTML = "";
            filtered.forEach(c => {{
                const div = document.createElement('div');
                div.className = 'course-card';
                
                let desc = c['curso-intro'] || c['Descrição'] || 'Sem descrição disponível.';
                
                // Montagem das tags visuais no card (opcional, mas bom para contexto)
                let tagsHTML = '';
                if (c.tags_aie_rev) {{
                    c.tags_aie_rev.split(',').forEach(t => {{
                        if(t.trim()) tagsHTML += `<span class="tag tag-aie">${{t.trim()}}</span>`;
                    }});
                }}
                if (c.tags_ampliadas) {{
                    c.tags_ampliadas.split(',').forEach(t => {{
                        if(t.trim()) tagsHTML += `<span class="tag">${{t.trim()}}</span>`;
                    }});
                }}

                div.innerHTML = `
                    <h3 class="course-title"><a href="${{c.url_curso}}" target="_blank">${{c.nome_curso}}</a></h3>
                    <div class="course-desc">${{desc}}</div>
                    <div class="course-tags">${{tagsHTML}}</div>
                `;
                listContainer.appendChild(div);
            }});
        }}

        // Listeners para os selects
        filterAIE.addEventListener('change', updateView);
        filterGeral.addEventListener('change', updateView);

        // Renderização inicial
        updateView();
    </script>
</body>
</html>
"""

output_html = '/mnt/data/Cursos_Filtro_EVG.html'
with open(output_html, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(output_html)