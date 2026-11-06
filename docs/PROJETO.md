# rotzx — documentação do projeto

Estado em 05/11/2026 (v0.13 e o globo com as decisões até D47). Este documento descreve o projeto inteiro: o que ele faz,
de onde vem cada dado, como as peças se encaixam e como operar. O porquê de cada escolha está em [`DECISOES.md`](DECISOES.md)
(D1–D52). Para continuar o projeto com um assistente de IA, use [`PROMPT.md`](PROMPT.md).

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
| Newsreader e IBM Plex Sans (Google Fonts) | tipografia do atlas | SIL Open Font License | serifa nos títulos, sans no texto (D49) |
| ISO 3166 (pycountry / iso-codes do Debian) | tabela de países | LGPL (dados ISO) | só para gerar `catalog/paises_mundo.csv` (D46) |
| flag-icons 7.5.0 | bandeiras | MIT | bandeira atual, não a do ano (D47) |
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

## 7. Frente 3 — Atlas "Como o Brasil se conecta ao mundo" (globo)

Pergunta-guia: **de quem o Brasil depende para vender e para comprar — e como isso mudou ao longo do tempo?** (D47).
A página é `prototipos/globo/index.html`, publicada em `/globo/` pelo build, que copia a pasta inteira, exceto o `LEIAME.md`. É uma página
única, sem build: globe.gl 2.46.2, ECharts 5.5.0, bandeiras flag-icons 7.5.0 e dados em `dados/*.js`. É um retrato fechado, sem atualização
automática (D45). As notícias estão pausadas (seção 7.5).

### 7.1 O que a pessoa vê

- **Início:**
  - frase do produto;
  - resumo do comércio do Brasil no ano: exportações, importações, saldo e corrente, mais a concentração (maior destino e maior origem,
    5 maiores), com o denominador dito;
  - perguntas que executam ações: maiores parceiros, para onde vão as exportações, de onde vêm as importações, quem ganhou importância
    desde 2000, a China desde 2000, fertilizantes, soja em 2000 × 2025, China × EUA;
  - os 5 maiores parceiros e o acesso à lista completa.
- **Mapa e controles:**
  - métricas: exportações, importações, corrente, participação, mudança em p.p. e, em segundo plano, contexto (votos na ONU, conflitos);
  - ano de 1997 a 2025 com ▶, e anos discretos quando a métrica é um produto;
  - legenda com o significado das cores e da escala, fixa para todos os anos (exceto a de mudança, ajustada ao par de anos e dita).
  O globo destaca o país escolhido. A **Lista** é a alternativa sem 3D e assume sozinha sem WebGL.
- **Painel do país (248 países e territórios):**
  - bandeira, nome (com marca de território), ano de referência e posição no ranking da métrica;
  - resumo por regras fixas;
  - **Relação comercial:** valores e participações de 1997 a 2025, com tabela alternativa aos gráficos;
  - **Produtos e concentração:** 10 maiores de cada lado em 2000, 2010 e 2025, a soma dos 5 maiores e a parte do país no total do produto;
  - **Contexto diplomático:** ONU, OMC, conflitos, link do Itamaraty e ficha econômica recolhível.
- **Explorar por produto:** busca, exportações ou importações, maiores destinos ou origens com participação e "outros", série de 1997 a
  2025. Clicar num parceiro abre o país mantendo o produto.
- **Comparar dois parceiros:** tabela no ano, participação na corrente no mesmo eixo e 5 maiores produtos lado a lado.
- **Fontes e método:** fonte, cobertura, unidade, definições, critérios, limitações e licenças.
- **Espaço de leitura (D48):** nas análises, o conteúdo ganha mais largura. "Ampliar análise" recolhe o mapa, e uma barra no topo da análise
  mostra o caminho (ex.: Início › Fertilizantes › Importações › Rússia), o ano e o botão. No celular, a análise abre com o mapa recolhido.
- **Dois níveis (D48):** valor, participação com o que ela representa, ano e fonte ficam visíveis. Código SH4, descrição oficial, fórmula,
  denominador e limitações ficam em "Detalhes" e "Sobre este dado".
- **Produto → país (D48):** um fornecedor ou destino aberto pelo explorador mostra o país visto por aquele produto, fluxo e ano, com volta à
  exploração (filtros e posição de leitura) e acesso à relação completa. A busca do topo abre sempre o painel geral.
- **Identidade editorial (D49):**
  - tema claro principal, com o escuro pelo sistema ou pelo botão do cabeçalho; cores só por tokens CSS;
  - Newsreader nos títulos e IBM Plex Sans no texto;
  - globo cartográfico com oceano liso, terra neutra para "sem registro" e o país selecionado em tinta escura;
  - entrada com uma exploração principal com gráfico e duas secundárias;
  - faixa de indicadores no país, rankings com barra na linha e comparação em duas colunas com cores de série fixas.
- **Acabamento (D50):**
  - leitura com cerca de 65% da largura;
  - o país aberto por um produto tem abertura própria (posição e parte naquele produto e fluxo);
  - atalhos de produto com rótulos curtos;
  - um só controle de ano ("Ano do recorte"), com aviso quando o ano pedido não tem distribuição por parceiro.
- **Versão estável (D51):**
  - o recorte por produto diz quantos parceiros estão detalhados, quantos a fonte registra e quanto está em "Outros";
  - os países fora do recorte aparecem como "fora do recorte detalhado", nunca como zero ou "sem registro";
  - avisos para ano ou parâmetro incompatível;
  - falha de carga com "Tentar de novo";
  - carregamento com a silhueta do Brasil e a assinatura "Pátria amada, Brasil." na entrada.
- **URL:** `#pais=RUS&prod=g-fertilizantes&fluxo=i&ano=2025` (país visto por um produto), `#ver=comparar&a=CHN&b=USA`, `&amplo=1`,
  `&aba=produtos`, `#ver=ranking&m=mud&base=2000`. Voltar, avançar e recarregar mantêm o estado; `#China` e `vs=` continuam funcionando.

### 7.2 Definições (o denominador muda; a tela sempre diz qual)

| Medida | Cálculo |
|---|---|
| Concentração de destinos | exportações para o país ÷ exportações totais do Brasil |
| Concentração de origens | importações do país ÷ importações totais do Brasil |
| Participação (mapa) | corrente com o país ÷ corrente total do Brasil |
| Mudança | participação no ano − participação no ano-base, em p.p. (só com comércio registrado nos dois anos) |
| Composição bilateral | produto ÷ total trocado com o país (total exato: vem da distribuição completa) |
| Fornecedores de um produto | importações do produto vindas do país ÷ importações totais do produto |

Não há nota de risco nem de dependência: participação alta indica concentração, não vulnerabilidade. Os totais do Brasil incluem operações sem
país definido.

### 7.3 Dados

- `catalog/paises_mundo.csv`: `iso_num`, `iso3`, `iso2`, `nome`, `tipo` (país ou território), `comex`, `cow`, `gw`, `no_mapa`.
  Gerado por `rotzx mundo-codigos`.
- `dados/historia.json|js` (`window.HISTORIA`), gerado por `rotzx mundo-atualizar --historico`:
  - `comercio`: séries por país de 1997 a 2025 (`e`, `i`), totais do Brasil, `anos_produtos` ([2000, 2010, 2025]);
  - por país e ano, `p[ano][e|i] = {t, n, top: [[sh4, valor] ×10]}`;
  - `sh4` (nomes oficiais) e `curtos` (nomes revisados);
  - `onu`, `conflitos`, `omc`, `economia` (D46).
- `dados/produtos.json|js` (`window.PRODUTOS`, carregado sob demanda): em `itens[código]`,
  - `nome`, `oficial` e, nos grupos, `grupo`;
  - séries `e` e `i` de 1997 a 2025;
  - `p[ano][e|i] = {t, n, top: [[iso_num, valor] ×12]}`.
- Ano sem registro = `null`.

### 7.4 Coleta

Tudo de uma vez, à mão (`workflow_dispatch` do workflow Globo, ou localmente), com cerca de 10 consultas ao Comex Stat:
- séries por país;
- séries por produto;
- pares país × produto em 2000, 2010 e 2025.
Os arquivos brutos da ONU e da UCDP ficam em `data/fontes/mundo/`, fora do git.

### 7.5 Notícias (pausadas)

Coletores e testes em `rotzx/mundo/` (`rss.py`, `gdelt.py`, `paises.py`: `MENCOES` e `citados`). A interface antiga das manchetes (assuntos,
linha do tempo, mapa de calor) está no histórico do git: `prototipos/globo/index.html` no commit `d193691`. Regras que continuam valendo: só
título, veículo, data e link; país citado com acento e palavra inteira.

## 8. Automação (GitHub Actions)

| Workflow | Quando | O que faz |
|---|---|---|
| `rotina-mensal.yml` | dias 12 e 20, ou à mão | testes, registro, dados abertos, previsões, backtest, calibração, verificação do registro, build do site, commit e deploy no Pages |
| `radar-siget.yml` | toda segunda, ou à mão | histórico do SIGET, eventos, contexto, relatório (artefato 90 dias), commit de `historico/` |
| `globo.yml` | só à mão (agendamentos pausados, D45) | testes; retrato histórico (`--historico`) e commit dos dados |

Actions em Node 24 (D36). Python 3.9 no Actions e no Mac; não atualizar `setup-python` para v7 sem migrar o Python.
O site só muda quando a rotina mensal roda; as manchetes do globo ficam frescas sem republicar, porque a página lê os dados do repositório.

Se o deploy no Pages travar em "updating_pages" até o tempo limite (aconteceu três vezes em 06/11/2026, com o site e o pacote corretos),
repetir o job não resolve: o Pages identifica a publicação pelo commit, e a do commit cancelado não volta. Publique a partir de um
commit novo na `main` e confira a página ao vivo, porque a tela de configurações pode dizer "deployed" sem o conteúdo novo.

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
.venv/bin/python -m pytest -q                    # 147 passam, 1 pulado
```

Só o globo: `python3 -m http.server 8000 --directory prototipos/globo` e abrir http://localhost:8000 (precisa de internet para as bibliotecas e de WebGL;
sem WebGL, a lista de países assume).

## 11. Testes e guardas

- 147 testes (`tests/`), com fixtures sintéticas **no formato real** das fontes e valores inventados, marcados como tal.
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
| D38–D52 | o globo: fontes, publicação, relações, conflitos, manchetes (pausadas), retrato histórico, atlas comercial, refinamento da leitura, identidade editorial, acabamento, versão estável e logo |
