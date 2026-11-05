# rotzx — documentação do projeto

Estado em 05/11/2026 (v0.13 e o globo com as decisões até D44). Este documento descreve o projeto inteiro: o que ele faz,
de onde vem cada dado, como as peças se encaixam e como operar. O porquê de cada escolha está em [`DECISOES.md`](DECISOES.md)
(D1–D44). Para continuar o projeto com um assistente de IA, use [`PROMPT.md`](PROMPT.md).

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
| `tests/` | pytest: 140 testes + 1 pulado (inclui as guardas do repositório público) |
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

## 7. Frente 3 — O mundo visto do Brasil (globo)

### O que a pessoa vê

Um quadro dividido em dois, com uma barra em cima (D41 e redesenho de 04/11):

- **Barra de cima:** marca, estado dos dados (hora das manchetes, ano do comércio, votos na ONU, OMC, conflitos; aviso se algum feed falhou), "Fontes e método", busca.
- **Esquerda — Visão mundial:** globo 3D (Blue Marble tingida, relevo, meridianos) que começa com o Brasil de frente e gira devagar;
  alternância **Globo / Lista de países** (a lista substitui o globo sem WebGL); zoom +/−; camada **Notícias** (mapa de calor:
  países pintados pelo número de manchetes da aba aberta) ou **Países com dados**.
- **Direita — Mundo agora:** abas
  - **Agora** e **No Brasil:** filtros por categoria com contagem; botões **Onde** (países citados) que filtram;
    **Assuntos mais cobertos** no topo (grupos de manchetes com palavras em comum, ordenados por número de veículos);
    o resto em **linha do tempo** por dia, com hora de Brasília (D44).
  - **Conflitos:** conflitos armados do último ano, os mais intensos primeiro (D43).
  - **Comércio do Brasil:** exportações, importações, saldo e maiores parceiros (clicáveis).
- **Painel do país** (substitui o resumo ao clicar): relação com o Brasil (resumo descritivo, KPIs, 5 produtos de cada lado),
  **Sinais da relação** (comércio, votos na ONU, disputas na OMC), visão externa na OMC, **conflitos armados** 2021–2025,
  economia (Banco Mundial) e manchetes com abas por categoria. Países fora dos 20 abrem um painel com as manchetes que os citam.
- Link direto por país: `globo/#China`. Esc ou "← Mundo" volta.

### Dados (`prototipos/globo/dados/`)

Gerados por `rotzx mundo-atualizar`; cada arquivo existe em `.json` e em `.js` (`window.MUNDO` / `window.NOTICIAS`), para a página funcionar também aberta como arquivo local.
Ao abrir, o globo busca a versão mais nova em `raw.githubusercontent.com/lcgalera/rotzx/main/prototipos/globo/dados/` e fica com a cópia se falhar.

`mundo.json`:
- `gerado_em`, `ano_comercio`, `fontes` (nome, url, licença, nota de cada fonte), `falhas`
- `paises[iso_num]`: `nome`, `artigo`, `iso3`, `resumo`, `comercio` (exportacao/importacao com fob, participacao, posicao; saldo; produtos_exportados/importados SH4),
  `economia` (indicadores do Banco Mundial), `relacoes.onu` (concordancia, media, anos_media, posicao, de), `relacoes.omc` (com_brasil, recentes, contrapartes, via_ue, total),
  `relacoes.conflitos` (lista com local, lados, papel, anos_pais, tipo, disputa, intensidade, url)
- `paises["076"]` (Brasil): também `comercio_total` e `maiores_parceiros` (15)
- `onu` (ano, mediana, versão), `conflitos` (ultimo_ano, desde, versao, mundo.ativos/total/guerras), `relacoes_em`

`noticias.json`:
- `gerado_em`, `fonte`, `dias`, `falhas`, `diagnostico`, `nomes` (iso_num → nome em português, para os 55 países marcáveis)
- `paises[iso_num]`: até 60 manchetes dos últimos 7 dias que citam o país no título
- `mundo`: até 100 manchetes de geopolítica e temas globais dos últimos 2 dias
- cada manchete: `titulo`, `url`, `veiculo`, `data` (AAAAMMDD), `hora` (HH:MM, Brasília, vazia sem fuso), `dominio`, `categorias`, `paises` (citados)

### Regras de texto e marcação

- Manchete só entra num país se o título o cita, **com acento e palavra inteira** ("França" ≠ Franca, SP). Termos ambíguos ficam de fora
  ("peru", "sírio", "libanês", "maduro", "português"). Lista em `rotzx/mundo/paises.py` (`PAISES` e `MENCOES`).
- Categorias (economia, política, geopolítica, afeta o mundo) por expressões regulares ancoradas em início de palavra (`rotzx/mundo/gdelt.py`).
- O resumo do país só descreve números do Comex Stat; nomes de produtos SH4 ficam na tabela, completos.
- Assuntos: duas ou mais palavras do título em comum (fora as vazias e os países); critério de destaque = número de veículos.

### Coleta

| Quando | O quê | Onde |
|---|---|---|
| todo dia, 6h41 de Brasília | manchetes (RSS + GDELT) | `globo.yml` → commit em `prototipos/globo/dados/` na `main` |
| todo dia 15 | comércio (~10 min, limite do Comex Stat), economia, ONU, OMC, conflitos | `globo.yml` |
| push em `claude/**` que mexa em `rotzx/mundo/` | testes + manchetes, para testar o coletor | `globo.yml` |

## 8. Automação (GitHub Actions)

| Workflow | Quando | O que faz |
|---|---|---|
| `rotina-mensal.yml` | dias 12 e 20, ou à mão | testes, registro, dados abertos, previsões, backtest, calibração, verificação do registro, build do site, commit e deploy no Pages |
| `radar-siget.yml` | toda segunda, ou à mão | histórico do SIGET, eventos, contexto, relatório (artefato 90 dias), commit de `historico/` |
| `globo.yml` | diário e dia 15 (ver acima) | coleta do globo e commit dos dados |

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
| `mundo-atualizar [--ano A] [--sem-noticias] [--so-noticias] [--so-relacoes]` | dados do globo |
| `servir` | interface local em http://127.0.0.1:8000 (o globo fica em `/globo`) |

## 10. Como rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m rotzx atualizar
.venv/bin/python -m rotzx servir                 # http://127.0.0.1:8000
.venv/bin/python -m pytest -q                    # 140 passam, 1 pulado
```

Só o globo: `python3 -m http.server 8000 --directory prototipos/globo` e abrir http://localhost:8000 (precisa de internet para as bibliotecas e de WebGL;
sem WebGL, a lista de países assume).

## 11. Testes e guardas

- 140 testes (`tests/`), com fixtures sintéticas **no formato real** das fontes e valores inventados, marcados como tal.
- Guardas do repositório público: falham se um arquivo versionado estiver em pastas privadas ou citar um código do catálogo da Macrodados.
- Varredura do build: falha se o site tiver id, código, nome ou sequência de valores (inclusive derivados) de série pessoal.
- Globo: testes de marcação de países (inclusive falsos positivos), categorias, hora de Brasília, ONU, OMC, UCDP, isolamento de falhas entre fontes.
- A interface do globo foi verificada em Chromium sem tela (WebGL por software), em 1440×900 e 390×844.

## 12. Limitações conhecidas

- Globo: 20 países com dados completos (mais o Brasil); 34 outros só com manchetes. A lista final deve sair do ranking de comércio.
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
| D38–D44 | o mundo visto do Brasil (globo, fontes, publicação, relações, conflitos, manchetes) |
