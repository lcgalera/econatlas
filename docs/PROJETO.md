# rotzx — documentação do projeto

Estado em 05/11/2026 (v0.13 e o globo com as decisões até D46). Este documento descreve o projeto inteiro: o que ele faz,
de onde vem cada dado, como as peças se encaixam e como operar. O porquê de cada escolha está em [`DECISOES.md`](DECISOES.md)
(D1–D46). Para continuar o projeto com um assistente de IA, use [`PROMPT.md`](PROMPT.md).

- Repositório: https://github.com/lcgalera/rotzx
- Site público: https://lcgalera.github.io/rotzx/
- O mundo visto do Brasil (globo): https://lcgalera.github.io/rotzx/globo/

---

## 1. O que é

rotzx é um projeto pessoal de **inteligência econômica com dados abertos e rastreáveis**. Tem três frentes, construídas
nesta ordem e todas ativas:

| Frente | Para quem | O que entrega | Onde |
|---|---|---|---|
| **Radar econômico e setorial** | quem acompanha economia e a indústria de materiais elétricos | séries oficiais (BCB, IBGE, Focus), previsões registradas antes dos dados saírem, placar público de acertos e erros | `rotzx/forecast`, `rotzx/analysis`, `registro/`, site público |
| **Radar de oportunidades (transmissão de energia)** | fornecedores do setor elétrico (B2B) | projetos do SIGET/ANEEL com evidência por regra, score explicado, histórico de mudanças, leilões e contexto econômico | `rotzx/intelligence`, `historico/`, `docs/03`–`08` |
| **O mundo visto do Brasil** | pessoas comuns que querem entender notícias e economia | globo interativo: cada país com a relação com o Brasil, economia, conflitos e manchetes organizadas | `rotzx/mundo`, `prototipos/globo/`, site `/globo/` |

O nome é **rotzx**, sempre em minúsculas (D25, D35). O nome antigo, EconAtlas, ainda funciona por compatibilidade
(`python -m econatlas` redireciona; o banco `data/econatlas.sqlite` é renomeado no primeiro uso).

## 2. Princípios (valem para tudo)

1. **Só dado real, com fonte.** Cada número mostra de onde veio e de quando é. Nada de valor inventado, nem em exemplo de interface.
2. **Interpretação nunca passa por fato.** Frases geradas a partir de números só descrevem; o que for interpretação aparece marcado.
   Na relação entre países não existe nota de "boa" ou "ruim": aparecem sinais medidos (D42).
3. **Proveniência.** Cada coleta guarda o arquivo bruto com SHA-256; cada versão dos dados é uma *vintage* (D2, D3).
4. **Previsão registrada antes e imutável.** Especificação fixa antes do backtest (D9); registro só recebe acréscimos e é verificado contra o git (D10, D23).
5. **Dado privado nunca vai para o público.** Séries da Macrodados são de uso pessoal (termos proíbem redistribuição): ficam fora do git,
   e duas guardas impedem vazamento — a varredura do build e os testes do repositório (D4, D13, D20).
6. **Notícias: só título, veículo, data e link.** O texto fica no site do veículo (D38, D40).
7. **Automático pode errar, e a página avisa.** Categorias, assuntos e países citados são marcados por palavras do título.
8. **Comunicação sem exagero** (D26, D27): frases de comparação sempre dizem a direção; nada de "comprovado" quando é associação.

## 3. Arquitetura

```
Fontes oficiais ──► providers/ e mundo/ (coleta, com novas tentativas e limite de ritmo)
                     │
                     ├─► storage.py  SQLite + arquivos brutos com SHA-256 (vintages)          ─┐
                     ├─► historico/*.csv  SIGET e leilões (só acréscimos, no git)              │
                     └─► prototipos/globo/dados/*.json|js  globo (comércio, relações, manchetes)│
                                                                                                ▼
forecast/, analysis/, intelligence/ ──► registro/*.csv (previsões)  ──► public_build.py ──► site/ (GitHub Pages)
                                                                     └► api.py + web/ (uso local, FastAPI)
```

- **Python 3.9**, monolítico (D1): FastAPI para uso local, HTML/JS sem build (ECharts e globe.gl por CDN com versão fixa).
- **SQLite** com gatilhos que impedem alterar previsões registradas (D10).
- **Dependências fixas** em `requirements.txt` (o Actions calcula com as mesmas bibliotecas do Mac).
- **Site público estático**: `rotzx publicar` gera `site/` só com dados abertos e termina com a varredura anti-vazamento (que lê também `.js`, D41).

### Pastas

| Pasta / arquivo | Conteúdo |
|---|---|
| `catalog/` | `series.json` (metadados conferidos nas fontes oficiais, D19), categorias de produto, perfil de demonstração, contexto do radar, contratos de leilões |
| `rotzx/providers/` | BCB/SGS, BCB/Expectativas (Focus), IBGE/SIDRA, arquivos, Macrodados (uso pessoal), CKAN/ANEEL, SIGET, leilões |
| `rotzx/forecast/` | modelos do IPCA (ingênuo, sazonal, SARIMA, Focus), backtest, faixa empírica, registro, previsão setorial |
| `rotzx/analysis/leading.py` | indicadores antecedentes fora da amostra (Clark-West + Holm, D14–D17) |
| `rotzx/intelligence/` | radar de oportunidades: evidências R1–R5, score, histórico do SIGET, leilões, contexto econômico, relatório |
| `rotzx/mundo/` | globo: Comex Stat, Banco Mundial, RSS, GDELT, ONU, OMC, UCDP, países e montagem dos dados |
| `rotzx/storage.py`, `transforms.py`, `payloads.py`, `quality.py`, `registro.py`, `public_build.py`, `api.py`, `cli.py` | núcleo |
| `web/` | interface do radar (local e pública) |
| `prototipos/globo/` | o globo: `index.html` (página única) e `dados/` (gerados) |
| `registro/` | previsões públicas e coletas (CSV, só acréscimos) |
| `historico/` | SIGET (coletas, eventos, estado) e leilões de transmissão (CSV, só acréscimos; ODbL) |
| `avaliacoes/` | avaliação humana de relevância do SIGET (conjunto de teste das regras) |
| `tests/` | pytest: 146 testes + 1 pulado (inclui as guardas do repositório público) |
| `docs/` | avaliações, diagnósticos, fontes, mercado, validação, motor, contexto, leilões, decisões, este documento e o prompt |
| `privado/`, `data/`, `site/`, `docs/DIARIO.md` | só locais, fora do git |

## 4. Fontes de dados

| Fonte | Usada em | Licença / termos | Observações |
|---|---|---|---|
| BCB/SGS e BCB/Expectativas (Focus) | radar econômico | dados abertos | câmbio e Selic mensal desde jul/1994 (D7) |
| IBGE/SIDRA | radar; PIM-PF seção 3.27 no setorial | dados abertos | 3.27 não mede investimento em transmissão |
| Macrodados | só uso pessoal, no Mac | proíbe redistribuição | importação manual, nunca automatizada (D13) |
| ANEEL SIGET (CKAN) | radar de oportunidades | ODbL | validado (D30), coleta semanal (D33) |
| ANEEL resultados de leilões | leilões de transmissão | dados abertos | planilha baixada à mão (o site tem desafio Cloudflare) (D37) |
| Comex Stat (MDIC) | globo: comércio | dados abertos | só o formato antigo `GET /general?filter=` funciona; ~12 s entre consultas |
| Banco Mundial (WDI) | globo: economia | CC BY 4.0 | PIB, crescimento, inflação, população |
| Feeds RSS (g1, Folha, BBC News Brasil, DW, Agência Brasil, RFI) | globo: manchetes | só título, veículo, data, link | fonte principal das manchetes (D40) |
| GDELT DOC 2.0 | globo: manchetes | aberto | complemento; limita IPs compartilhados |
| Votos na Assembleia Geral da ONU (Voeten, Strezhnev e Bailey, Harvard Dataverse) | globo: sinais da relação | CC0 | índice de Lijphart; sensível à pauta do ano (D42) |
| Disputas na OMC (site da OMC) | globo: sinais e visão externa | site oficial | lido como texto; países da UE aparecem pela UE (D42) |
| UCDP/PRIO Armed Conflict Dataset (Uppsala) | globo: conflitos armados | CC BY 4.0 | 25+ mortes em combate/ano; conta tropas de missões multinacionais como apoio (D43) |
| NASA Blue Marble (via `three-globe@2.45.6`) | imagem do planeta | domínio público (pacote MIT) | tingida de verde-petróleo |
| ISO 3166 (pycountry / iso-codes do Debian) | tabela de países | LGPL (dados ISO) | só para gerar `catalog/paises_mundo.csv` (D46) |
| Itamaraty — relações bilaterais | link no painel | site oficial | desafio anti-robô: só o índice, sem conferir página por país (D46) |
| Natural Earth 1:110m (via `world-atlas@2.0.2`) | contornos dos países | domínio público (pacote ISC) | ids = ISO 3166 numérico |

Ficaram de fora, com motivo registrado: FMI (barra acesso automatizado, D39); blocos e alianças pelo Wikidata (erros
encontrados, D42); API da UCDP (pede chave; o download não pede, D43).

## 5. Frente 1 — radar econômico e setorial

- **Radar Brasil:** 18 séries públicas (inflação, juros, câmbio, atividade, renda, crédito).
- **MacroForecast (IPCA):** ingênuo, sazonal ingênuo, SARIMA e Focus; backtest desde 2016; faixa de 80% empírica (erros dos últimos 60 meses, por horizonte, D21).
- **Setorial:** indústria de máquinas e materiais elétricos (IBGE 3.27) a 3 e 6 meses, especificação `setorial_v1` com hash (D18, D22).
  As faixas cobriram 61–69% no backtest para meta de 80%: o próximo passo é uma `setorial_v2`, sem mexer na v1.
- **Indicadores antecedentes:** avaliados fora da amostra, em tempo pseudo-real, com Clark-West e correção de Holm; achado só vale se replicar (D14–D17).
- **Página "Indústria de materiais elétricos: o que os juros indicam"** em linguagem simples, com todo número calculado dos dados (D24).

## 6. Frente 2 — radar de oportunidades (transmissão)

Fases (detalhes em `docs/02`, `03`, `06`, `07`, `08`):
1. **Fonte:** exploração do portal da ANEEL e validação do SIGET (D28, D30).
2. **Histórico:** coletas que só baixam o que mudou, eventos de mudança e estado em `historico/` (D33), toda segunda-feira (`radar-siget.yml`).
3. **Motor:** regras determinísticas R1–R5 com evidência por regra e score separado da evidência (D32); precisão de 80% (IC 58–92%) numa amostra aleatória avaliada à mão (D31).
4. **Leilões:** resultado dos leilões de transmissão como sinal antecipado, com ligação lote → contrato (D37).
5. **Contexto econômico** no relatório, fora do score (D34).

Pendente: conversas com compradores antes de construir interface (D29), nova amostra fora da amostra, janela por categoria.

## 7. Frente 3 — O mundo visto do Brasil (globo, retrato histórico)

Desde 05/11/2026 o globo é um **portfólio histórico**: a relação de todos os países com o Brasil de 1946 a 2025, coletada de uma vez,
sem atualização recorrente (D45, D46). As notícias estão **pausadas e escondidas** (`NOTICIAS = false` no topo do script); o código das
manchetes (seção 7.4) continua no repositório para voltar no futuro.

### 7.1 O que a pessoa vê

- **Barra de cima:** marca, cobertura dos dados, "Fontes e método", busca (todos os países).
- **Esquerda:** globo 3D (Blue Marble tingida, relevo, meridianos), Brasil sempre em verde; **Globo / Lista de países** (a lista substitui o
  globo sem WebGL); zoom; e o **controle do tempo**: indicador (**Comércio**, **Saldo**, **Votos na ONU**, **Conflitos**), barra de ano
  1946–2025 e **▶** (avança ano a ano). O globo pinta cada país pelo indicador no ano; sem dado = cinza; fora da cobertura da fonte, a
  legenda avisa ("comércio só desde 1997").
- **Direita, sem país aberto — "O Brasil e o mundo em [ano]":** abas **Ranking** (números do ano + lista clicável: maiores parceiros,
  maiores superávits e déficits, quem mais e menos votou com o Brasil, onde houve conflito), **Conflitos do ano** e **Fontes**.
- **Painel do país** (248 países): números do ano escolhido; gráficos de **comércio 1997–2025**, **votos na ONU 1946–2024** contra a mediana
  dos países e **conflitos por ano** (no território, como lado, com tropas) — clicar num ponto muda o ano; **produtos 2000 × 2025** de cada
  lado; **disputas na OMC** com o Brasil; **economia** (Banco Mundial); para os 20 países do primeiro protótipo, também os **sinais da
  relação**; link para as **relações bilaterais no Itamaraty** (índice oficial; o site não permite conferir a página de cada país).
- Link direto por país: `globo/#Argentina`. Esc ou "← Mundo" volta.

### 7.2 Dados

`catalog/paises_mundo.csv` (D46): uma linha por país — `iso_num` (id do mapa), `iso3`, `nome`, `comex` (códigos do Comex Stat, separados por
`|`), `cow` (ONU), `gw` (UCDP), `no_mapa`. Gerado por `rotzx mundo-codigos`; exceções escritas à mão em `rotzx/mundo/codigos.py`.

`prototipos/globo/dados/historia.json|js` (`window.HISTORIA`, ~1,3 MB), gerado por `rotzx mundo-atualizar --historico`:
- `paises[iso_num]`: `nome`, `iso3`, `no_mapa`
- `comercio`: `inicio` (1997), `fim`, `paises[iso_num].e|i` (US$ FOB por ano, `null` sem dado), `paises[iso_num].p[ano].e|i`
  (5 produtos: `[sh4, fob, participação]`, para 2000 e o último ano), `brasil.e|i` (totais), `sh4` (código → nome oficial)
- `onu`: `inicio` (1946), `fim`, `paises[iso_num]` (concordância 0–1 por ano), `mediana` (por ano)
- `conflitos`: `inicio`, `fim`, `paises[iso_num][ano]` = `{t: intensidade no território (0, 1, 2), l: nº como lado, a: nº com tropas}`,
  `por_ano[ano]` (lista: local, lados, tipo, disputa, território, guerra, países no mapa)
- `omc[iso_num]`: `via_ue`, `casos` (ds, ano, título, quem abriu, situação, link)
- `economia[iso_num]`: indicadores do Banco Mundial, valor mais recente
- `gerado_em`, `falhas`

`mundo.json` (D39–D43) continua com o painel detalhado dos 20 países do primeiro protótipo (sinais da relação, conflitos 2021–2025).

### 7.3 Coleta

Tudo de uma vez, à mão (`workflow_dispatch` do workflow Globo, ou localmente): o Comex Stat entrega o histórico inteiro em 6 consultas
(~2 min). Os arquivos da ONU e da UCDP ficam em `data/fontes/mundo/` (fora do git). Para refazer: `rotzx mundo-codigos` (se mudar a lista
de países) e `rotzx mundo-atualizar --historico`.

### 7.4 Notícias (pausadas)

Código pronto e testado: feeds RSS + GDELT (`rss.py`, `gdelt.py`), hora de Brasília, países citados (`MENCOES`), assuntos por palavras em
comum, linha do tempo e mapa de calor (D40, D44). Para voltar: `NOTICIAS = true` no globo e os agendamentos comentados em `globo.yml`.
Regras que continuam valendo: só título, veículo, data e link; país citado com acento e palavra inteira, sem termos ambíguos.

## 8. Automação (GitHub Actions)

| Workflow | Quando | O que faz |
|---|---|---|
| `rotina-mensal.yml` | dias 12 e 20, ou à mão | testes, registro, dados abertos, previsões, backtest, calibração, verificação do registro, build do site, commit e deploy no Pages |
| `radar-siget.yml` | toda segunda, ou à mão | histórico do SIGET, eventos, contexto, relatório (artefato 90 dias), commit de `historico/` |
| `globo.yml` | só à mão (agendamentos pausados, D45) | testes; retrato histórico (`--historico`) e commit dos dados |

Actions em Node 24 (D36). Python 3.9 no Actions e no Mac; não atualizar `setup-python` para v7 sem migrar o Python.
O site só muda quando a rotina mensal roda; as manchetes do globo ficam frescas sem republicar, porque a página lê os dados do repositório.

## 9. Linha de comando

`.venv/bin/python -m rotzx <comando>`:

| Comando | O que faz |
|---|---|
| `atualizar [séries]` | baixa as séries do catálogo (vintages com SHA-256) |
| `prever` / `prever-setor [--pessoal]` | registra as previsões do IPCA / setoriais |
| `backtest`, `calibrar-setorial`, `analisar-setor` | backtest do IPCA, cobertura das faixas setoriais, indicadores antecedentes |
| `publicar [--saida pasta]` | gera o site público com a varredura anti-vazamento |
| `registro-exportar` / `registro-importar` / `registro-verificar [--contra REF]` | registro público em CSV |
| `importar-macrodados arquivo.csv` | só no Mac, uso pessoal |
| `qualidade` | verificações de consistência |
| `fonte-explorar`, `siget-atualizar`, `siget-amostra`, `siget-historico-exportar/importar` | radar de oportunidades |
| `leiloes-importar arquivo.xlsx`, `contexto-atualizar`, `oportunidades [--perfil] [--top]` | leilões, contexto, relatório |
| `mundo-atualizar [--ano A] [--historico] [--sem-noticias] [--so-noticias] [--so-relacoes]` | dados do globo (`--historico`: retrato de todos os países) |
| `mundo-codigos [--atlas arquivo]` | gera `catalog/paises_mundo.csv` |
| `servir` | interface local em http://127.0.0.1:8000 (o globo fica em `/globo`) |

## 10. Como rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m rotzx atualizar
.venv/bin/python -m rotzx servir                 # http://127.0.0.1:8000
.venv/bin/python -m pytest -q                    # 146 passam, 1 pulado
```

Só o globo: `python3 -m http.server 8000 --directory prototipos/globo` e abrir http://localhost:8000 (precisa de internet para as bibliotecas e de WebGL;
sem WebGL, a lista de países assume).

## 11. Testes e guardas

- 146 testes (`tests/`), com fixtures sintéticas **no formato real** das fontes e valores inventados, marcados como tal.
- Guardas do repositório público: falham se um arquivo versionado estiver em pastas privadas ou citar um código do catálogo da Macrodados.
- Varredura do build: falha se o site tiver id, código, nome ou sequência de valores (inclusive derivados) de série pessoal.
- Globo: testes de marcação de países (inclusive falsos positivos), categorias, hora de Brasília, ONU, OMC, UCDP, isolamento de falhas entre fontes.
- A interface do globo foi verificada em Chromium sem tela (WebGL por software), em 1440×900 e 390×844.

## 12. Limitações conhecidas

- Globo: retrato fechado (sem atualização automática); fronteiras atuais para países que não existem mais; o painel detalhado dos
  "sinais da relação" só existe para os 20 países do primeiro protótipo.
- Agrupamento de assuntos, categorias e países citados são automáticos e podem errar (a página avisa).
- O índice de votos na ONU muda com a pauta do ano; por isso aparece a média de 5 anos.
- A OMC não dá encerramento formal a muitos casos antigos; o sinal conta disputas abertas nos últimos 5 anos, não "em aberto".
- A UCDP conta tropas de missões de paz como apoio: o Brasil aparece na República Centro-Africana ao lado de 38 países.
- Nomes de lados em conflitos e títulos de disputas na OMC ficam em inglês, como nas fontes.
- Faixas setoriais estreitas (61–69% de cobertura para meta de 80%).
- O registro é auditável, não impossível de reescrever: quem controla o repositório poderia reescrever o histórico do git (D27).

## 13. Próximos passos sugeridos

**Globo**
- "Por que importa para o Brasil": texto curto por país, com a fonte de cada número e a interpretação marcada.
- Camada de conflitos no mapa (precisa ligar os códigos da UCDP a todos os países do mapa).
- Mais países com dados (pelo ranking de comércio) e mais veículos nos feeds.
- Blocos e alianças de fonte oficial (os sites de cada bloco), em vez do Wikidata.

**Radar**
- `setorial_v2` com janela recente de erros; primeiras avaliações do IPCA (nov/2026) e da indústria (dez/2026).
- Validação com compradores (5 conversas) antes da interface do radar de oportunidades.

## 14. Índice das decisões

| Faixa | Assunto |
|---|---|
| D1–D13 | arquitetura, dados, previsões, identidade visual, Macrodados |
| D14–D24 | indicadores antecedentes, previsão setorial, metadados, site público, rotina mensal, página do setor |
| D25–D27, D35 | nome rotzx e comunicação sem exagero |
| D28–D34, D37 | radar de oportunidades (SIGET, avaliação, motor, histórico, contexto, leilões) |
| D36 | Actions em Node 24 |
| D38–D46 | o mundo visto do Brasil (globo, fontes, publicação, relações, conflitos, manchetes, pausa das notícias, retrato histórico) |
