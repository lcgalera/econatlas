# rotzx

Inteligência econômica com dados abertos e rastreáveis. O foco é o **Radar Setorial**: o que os juros indicam
para a produção da indústria de máquinas e materiais elétricos nos próximos 3 a 6 meses, com previsões registradas antes de os dados saírem
e um placar público de acertos e erros. O Radar Brasil (inflação, juros, câmbio, atividade, renda, crédito) dá o contexto.

- **Site público:** https://lcgalera.github.io/econatlas/ (comece por "Leitura do mês: indústria de materiais elétricos")
- **Registro de previsões:** [`registro/`](registro/), que só recebe acréscimos (veja "Como auditar o registro")

**Estado (v0.12, nov/2026)**

| Parte | O que tem |
|---|---|
| Radar Setorial | Página "Indústria de materiais elétricos: o que os juros indicam" em linguagem simples. Análise de indicadores antecedentes fora da amostra (Clark-West com correção de Holm). Previsões da indústria de máquinas e materiais elétricos (IBGE, PIM-PF, seção 3.27; não mede investimento em transmissão nem compras de concessionárias) a 3 e 6 meses, com especificação fixa `setorial_v1` e placar automático |
| MacroForecast | Previsões mensais do IPCA (ingênuo, sazonal ingênuo, SARIMA e Focus), backtest desde 2016 e faixa de 80% empírica, com cobertura medida antes e depois |
| Radar Brasil | 18 séries públicas do BCB, do IBGE e do Focus, com nomes e unidades conferidos nas fontes oficiais |
| Brasil x Mundo | Adiado (baixa diferenciação) |

## Dados abertos × uso pessoal

O repositório e o site usam **só dados abertos** (BCB, IBGE). Séries da Macrodados são de uso pessoal e só
existem no computador do autor, porque os Termos de uso dela proíbem redistribuição. Elas ficam fora do git
(`privado/`, `data/`, `docs/DIARIO.md`). Duas verificações garantem isso:

- **No build do site:** `econatlas publicar` termina com uma varredura que falha se aparecer id, código, nome ou sequência de valores (inclusive derivados) de qualquer série pessoal.
- **No repositório:** dois testes falham se algum arquivo versionado estiver nessas pastas ou contiver um código do catálogo da Macrodados.

## Como rodar localmente

```bash
cd ~/Claude/econatlas
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # só na primeira vez
.venv/bin/python -m econatlas atualizar     # baixa/atualiza as séries abertas (~1 min)
.venv/bin/python -m econatlas servir        # interface completa em http://127.0.0.1:8000
```

| Comando (`.venv/bin/python -m econatlas …`) | O que faz |
|---|---|
| `atualizar [séries]` | Baixa as séries do catálogo (BCB, IBGE, Focus); cada versão nova fica guardada com SHA-256 |
| `prever` | Registra as previsões do IPCA do mês (imutáveis) |
| `prever-setor` | Registra as previsões setoriais públicas (IBGE 3.27) e mostra o placar |
| `prever-setor --pessoal` | Só no Mac: registra as previsões de CNI e ABIMAQ (Macrodados) |
| `backtest` | Refaz o backtest do IPCA e mede a cobertura das faixas |
| `analisar-setor [setores]` | Indicadores antecedentes por série-alvo |
| `calibrar-setorial` | Cobertura das faixas das previsões setoriais (~1–5 min) |
| `publicar [--saida pasta]` | Gera o site público estático em `./site`, com a verificação anti-vazamento |
| `registro-exportar` / `registro-importar` | Grava o registro em CSV (só acrescenta) / carrega os CSVs no banco |
| `registro-verificar [--contra REF]` | Falha se uma linha antiga do registro mudou no git ou diverge do banco |
| `importar-macrodados arquivo.csv` | Só no Mac: importa exportações da Macrodados (uso pessoal) |
| `qualidade` | Verificações de consistência dos dados |
| `fonte-explorar TERMO [--conjunto NOME]` | Fase 1 do radar de oportunidades: lista conjuntos do portal da ANEEL ou baixa um conjunto e gera o perfil dos campos em `data/fontes/` (ver `docs/03-fonte-siget.md`) |

Testes: `.venv/bin/python -m pytest -q`.

## Versão pública

```bash
.venv/bin/python -m econatlas publicar
python3 -m http.server 8010 --directory site   # abrir http://localhost:8010
```

`site/` é HTML + JSON (mais um SQLite público) e não depende do servidor FastAPI. A publicação oficial é feita pelo GitHub Actions no GitHub Pages; não é preciso publicar à mão.

## Rotina mensal (GitHub Actions)

O workflow [`.github/workflows/rotina-mensal.yml`](.github/workflows/rotina-mensal.yml) roda **todo dia 12** (depois do IPCA) e **todo dia 20** (segunda passada, para a produção industrial do IBGE). Também dá para rodar à mão em *Actions › Rotina mensal › Run workflow*, ou no terminal:

```bash
gh workflow run rotina-mensal.yml
```

A cada execução, num banco novo:
1. roda os testes;
2. carrega o registro de `registro/*.csv`;
3. baixa só dados abertos;
4. registra as previsões do mês (`prever` e `prever-setor`);
5. refaz o backtest e a calibração;
6. acrescenta as linhas novas ao registro e roda `registro-verificar --contra HEAD`;
7. gera o site, faz o commit de `registro/` (autor `github-actions[bot]`) e publica no Pages.

A importação da Macrodados é manual e fica fora da automação.

**Como auditar o registro.** Cada previsão vira uma linha em `registro/previsoes_*.csv`, com data de registro, especificação do modelo e o SHA-256 dos dados usados. `registro/coletas.csv` lista cada versão de dados. O verificador falha se qualquer linha antiga mudar, e o histórico do git mostra quando cada linha entrou. Isso torna o registro auditável, não impossível de reescrever: quem controla o repositório ainda poderia reescrever o histórico do git. Um registro externo (ex.: carimbo de tempo de terceiros) aumentaria a garantia, se for preciso (D27).

**No Mac do autor**, para trazer as previsões oficiais para o banco local:

```bash
git pull && .venv/bin/python -m econatlas registro-importar
```

## Nome

O produto se chama **rotzx** (sempre em minúsculas). O repositório, o endereço do site, o pacote Python e os comandos
continuam com o identificador interno `econatlas` por enquanto, para não quebrar o site público, o registro e a rotina mensal (D25).

## Estrutura

```
catalog/series.json        catálogo público (metadados conferidos nas fontes oficiais)
econatlas/
  providers/               BCB/SGS, BCB/Expectativas, IBGE/SIDRA, arquivos (e exportações da Macrodados), ckan (exploração de fontes)
  storage.py               SQLite com versões (vintages) e arquivos brutos com SHA-256
  transforms.py            transformações declaradas
  payloads.py              dados que a interface consome (API local e site público)
  forecast/                IPCA: modelos, backtest, Focus, faixa empírica, registro; setorial.py
  analysis/leading.py      indicadores antecedentes (fora da amostra, Clark-West + Holm)
  registro.py              registro público em CSV (só acréscimos) e verificação
  public_build.py          site público estático + verificação anti-vazamento
  api.py, cli.py           servidor local e linha de comando
web/                       interface (HTML/JS + ECharts, sem build); texto.js: frases de comparação de erro, testadas
registro/                  registro público de previsões (versionado)
tests/                     pytest (inclui as guardas do repositório público)
docs/01-avaliacao-inicial.md, 02-diagnostico-intelligence.md, 03-fonte-siget.md, 04-mercado-e-posicionamento.md,
05-validacao-com-compradores.md, DECISOES.md
privado/, data/, site/, docs/DIARIO.md   só locais (fora do git)
```

## Pendências

- **Validação com compradores (antes de construir a interface):** 5 conversas de descoberta com o roteiro de `docs/05-validacao-com-compradores.md`; resultados em `privado/validacao/`, fora do git (D29).
- **Radar de oportunidades (Fase 1):** validar o SIGET da ANEEL com `fonte-explorar`. O ambiente de nuvem não alcança o portal; rodar no Mac ou liberar o domínio (`docs/03-fonte-siget.md`).
- **Macrodados:** aguardar a resposta sobre uso de dados derivados e uso comercial. Até lá, nada dela em material público.
- **Faixas da indústria de materiais elétricos estreitas:** cobriram 61–69% no backtest, para uma meta de 80%. Testar uma janela recente de erros, como a do IPCA, como especificação nova (`setorial_v2`), sem alterar a v1.
- **Defasagens de divulgação** (IBGE, CNI, FGV): são premissas do teste em tempo real; conferir nos calendários oficiais.
- **ABIMAQ e CNI** (uso pessoal): previsões só locais. A causa do descolamento da série CNI de máquinas em 2022–23 não pode ser verificada com os dados disponíveis.
- **IPFF** (Índice de Pressão Financeira das Famílias): metodologia proposta em `docs/01-avaliacao-inicial.md`, ainda não construído.
- **GitHub Actions:** o workflow usa Python 3.9, igual ao Mac. Se o GitHub deixar de oferecer essa versão, mudar `python-version` para 3.12 (as versões fixadas são compatíveis). O rótulo `ubuntu-latest` passará ao Ubuntu 26 a partir de out/2026.
- **Primeiras avaliações:** IPCA de out/2026 (por volta de 10/nov) e produção da indústria de materiais elétricos de out/2026 (dezembro).

Decisões e motivos: [`docs/DECISOES.md`](docs/DECISOES.md). Análises econômicas são associações preditivas, não causalidade, e não constituem recomendação financeira ou de investimento.
