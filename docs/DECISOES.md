# Registro de decisões

Formato: data · decisão · motivo · quando revisar.

### D1 · 02/11/2026 · Python monolítico (FastAPI + HTML/JS), sem Next.js por enquanto
**Motivo:** um único ecossistema para quem não é desenvolvedor e tem 2–3 h/semana; o Node nem está instalado; nenhum passo de build.
**Revisar quando:** houver login, páginas públicas que precisem de SEO ou mais alguém desenvolvendo.

### D2 · 02/11/2026 · SQLite + arquivos brutos imutáveis
**Motivo:** zero instalação, um arquivo só e volume pequeno (dezenas de milhares de linhas).
**Revisar quando:** análises ficarem lentas (→ DuckDB) ou houver vários usuários (→ PostgreSQL).

### D3 · 02/11/2026 · Cada coleta que muda os dados vira uma versão (vintage)
**Motivo:** rastrear revisões (PIB, PNAD) e permitir, no MacroForecast, backtests com o dado disponível em cada data.
**Custo:** a série inteira é duplicada a cada versão; aceitável no volume atual.

### D4 · 02/11/2026 · Base do produto em fontes públicas primárias; Macrodados para uso pessoal
**Motivo:** a licença de uso via CORECON-SP não foi confirmada; redistribuição presumida como proibida até haver confirmação por escrito.
**Implementação:** séries importadas recebem `uso = pessoal`, ficam em `data/catalogo_local.json` (fora do catálogo público), são sinalizadas na interface e não oferecem download.

### D5 · 02/11/2026 · Sem gráfico de eixo duplo
**Motivo:** dois eixos Y induzem a leituras de correlação arbitrárias (a escala escolhida cria a "relação"). A comparação usa dois gráficos com o tempo sincronizado.

### D6 · 02/11/2026 · Brasil x Mundo rebaixado a "estudos"
**Motivo:** baixa diferenciação diante de OWID, Banco Mundial e FMI DataMapper.

### D7 · 02/11/2026 · Câmbio e Selic mensal começam em jul/1994
**Motivo:** antes do Plano Real a unidade monetária era outra; misturar os dois períodos numa série gera leituras erradas.

### D8 · 02/11/2026 · Inadimplência valida o IPFF, não o compõe
**Motivo:** se a inadimplência fosse componente, a validação seria circular.

### D9 · 02/11/2026 · Modelos de previsão com especificação fixa, definida antes do backtest
**Motivo:** escolher a ordem do SARIMA olhando o erro do backtest seria sobreajuste disfarçado. Mudanças de especificação entram como modelo novo, com nome novo, e não substituem o antigo no registro.

### D10 · 02/11/2026 · Registro de previsões imutável no próprio banco (gatilhos SQLite)
**Motivo:** a credibilidade do placar depende de ser impossível corrigir uma previsão depois. Para a mesma (modelo, origem, alvo), vale a primeira.

### D11 · 02/11/2026 · Focus comparado com a última pesquisa até o dia 15 do mês seguinte à origem
**Motivo:** nessa data o IPCA da origem já foi divulgado, então os dois lados conhecem y(o). O Focus ainda tem vantagem (IPCA-15 e outros dados), o que o torna um benchmark exigente.

### D12 · 02/11/2026 · Identidade visual editorial-financeira
Source Serif 4 nos títulos, IBM Plex Sans/Mono nos dados, filetes em vez de cartões, cor reservada para as séries e textos de status em versalete no lugar de pílulas e emojis. Categóricas fixas por modelo: SARIMA azul, Focus laranja, sazonal ingênuo verde-água, ingênuo amarelo; observado em tinta.

### D13 · 02/11/2026 · Macrodados: importação manual, sempre "uso pessoal", sem automação da área logada
**Motivo:** os Termos de uso da Macrodados proíbem cópia, redistribuição e republicação "sob qualquer forma". A autorização do Lucas cobre o lado dele, não o contrato com a Macrodados. Não há API; um robô percorrendo a área logada seria a cópia em massa que os termos vedam.
**Consequência:** a Macrodados alimenta análises pessoais e o Radar Setorial privado. Qualquer produto público usa fontes abertas ou exige autorização escrita da Macrodados.

### D14 · 02/11/2026 · Indicadores antecedentes avaliados fora da amostra, em tempo pseudo-real, com correção para múltiplos testes
**Motivo:** correlações entre séries persistentes enganam, e testar 10 indicadores × 3 horizontes gera falsos positivos. O critério é melhorar a previsão em relação ao histórico do próprio setor (Clark-West + Holm), usando só o que estaria publicado em cada data. Candidatos, transformações e defasagens de divulgação ficam declarados no código antes de rodar; novas hipóteses entram como novos candidatos, sem apagar os anteriores.

### D15 · 02/11/2026 · Hipóteses em rodadas; "ganho" exige significância e redução robusta do erro
**Motivo:** hipóteses formuladas depois de ver resultados (rodada 2) são condicionadas aos dados, então ficam numa família de Holm própria e marcadas na interface. O teste de Clark-West pode rejeitar mesmo quando o erro não cai, porque detecta conteúdo preditivo populacional, não o ganho em amostra finita. Por isso a melhora exige três coisas: teste significativo, RMSE menor no total e RMSE menor sem a pandemia.

### D16 · 02/11/2026 · Achado setorial só vale se replicar em outra série
**Motivo:** um resultado pode ser específico da série escolhida. A análise ficou parametrizada por série-alvo (`SETORES` em `leading.py`), e as mesmas hipóteses são aplicadas sem ajuste a séries novas (replicação). O resultado se reporta como "repete em k de n séries", não como regra geral.

### D17 · 02/11/2026 · Força do sinal graduada pelo número de medidas robustas e conferida em fontes independentes
**Motivo:** "repete em k de n séries" mistura sinais fortes e fracos. A interface agora classifica o sinal como forte (4 ou mais das 6 medidas de juros), fraco (1 a 3) ou ausente. Quando duas fontes discordam, uma terceira fonte pública (IBGE/PIM-PF) entra para desempatar antes de qualquer conclusão.

### D18 · 03/11/2026 · Previsão setorial com a medida de juros da rodada 1 e faixas empíricas
**Motivo:** usar a melhor medida da rodada 2 seria escolher o modelo pelo resultado. A faixa vem dos erros fora da amostra já realizados em cada origem, e não de uma fórmula do modelo, porque as faixas paramétricas do SARIMA se mostraram estreitas demais (68% para uma meta de 80%). A calibração das faixas é medida e mostrada na interface.

### D19 · 03/11/2026 · Metadado só é "conferido" com fonte oficial citada e evidência arquivada
**Motivo:** um rótulo escrito de memória pode estar errado. Isso aconteceu: o "(2002=100)" do IBC-Br e o "atraso acima de 90 dias" da inadimplência não constam dos rótulos oficiais. Uma série só sai de "a conferir" com `nome_oficial` e `fonte_metadados` no catálogo e a resposta da fonte guardada em `data/raw/bcb_metadados/`. Um teste garante isso para o BCB.

### D20 · 03/11/2026 · Versão pública: build estático só com dados abertos, com análises refeitas e verificação anti-vazamento
**Motivo:** a Macrodados ainda não respondeu sobre dados derivados e uso comercial (D13), então nada que dependa dela pode ser publicado, nem números calculados a partir dela. Por isso o build:
- usa só séries com uso "publico";
- refaz as análises com candidatos públicos (até a correção para múltiplos testes muda com a família);
- termina com uma varredura que procura ids, códigos, nomes e sequências de valores (inclusive derivados) das séries pessoais.

Site estático em vez de servidor: hospedagem gratuita e sem manutenção. A interface é a mesma, num modo que lê arquivos JSON.

### D21 · 03/11/2026 · Faixa do SARIMA empírica (erros dos últimos 60 meses, por horizonte), versionada por linha
**Motivo:** a faixa da fórmula supõe erro de tamanho constante e cobriu 64–73% para uma meta de 80%. A versão empírica com todos os erros desde 2008 também falhou (63–71%), porque o erro mudou de patamar. A janela foi escolhida entre três variantes declaradas antes, olhando só 2016–2020. Em 2021–2026, fora da escolha, cobriu 75–83%.
**Por que não um modelo novo (D9):** a previsão pontual não muda, só a faixa. Por isso o método da faixa fica registrado em cada linha (`metodo_faixa`). As linhas antigas, sem a coluna, leem "parametrica", que é o que elas são, e nenhuma previsão registrada foi alterada.
**Limite conhecido:** quando a incerteza sobe de repente, como em 2016–2020, nenhuma janela de erros passados acompanha. A cobertura ao vivo é acompanhada no placar, separada por método.

### D22 · 03/11/2026 · Registro setorial: especificação com identificador e hash, público por padrão
**Motivo:** "fixada antes" precisa ser verificável. A especificação é um objeto (`setorial.SPEC`) com identificador (`setorial_v1`), e um teste falha se ela mudar sem um identificador novo. O registro automático só cobre séries abertas (IBGE 3.27), para poder ser publicado e entrar na automação. CNI e ABIMAQ continuam possíveis localmente (`--pessoal`), mas não saem do computador do Lucas (D13).

### D23 · 03/11/2026 · Rotina mensal no GitHub Actions, com repositório público e registro em CSV só de acréscimos
**Escolha do Lucas:** GitHub Actions num repositório público, para que o histórico seja prova pública.
**Como:**
- O Actions monta um banco novo a cada execução: importa `registro/*.csv`, baixa só dados abertos, registra as previsões do mês, acrescenta as linhas novas aos CSV e roda `registro-verificar --contra HEAD`, que falha se qualquer linha antiga mudar. Em seguida faz o commit de `registro/` e publica o site no GitHub Pages.
- A identidade de cada previsão é a chave natural (modelo, série, origem, alvo), e cada linha guarda o SHA-256 dos dados usados (`coletas.csv` lista cada versão).
- As versões das bibliotecas ficam fixas, e o Python é o mesmo do Mac (3.9).

**O que fica fora do repositório (`.gitignore`):** `privado/` (configuração dos setores CNI/ABIMAQ, manifesto e scripts da Macrodados), `docs/DIARIO.md` (tem resultados calculados com dados da Macrodados), `data/` e `site/`. Dois testes falham se algum arquivo versionado estiver nessas pastas ou contiver um código do catálogo da Macrodados.

**Consequências para o uso local:**
- O registro público oficial é o do repositório.
- No Mac, `prever-setor --pessoal` registra só CNI/ABIMAQ.
- Para ver as previsões oficiais no Mac, rodar `git pull` e `econatlas registro-importar`.
- O `prever` local continua possível, mas um registro feito antes do Actions aparece como divergência em `registro-verificar`.
