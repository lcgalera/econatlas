# EconAtlas

Plataforma pessoal de inteligência econômica: dados rastreáveis, análise quantitativa e, mais adiante, IA como assistente de pesquisa.

**Estado atual (v0.8, nov/2026):** Radar Brasil com 18 séries públicas (BCB, IBGE, Focus). MacroForecast com previsões mensais do IPCA registradas sem possibilidade de alteração, backtest desde 2016 e comparação com o Focus. Radar Setorial com 30 séries da Macrodados (uso pessoal) e 2 do IBGE, análise de indicadores antecedentes em 5 séries e previsões setoriais registradas todo mês. Brasil x Mundo adiado. Relatório da sessão 1: https://claude.ai/artifact/Tc4SxFRhTnmMHvEbrhk3kM

## Como rodar

```bash
cd ~/Claude/econatlas
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # só na primeira vez
.venv/bin/python -m econatlas atualizar     # baixa/atualiza as séries (~1–2 min)
.venv/bin/python -m econatlas servir        # abre em http://127.0.0.1:8000
```

Outros comandos:

```bash
.venv/bin/python -m econatlas qualidade                     # verificações de consistência
.venv/bin/python -m econatlas prever                        # registra as previsões do mês: IPCA e setoriais (após o IPCA sair)
.venv/bin/python -m econatlas backtest                      # refaz o backtest (~1–2 min)
.venv/bin/python -m econatlas analisar-setor [setores]      # indicadores antecedentes (eletrico, eletrico_pim, maquinas, maquinas_abimaq, maquinas_pim)
.venv/bin/python -m econatlas calibrar-setorial             # cobertura das faixas das previsões setoriais (~5 min)
.venv/bin/python -m pytest -q                               # testes automatizados
.venv/bin/python -m econatlas importar-macrodados ~/Claude/macrodados_XXXX.CSV   # exportação da Macrodados (várias séries)
.venv/bin/python -m econatlas importar ~/Downloads/export.csv \
    --id md_minha_serie --nome "Nome da série" --unidade "%" \
    --periodicidade mensal --instituicao "IBGE" --fonte "Macrodados (exportação)"
```

A documentação automática da API fica em http://127.0.0.1:8000/docs.

## Estrutura

```
catalog/series.json        catálogo público: metadados de cada série
econatlas/
  catalog.py               modelo de metadados + catálogo local (importações)
  providers/               bcb_sgs, ibge_sidra, arquivo (CSV/Excel); um módulo por fonte
  storage.py               SQLite com versões (vintages), arquivos brutos com SHA-256
  transforms.py            transformações declaradas (var. 12m, acumulado, deflação...)
  quality.py               verificações de qualidade
  forecast/                modelos, backtest, Focus e registro imutável de previsões
  analysis/                análises (indicadores antecedentes setoriais)
scripts/                   investigações reprodutíveis (ex.: divergencia_maquinas.py)
  api.py                   FastAPI (JSON + interface)
  cli.py                   linha de comando
web/                       interface (HTML/JS + ECharts, sem build)
tests/                     pytest
data/                      banco, arquivos brutos e importações (não versionar)
docs/
  01-avaliacao-inicial.md  avaliação, mercado, Macrodados, arquitetura, catálogo, MVP, cronograma, monetização
  DECISOES.md              registro de decisões
  DIARIO.md                progresso, problemas e próximos passos (ler primeiro ao retomar)
```

## Princípios

- Todo número exibido informa a série, a fonte, a versão coletada e a transformação aplicada.
- Dados de uso pessoal (ex.: exportações da Macrodados) são marcados como tal e não podem ser baixados pela interface.
- Nenhum módulo exibe dados simulados como se fossem reais.
