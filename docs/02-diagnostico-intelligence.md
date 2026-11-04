# rotzx — Diagnóstico e plano do MVP de inteligência comercial (Fase 0)

Data: 04/11/2026. Base: branch `claude/magical-knuth-rfhjxu`, a partir do commit `c189c04` (v0.12).
Escopo: auditoria do repositório, diagnóstico de produto e desenho do primeiro MVP (radar de projetos de transmissão).
A validação de fonte está em [`03-fonte-siget.md`](03-fonte-siget.md).

---

## A. Diagnóstico técnico

### Estrutura real (confere com o README; nenhuma divergência relevante encontrada)

| Parte | Arquivos | Linhas | Situação |
|---|---|---|---|
| Coleta | `providers/` (BCB/SGS, BCB/Expectativas, IBGE/SIDRA, arquivo, Macrodados) | ~450 | Estável. Só biblioteca padrão + pandas, com novas tentativas. |
| Armazenamento | `storage.py` | 128 | Vintages com SHA-256 do bruto e dos dados, arquivo bruto preservado. É a base certa para o histórico de projetos. |
| Catálogo | `catalog/series.json`, `catalog.py` | ~530 | Metadados conferidos com fonte citada (D19). |
| Previsão | `forecast/` (modelos, backtest, Focus, faixa empírica, registro, setorial) | ~700 | Especificações fixas e versionadas (D9, D22). |
| Análise | `analysis/leading.py` | 253 | Clark-West + Holm, fora da amostra, em pseudo-tempo real. |
| Registro público | `registro.py`, `registro/*.csv` | 184 | Só acréscimos, verificação contra o git. |
| Publicação | `public_build.py` | 217 | Site estático + varredura anti-vazamento. |
| Interface | `web/app.js`, `index.html`, `styles.css` | ~1.400 | Um arquivo JS sem build; ECharts por CDN. |
| Testes | `tests/` | ~900 | 59 + 1 pulado na linha de base, Python 3.9. |

### Qualidade geral

- **Bom:** proveniência (bruto + hash + vintage), especificações fixadas antes do backtest, testes de vazamento, decisões registradas (D1–D25), dependências fixas. É raro um projeto individual ter essa disciplina, e ela é o ativo mais reaproveitável para o produto comercial ("toda conclusão é rastreável").
- **Fraco:**
  - `web/app.js` com ~1.100 linhas num único arquivo, sem testes. As frases geradas a partir de números não tinham teste nenhum, e foi aí que estava o bug de comunicação abaixo.
  - Os provedores são todos de **séries temporais** (`date`, `value`). Projetos, empresas e evidências não cabem nesse modelo: o MVP precisa de um esquema novo, ao lado do atual, sem reescrever o que existe.
  - O Python do ambiente local é 3.9, fixado por reprodutibilidade (D23). Bibliotecas novas precisam ser compatíveis.

### Falhas encontradas e corrigidas nesta etapa

| # | Problema | Onde | Correção |
|---|---|---|---|
| 1 | **Direção do erro escondida (item 14.1).** `menos(r) = |r − 1| × 100` e o texto fixo "errou X% menos". Com razão de RMSE 1,05 a página diria "errou 5% menos". Hoje as razões publicadas são < 1, então o erro não aparecia, mas apareceria assim que o resultado piorasse. A frase seguinte ("a melhora fica em…") e a do Focus ("erra X% menos que o SARIMA") tinham o mesmo defeito. | `web/app.js`, página do setor e MacroForecast | Novo `web/texto.js` com `comparaErro`/`errou`/`erroRelativo`: razão < 1 = menos, > 1 = mais, diferença < 0,5% = "praticamente o mesmo". Quatro testes (`tests/test_texto_js.py`) cobrem os três casos e entradas inválidas (D26). |
| 2 | **Garantia exagerada do registro (14.3).** "Ninguém consegue mudar uma previsão depois", "registro imutável". O banco recusa alterações e a verificação falha se uma linha antiga mudar, mas quem controla o repositório pode reescrever o histórico do git. | `web/app.js`, README, comentário do workflow | Texto passa a falar em auditabilidade, não em impossibilidade (D27). |
| 3 | **Backtest descrito como tempo real (14.2).** "Cada uma usando só os dados que existiam naquela data", enquanto o próprio método diz que usa a versão atual (revisada) dos dados. | `web/app.js`, página do setor | "Só os dados até aquela data (na versão revisada de hoje, não na que existia na época)." |
| 4 | **Série CNAE 27 tratada como "setor elétrico" (8.3).** O título "Setor elétrico: o que os juros indicam" sugere investimento em transmissão, distribuição ou compra de concessionárias. A série do IBGE mede produção física de máquinas, aparelhos e materiais elétricos, o que inclui lâmpadas e eletrodomésticos. | `web/app.js`, README | Título "Indústria de materiais elétricos" e um parágrafo "O que a série mede" no método (D27). A rota `#/setor-eletrico` foi mantida. |

### Pontos verificados que continuam válidos

- **Vazamento de informação futura nos backtests:** a origem respeita a defasagem de divulgação assumida (último dado + 2 meses), e os modelos são reestimados em janela expansiva. Não encontrei uso de dado posterior à origem.
- **Vintages:** o banco guarda versões desde a primeira coleta (nov/2026). Não existem versões históricas anteriores, então nenhum backtest reproduz o tempo real. Isso já aparece em "Limitações" e agora também no texto principal.
- **Múltiplos testes:** correção de Holm por família, documentada.
- **Cobertura das faixas:** medida e exibida (o setor ficou em 61–69% para meta de 80%; a pendência já está no README).
- **Ainda não verificado nesta etapa:** as defasagens de divulgação contra os calendários oficiais (pendência antiga). O único teste pulado (`test_macrodados.py:59`) depende do manifesto local da Macrodados, fora do repositório, como esperado.

### Componentes reutilizáveis para o MVP

1. `storage.py`: o padrão "bruto + SHA-256 + versão + data de coleta" serve como está para `SourceRecord`.
2. `providers/_get` com novas tentativas: o padrão foi copiado no explorador CKAN.
3. `public_build.verificar`: a varredura anti-vazamento é o lugar certo para impedir que perfis de fornecedor ou anotações comerciais vão para o Pages.
4. `registro.py` e o padrão "só acréscimos + verificação contra o git": serve para o histórico de mudanças de estágio dos projetos.
5. O sistema visual editorial (tabelas densas, `lede`, `fig`, `aside`) já comporta uma lista de oportunidades sem cara de CRM.
6. A camada econômica (Selic, crédito PJ, câmbio, produção industrial) vira contexto da página de oportunidades.

---

## B. Diagnóstico de produto

**O que o site oferece hoje:** 18 séries macro, previsões de IPCA com backtest e comparação com o Focus, análise de indicadores antecedentes para a indústria de materiais elétricos, uma página em linguagem simples e um registro público de previsões.

**Para quem parece ter sido feito:** economistas e analistas que valorizam método (Clark-West, Holm, vintages). Não foi feito para um gerente comercial: nenhuma página responde "o que eu faço com isso?".

**Onde há utilidade real:**
- A página da indústria de materiais elétricos chega mais perto de um uso B2B (um fabricante quer saber se a demanda do setor esfria). Mas a diferença entre o modelo com e sem juros é de cerca de 1 ponto, com faixas de ±12 a ±20 pontos. **Para decidir prospecção, esse sinal é fraco.** Serve como contexto, não como produto.
- A rastreabilidade (fonte, data, hash, registro) é o diferencial que vale levar para o produto comercial.

**Excesso de informação / sem relação com a proposta comercial:**
- **MacroForecast (IPCA):** rigoroso, mas o mercado já tem o Focus de graça. Fica como laboratório e demonstração de método, fora do caminho principal.
- **Brasil x Mundo:** aparece no menu como "planejado" sem conteúdo. Sugestão: tirar do menu principal na reorganização (não feito agora).
- **Radar Brasil completo:** 18 séries sem hierarquia para quem vende equipamento. Na área "Inteligência de Mercado", mostrar 4 ou 5 indicadores ligados ao setor e deixar o resto como "todas as séries".

**Navegação proposta** (a implementar junto com a Fase 4, não agora):

| Área | Conteúdo | Origem |
|---|---|---|
| Oportunidades (início) | Radar de projetos de transmissão, filtros, detalhe, exportação | novo |
| Inteligência de Mercado | Indicadores do setor, indústria de materiais elétricos, crédito, juros, câmbio | Radar Brasil + Radar Setorial |
| Acompanhamento | Lista local de projetos marcados (só no modo local, nunca no Pages) | novo, opcional |
| Pesquisa e Metodologia | MacroForecast, backtests, registro, qualidade, decisões | existente |

**Crítica à premissa:** o setor de transmissão concentra compras em poucos compradores grandes (transmissoras e EPCistas), e eles compram por homologação e cotação privada, não por edital público. Um "radar" só tem valor se chegar **antes** da cotação: estágio "em implantação" com data de energização distante e módulos de equipamento descritos. Se o SIGET não trouxer equipamento por módulo nem datas previstas confiáveis, o radar vira uma lista de obras que qualquer fornecedor do nicho já conhece. Essa é a hipótese que a Fase 1 precisa testar antes de qualquer interface.

---

## C. Validação de fontes

Ver [`03-fonte-siget.md`](03-fonte-siget.md). Resumo: **o portal da ANEEL não pôde ser acessado deste ambiente** (o proxy de rede bloqueia `dadosabertos.aneel.gov.br`). Nenhum dado da ANEEL foi baixado e nenhum exemplo real é mostrado aqui. A ferramenta `fonte-explorar` está pronta para gerar o perfil dos campos assim que houver acesso.

---

## D. Projeto do MVP

### Fluxo do usuário (fornecedor de equipamento para subestação)

1. Abre **Oportunidades**: lista de empreendimentos de transmissão ordenada pelo score, com filtros por UF, estágio, categoria de equipamento e grau de evidência.
2. Abre um empreendimento: o que é (fato, com link da fonte), quem é o responsável (concessionária do contrato), estágio e datas, módulos e equipamentos **mencionados na fonte**, categorias **inferidas** (separadas e rotuladas) e a explicação do score.
3. Exporta CSV com as colunas de evidência para montar o relatório comercial.
4. (Opcional, só local) marca como "em análise" ou "descartado" e anota o próximo passo.

### Estrutura de dados (SQLite, tabelas novas; nenhuma tabela atual muda)

| Tabela | Papel | Chave |
|---|---|---|
| `fonte_registro` | Linha original de cada arquivo da fonte (JSON), com `fonte`, `recurso`, `id_na_fonte`, `coletado_em`, `sha256_arquivo` | (fonte, recurso, id_na_fonte, sha256) |
| `organizacao` | Concessionária ou empresa, com CNPJ quando a fonte trouxer | id interno + CNPJ |
| `projeto` | Empreendimento, com `id_na_fonte` oficial. Nunca é unido a outro só por nome parecido | (fonte, id_na_fonte) |
| `projeto_evento` | Mudança de estágio, data ou valor entre duas coletas (diff), só acréscimos | (projeto, campo, coletado_em) |
| `evidencia` | Trecho ou campo que sustenta uma afirmação, com nível: `confirmado`, `inferencia_tecnica`, `hipotese_mercado`, `nao_verificado` | id |
| `categoria_produto` | Vocabulário controlado (`catalog/product_categories.json`, versionado) | slug |
| `projeto_categoria` | Ligação projeto ↔ categoria, com regra aplicada, evidência e nível | (projeto, categoria, regra) |
| `perfil_fornecedor` | Perfil de demonstração no MVP (arquivo local, fora do git e do Pages) | id |
| `oportunidade_acao` | Status e anotações do usuário (só local) | (projeto, perfil, data) |

A separação entre `projeto` e `fonte_registro` existe para que duas fontes (SIGET e leilões) possam falar do mesmo empreendimento sem contagem dupla. A ligação só é feita por identificador oficial ou regra documentada, e o caso ambíguo vai para revisão manual.

### Primeiros critérios de classificação (determinísticos)

- **Confirmado:** o nome do equipamento ou do tipo de módulo aparece em campo estruturado da fonte (ex.: módulo de transformação, módulo de entrada de linha), com mapeamento explícito módulo → categoria versionado em `product_categories.json`.
- **Inferência técnica:** a natureza do empreendimento implica a categoria com regra escrita (ex.: "subestação nova de 500 kV" → seccionadoras, para-raios, transformadores de instrumento), sempre rotulada como inferência e **nunca como compra**.
- **Score 0–100** = 40% compatibilidade com o catálogo do perfil + 25% estágio acionável + 20% qualidade e atualidade da evidência + 15% geografia. Pesos em arquivo de configuração. Projetos só com inferência têm teto de pontuação (regra a calibrar), e o score fica separado do grau de evidência.
- Estes critérios são provisórios: **só serão escritos depois do perfil real dos campos do SIGET.**

### Arquivos a criar (fases 2–4)

`econatlas/providers/aneel_siget.py` (coletor real, depois do perfil), `econatlas/intelligence/{projetos,evidencia,matching,scoring}.py`, `catalog/product_categories.json`, `web/oportunidades.js`, testes correspondentes.

### Arquivos existentes que vão mudar

`storage.py` (esquema novo, sem alterar o atual), `cli.py` (comandos `projetos-atualizar`, `oportunidades-exportar`), `api.py` (rotas `/api/projetos`), `payloads.py`, `public_build.py` (decidir o que é publicável e estender `verificar` para dados privados), `web/index.html` e `web/app.js` (navegação).

### Critérios de aceitação do MVP

Os do item 17 do plano mestre, com três condições adicionais desta auditoria:
1. A licença do SIGET está registrada no catálogo e permite republicação. Senão, os projetos ficam só no modo local.
2. Cada categoria exibida mostra o nível de evidência e o campo ou regra de origem.
3. Uma amostra de 20 projetos foi avaliada à mão **antes** de escrever as regras, com critério de relevância definido por escrito.

---

## E. Plano revisado das próximas entregas

| Passo | Entregável | Depende de |
|---|---|---|
| 1 | Liberar `dadosabertos.aneel.gov.br` na rede do ambiente (ou rodar `fonte-explorar` no Mac) | Lucas |
| 2 | Perfil real do SIGET: `relatorio.md` + respostas às perguntas do `03-fonte-siget.md` | passo 1 |
| 3 | Amostra de 10–20 empreendimentos com módulos e equipamentos, avaliada à mão | passo 2 + 1 h do Lucas |
| 4 | Decisão: seguir com o SIGET, combinar com leilões, ou trocar de fonte | passo 3 |
| 5 | Coletor + esquema (Fase 2) | passo 4 |

O que **não** fazer antes do passo 4: classificador, score, interface de oportunidades, catálogo de produtos detalhado.
