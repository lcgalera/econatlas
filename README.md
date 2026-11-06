# rotzx

Inteligência econômica com dados abertos e rastreáveis. O foco é o **Radar Setorial**: o que os juros indicam
para a produção da indústria de máquinas e materiais elétricos nos próximos 3 a 6 meses, com previsões registradas antes de os dados saírem
e um placar público de acertos e erros. O Radar Brasil (inflação, juros, câmbio, atividade, renda, crédito) dá o contexto.

- **Site público:** https://lcgalera.github.io/rotzx/ é o atlas "Como o Brasil se conecta ao mundo" (parceiros e produtos do comércio brasileiro desde 1997, com seletor de ano, comparação e explorador por produto; `prototipos/globo/`). Desde a D53, os radares e o placar de previsões não são mais publicados; continuam no repositório (`rotzx publicar --completo` gera o site antigo). Links antigos em `/globo/` redirecionam para a raiz.
- **Registro de previsões:** [`registro/`](registro/), que só recebe acréscimos (veja "Como auditar o registro")
- **Documentação completa:** [`docs/PROJETO.md`](docs/PROJETO.md) · **prompt para continuar com uma IA:** [`docs/PROMPT.md`](docs/PROMPT.md)

**Estado (v0.12, nov/2026)**

| Parte | O que tem |
|---|---|
| Radar Setorial | Página "Indústria de materiais elétricos: o que os juros indicam" em linguagem simples. Análise de indicadores antecedentes fora da amostra (Clark-West com correção de Holm). Previsões da indústria de máquinas e materiais elétricos (IBGE, PIM-PF, seção 3.27; não mede investimento em transmissão nem compras de concessionárias) a 3 e 6 meses, com especificação fixa `setorial_v1` e placar automático |
| MacroForecast | Previsões mensais do IPCA (ingênuo, sazonal ingênuo, SARIMA e Focus), backtest desde 2016 e faixa de 80% empírica, com cobertura medida antes e depois |
| Radar Brasil | 18 séries públicas do BCB, do IBGE e do Focus, com nomes e unidades conferidos nas fontes oficiais |
| Atlas comercial (globo) | De quem o Brasil depende para vender e comprar: parceiros, produtos (SH4), concentração e mudanças desde 1997 (Comex Stat), com contexto diplomático (ONU, OMC, conflitos) e econômico; explorar por produto, comparar parceiros, bandeiras, estado na URL. Notícias pausadas (D38–D47) |
| Brasil x Mundo | Adiado (baixa diferenciação) |

## Dados abertos × uso pessoal

O repositório e o site usam **só dados abertos** (BCB, IBGE). Séries da Macrodados são de uso pessoal e só
existem no computador do autor, porque os Termos de uso dela proíbem redistribuição. Elas ficam fora do git
(`privado/`, `data/`, `docs/DIARIO.md`). Duas verificações garantem isso:

- **No build do site:** `rotzx publicar` termina com uma varredura que falha se aparecer id, código, nome ou sequência de valores (inclusive derivados) de qualquer série pessoal.
- **No repositório:** dois testes falham se algum arquivo versionado estiver nessas pastas ou contiver um código do catálogo da Macrodados.

## Como rodar localmente

```bash
cd ~/Claude/econatlas   # ou o nome que a pasta tiver no seu Mac
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # só na primeira vez
.venv/bin/python -m rotzx atualizar     # baixa/atualiza as séries abertas (~1 min)
.venv/bin/python -m rotzx servir        # interface completa em http://127.0.0.1:8000
```

| Comando (`.venv/bin/python -m rotzx …`) | O que faz |
|---|---|
| `atualizar [séries]` | Baixa as séries do catálogo (BCB, IBGE, Focus); cada versão nova fica guardada com SHA-256 |
| `prever` | Registra as previsões do IPCA do mês (imutáveis) |
| `prever-setor` | Registra as previsões setoriais públicas (IBGE 3.27) e mostra o placar |
| `prever-setor --pessoal` | Só no Mac: registra as previsões de CNI e ABIMAQ (Macrodados) |
| `backtest` | Refaz o backtest do IPCA e mede a cobertura das faixas |
| `analisar-setor [setores]` | Indicadores antecedentes por série-alvo |
| `calibrar-setorial` | Cobertura das faixas das previsões setoriais (~1–5 min) |
| `publicar [--saida pasta] [--completo]` | Gera o site público em `./site` (só o atlas, na raiz; `--completo`: site antigo com os radares), com a verificação anti-vazamento |
| `registro-exportar` / `registro-importar` | Grava o registro em CSV (só acrescenta) / carrega os CSVs no banco |
| `registro-verificar [--contra REF]` | Falha se uma linha antiga do registro mudou no git ou diverge do banco |
| `importar-macrodados arquivo.csv` | Só no Mac: importa exportações da Macrodados (uso pessoal) |
| `qualidade` | Verificações de consistência dos dados |
| `fonte-explorar TERMO [--conjunto NOME]` | Fase 1 do radar de oportunidades: lista conjuntos do portal da ANEEL ou baixa um conjunto e gera o perfil dos campos em `data/fontes/` (ver `docs/03-fonte-siget.md`) |
| `siget-atualizar` | Fase 2: baixa só os arquivos do SIGET que a ANEEL atualizou e registra versões e eventos de mudança no histórico |
| `siget-historico-exportar` / `siget-historico-importar` | Grava o histórico em `historico/*.csv` (só acrescenta) / carrega os CSVs num banco novo |
| `leiloes-importar arquivo.xlsx` | Importa a planilha oficial de resultados de leilões de transmissão (baixada à mão no gov.br/aneel) para `historico/leiloes_transmissao.csv` (`docs/08-leiloes.md`) |
| `contexto-atualizar` | Fase 5: baixa só as séries públicas do contexto econômico do radar (`catalog/contexto_radar.json`) |
| `oportunidades [--perfil arq.json] [--top 30]` | Fase 3: oportunidades do SIGET para um perfil, com evidência por regra e score explicado; gera `relatorio.html` e CSVs em `data/relatorios/` (`docs/06-motor-de-oportunidades.md`) |
| `mundo-atualizar [--ano A] [--historico] [--sem-noticias] [--so-noticias] [--so-relacoes]` | Dados do globo em `prototipos/globo/dados/`; `--historico` gera o retrato de todos os países (`docs/PROJETO.md`, seção 7) |
| `mundo-codigos [--atlas arquivo]` | Gera `catalog/paises_mundo.csv`, a tabela que liga Comex Stat, ONU, UCDP e o mapa (D46) |
| `siget-amostra [--n 20] [--aleatoria]` | Visão por empreendimento do SIGET (ANEEL, licença ODbL) e amostra para avaliação manual, a partir dos arquivos baixados por `fonte-explorar` |

Testes: `.venv/bin/python -m pytest -q`.

## Versão pública

```bash
.venv/bin/python -m rotzx publicar
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
git pull && .venv/bin/python -m rotzx registro-importar
```

## Nome

O produto se chama **rotzx** (sempre em minúsculas), assim como o repositório (`lcgalera/rotzx`), o site
(`lcgalera.github.io/rotzx`), o pacote Python (`rotzx/`) e os comandos (`python -m rotzx …`), desde a v0.13 (D35).
O nome antigo continua funcionando por compatibilidade: `python -m econatlas …` redireciona para `rotzx`, e o banco
local `data/econatlas.sqlite` é renomeado para `data/rotzx.sqlite` no primeiro uso.

**No Mac, uma vez só**, depois do rename do repositório:

```bash
cd ~/Claude/econatlas && git remote set-url origin https://github.com/lcgalera/rotzx && git pull
```

A pasta local pode continuar se chamando `econatlas`; se quiser renomear, é só renomear a pasta (o `.venv` precisa ser recriado).

## Estrutura

```
catalog/series.json        catálogo público (metadados conferidos nas fontes oficiais)
catalog/product_categories.json, perfil_demo.json   categorias de produto e perfil de demonstração do radar
rotzx/
  providers/               BCB/SGS, BCB/Expectativas, IBGE/SIDRA, arquivos (e exportações da Macrodados), ckan (exploração de fontes), aneel_siget (visão por empreendimento)
  intelligence/            motor de oportunidades: evidências (R1–R5), score, histórico, contexto econômico e relatório
  mundo/                   globo: Comex Stat, Banco Mundial, RSS, GDELT, ONU, OMC, UCDP, países citados e montagem dos dados
  storage.py               SQLite com versões (vintages) e arquivos brutos com SHA-256
  transforms.py            transformações declaradas
  payloads.py              dados que a interface consome (API local e site público)
  forecast/                IPCA: modelos, backtest, Focus, faixa empírica, registro; setorial.py
  analysis/leading.py      indicadores antecedentes (fora da amostra, Clark-West + Holm)
  registro.py              registro público em CSV (só acréscimos) e verificação
  public_build.py          site público estático + verificação anti-vazamento
  api.py, cli.py           servidor local e linha de comando
web/                       interface (HTML/JS + ECharts, sem build); texto.js: frases de comparação de erro, testadas
prototipos/globo/          o mundo visto do Brasil: index.html (página única) e dados/ (gerados pelo workflow Globo)
registro/                  registro público de previsões (versionado)
avaliacoes/                avaliações humanas de relevância (conjunto de teste das regras do radar)
historico/                 histórico do SIGET: coletas, eventos de mudança e estado (CSV, só acréscimos; ODbL)
tests/                     pytest (inclui as guardas do repositório público)
docs/01-avaliacao-inicial.md, 02-diagnostico-intelligence.md, 03-fonte-siget.md, 04-mercado-e-posicionamento.md,
05-validacao-com-compradores.md, 06-motor-de-oportunidades.md, 07-contexto-economico.md, 08-leiloes.md, DECISOES.md,
PROJETO.md (documentação completa), PROMPT.md (prompt para continuar com uma IA)
privado/, data/, site/, docs/DIARIO.md   só locais (fora do git)
```

## Radar SIGET (GitHub Actions, semanal)

O workflow [`.github/workflows/radar-siget.yml`](.github/workflows/radar-siget.yml) roda **toda segunda-feira** (ou à mão, em *Actions › Radar SIGET › Run workflow*):
carrega `historico/`, baixa o que mudou no SIGET, registra os eventos, acrescenta ao histórico, atualiza as séries do contexto, gera o relatório do perfil de demonstração
(artefato `relatorio-radar` da execução, guardado por 90 dias) e faz o commit de `historico/`.

## Globo (GitHub Actions, só à mão)

O workflow [`.github/workflows/globo.yml`](.github/workflows/globo.yml) não tem mais agendamento (D45): rodado à mão, refaz o retrato histórico
(`mundo-atualizar --historico`) e faz o commit de `prototipos/globo/dados/`. A coleta das notícias está pausada; os agendamentos ficam
comentados no arquivo para quando elas voltarem.

## Pendências

- **Validação com compradores (antes de construir a interface):** 5 conversas de descoberta com o roteiro de `docs/05-validacao-com-compradores.md`; resultados em `privado/validacao/`, fora do git (D29).
- **Leilões:** importar a planilha da ANEEL depois de cada leilão (`rotzx leiloes-importar`) e atualizar `catalog/leiloes_contratos.json` quando os contratos aparecerem no SIGET; resolver os lotes 1 e 2 do 01/2026 (D37).
- **Radar de oportunidades:** SIGET validado (D30); amostra aleatória com 80% de precisão, IC 58–92% (D31); motor e relatório da Fase 3 prontos (D32). Próximos: amostra nova para medir a precisão fora da amostra; janela por categoria validada com compradores; segunda coleta e histórico (Fase 2).
- **Macrodados:** aguardar a resposta sobre uso de dados derivados e uso comercial. Até lá, nada dela em material público.
- **Faixas da indústria de materiais elétricos estreitas:** cobriram 61–69% no backtest, para uma meta de 80%. Testar uma janela recente de erros, como a do IPCA, como especificação nova (`setorial_v2`), sem alterar a v1.
- **Defasagens de divulgação** (IBGE, CNI, FGV): são premissas do teste em tempo real; conferir nos calendários oficiais.
- **ABIMAQ e CNI** (uso pessoal): previsões só locais. A causa do descolamento da série CNI de máquinas em 2022–23 não pode ser verificada com os dados disponíveis.
- **IPFF** (Índice de Pressão Financeira das Famílias): metodologia proposta em `docs/01-avaliacao-inicial.md`, ainda não construído.
- **GitHub Actions:** as actions rodam em Node 24 (checkout v5, setup-python v6, upload-artifact v6, upload-pages-artifact v5, deploy-pages v5; D36). O `setup-python` v7 remove versões do Python fora de suporte, como a 3.9: não atualizar sem antes migrar o Python. O workflow usa Python 3.9, igual ao Mac. Se o GitHub deixar de oferecer essa versão, mudar `python-version` para 3.12 (as versões fixadas são compatíveis). O rótulo `ubuntu-latest` passará ao Ubuntu 26 a partir de out/2026.
- **Primeiras avaliações:** IPCA de out/2026 (por volta de 10/nov) e produção da indústria de materiais elétricos de out/2026 (dezembro).

Decisões e motivos: [`docs/DECISOES.md`](docs/DECISOES.md). Análises econômicas são associações preditivas, não causalidade, e não constituem recomendação financeira ou de investimento.
