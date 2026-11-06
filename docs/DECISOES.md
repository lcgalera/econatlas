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
- Para ver as previsões oficiais no Mac, rodar `git pull` e `rotzx registro-importar`.
- O `prever` local continua possível, mas um registro feito antes do Actions aparece como divergência em `registro-verificar`.

### D24 · 03/11/2026 · Página do setor elétrico em linguagem simples, com todo número calculado dos dados
**Motivo:** a página pública é a porta de entrada e muda todo mês. Frases fixas envelheceriam ou contradiriam os dados. Por isso a conclusão, as margens, os ciclos de alta da Selic (do primeiro aumento ao último antes de um corte), o resultado do teste e a lista do que "não ajudou" são todos calculados na hora, a partir das séries abertas, da análise pública e do registro.
- **Linguagem:** sem jargão no corpo do texto. Os termos técnicos (RMSE, Clark-West, Holm) ficam numa seção recolhível "Para quem quer o método".
- **Ressalvas na própria página:** associação preditiva não é causalidade, não é recomendação financeira, e a margem de 80% vem acompanhada da cobertura real quando ela fica abaixo de 75%.
- **Gráficos:** dois gráficos com o tempo sincronizado, em vez de eixo duplo (D5).

### D25 · 04/11/2026 · Nome do produto passa a ser rotzx (sempre em minúsculas)
**Escolha do Lucas:** a marca EconAtlas é substituída por **rotzx** em toda a interface, títulos, textos, documentação e metadados (título da página, marca no cabeçalho, rodapé, título da API FastAPI, User-Agent das coletas, docstrings e cabeçalhos de arquivos).
**O que não muda nesta etapa (de propósito, para não quebrar nada):** o nome do repositório (`lcgalera/econatlas`) e o endereço do site público (`lcgalera.github.io/econatlas`), o pacote Python `econatlas/`, os comandos `python -m econatlas …`, a variável `window.ECONATLAS_STATIC`, a chave `econatlas-theme` do `localStorage` (mudar faria quem já usa o site perder o tema escolhido), o marcador `.econatlas-publico` do build e os arquivos `econatlas.sqlite`/`econatlas_publico.sqlite`. São identificadores internos ou endereços, não marca.
**Onde o identificador antigo ainda aparece na tela:** só nas instruções de linha de comando dos estados vazios (por exemplo, "rode `python -m econatlas prever`"), porque esse é o comando real. O link do rodapé da página do setor elétrico passou a dizer "repositório público no GitHub" em vez de exibir o endereço.
**A avaliar separadamente:** renomear repositório, URL do site, pacote e comandos (exige redirecionamento do GitHub Pages, ajuste do workflow, dos imports dos testes e da documentação de uso no Mac).

### D26 · 04/11/2026 · Frases de comparação de erro dizem sempre a direção
**Motivo:** a página da indústria de materiais elétricos calculava `|razão − 1|` e escrevia sempre "errou X% menos". Uma razão de RMSE de 1,05 viraria "errou 5% menos".
**Regra:** razão = RMSE do modelo ÷ RMSE da referência. Razão < 1 = "errou menos"; razão > 1 = "errou mais"; |razão − 1| < 0,5% = "praticamente o mesmo erro". O limiar de 0,5% é o arredondamento abaixo do qual a frase com 0 casas mostraria 0%.
**Como:** as frases ficam em `web/texto.js`, sem DOM, testadas no Node (`tests/test_texto_js.py`; o teste é pulado onde não há Node, como no Mac, e roda no GitHub Actions). A frase de conclusão também muda: se o erro não diminuiu em algum horizonte, a página diz isso em vez de falar em "melhora".

### D27 · 04/11/2026 · Comunicação sem exagero: registro, backtest e nome da série
- **Registro:** "imutável" e "ninguém consegue mudar" saem da interface. O banco recusa alterações, o verificador falha se uma linha antiga mudar e o git mostra quando cada linha entrou: isso é **auditabilidade**. Quem controla o repositório ainda poderia reescrever o histórico. Os gatilhos do SQLite e as docstrings continuam a usar "imutável" no sentido técnico (o banco recusa UPDATE/DELETE).
- **Backtest:** o texto principal deixa de dizer "só os dados que existiam naquela data". Diz "só os dados até aquela data, na versão revisada de hoje", que é o que o método faz (D3: não há vintages anteriores a nov/2026).
- **Nome da série:** a série do IBGE (PIM-PF, seção 3.27 = CNAE 27) passa a ser chamada de "indústria de (máquinas e) materiais elétricos", não "setor elétrico". Ela inclui de transformadores e cabos a lâmpadas e eletrodomésticos, e não mede investimento em transmissão ou distribuição nem compras de concessionárias. A rota `#/setor-eletrico` e os identificadores internos (`eletrico_pim`, `pim_eletricos`) não mudam.

### D28 · 04/11/2026 · Radar de oportunidades começa pela exploração da fonte, não pelo classificador
**Motivo:** o plano do rotzx Intelligence (radar de projetos de transmissão para fornecedores) depende de o SIGET trazer chave estável, estágio, datas e equipamentos por módulo. Nada disso foi verificado.
**Como:** `rotzx fonte-explorar` usa a API padrão do CKAN do portal da ANEEL, baixa os recursos tabulares com SHA-256 para `data/fontes/` (fora do git) e gera um relatório de campos para avaliação humana. Não é coletor de produção e não interpreta nada.
**Critério de decisão** fixado antes de ver os dados em `docs/03-fonte-siget.md` §4. Classificador, score e interface só depois dessa decisão.
**Licença:** nenhum dado da ANEEL entra no build público até a licença do conjunto estar registrada.

### D29 · 04/11/2026 · Relatório antes da interface; conversas com compradores antes do pipeline
**Motivo:** a pesquisa de mercado (`docs/04-mercado-e-posicionamento.md`) mostra que a lista de projetos de transmissão é pública, pequena e coberta pela imprensa e por bases de obras. O valor possível está na leitura técnica (módulo → equipamento), nas mudanças e no cruzamento com o catálogo, e nada disso foi validado com comprador.
**Decisão:** (1) começar as conversas de descoberta já (roteiro em `docs/05-validacao-com-compradores.md`, registros em `privado/`); (2) a primeira entrega comercial é um relatório gerado pelo pipeline e revisado à mão; (3) a interface de oportunidades só começa depois de piloto; (4) a distribuição entra nas conversas como nicho concorrente.
**Navegação:** o Radar Setorial passa a ser o primeiro item do menu e aparece como ativo; Brasil x Mundo sai do menu e da home (D6), mas a rota continua existindo.
**Revisar quando:** houver resultado das 5 conversas ou do perfil do SIGET.

### D30 · 04/11/2026 · SIGET validado: seguir com a fonte; autorizações (REA/DSP) como foco inicial
**Resultado** (`docs/03-fonte-siget.md`): chaves estáveis com 100% de ligação entre as tabelas, situação preenchida, 754 empreendimentos em andamento (652 com módulo de equipamento), concessionária com CNPJ, datas do ato legal e UF. Licença ODbL, atualização diária. Os três critérios fixados antes de ver os dados foram atendidos.
**Descoberta:** 616 dos 754 empreendimentos em andamento são autorizações (reforços e melhorias por resolução ou despacho em concessões existentes), com link do ato. Elas quase não saem na imprensa e descrevem a troca ou instalação de equipamento de forma concreta. É o melhor candidato a diferencial do radar, e vale testar nas conversas com compradores.
**Limites que o produto precisa mostrar:** as datas são as do ato legal, não a previsão da transmissora; potência e quantidade de disjuntores têm preenchimento parcial; `DscSituacaoModulo` está com defeito na fonte; campos fora do dicionário não são usados; lotes de leilão ainda não assinados não aparecem.
**Como:** `rotzx siget-amostra` (`providers/aneel_siget.py`) monta a visão por empreendimento só com o que a fonte afirma e uma amostra reproduzível de 20 casos, que a avaliação humana classifica com o critério de `docs/03` §5.
**Licença:** a ODbL permite republicar com atribuição ("Contém dados da ANEEL…") e exige a mesma licença na base derivada. A amostra no `docs/03` já leva a atribuição.

### D31 · 04/11/2026 · Avaliação aleatória: 80% de precisão (IC 58–92%) — regras da Fase 3 definidas, meta não demonstrada
**Resultado:** 16 de 20 relevantes numa amostra aleatória (semente 20261104) dos 612 elegíveis; 3 das 4 falhas vieram da janela de 6 meses e 1 de "revitalização" sem equipamento novo. Com n = 20, o intervalo de 95% vai de 58% a 92%: a meta de 80% não está demonstrada.
**Decisões:** (1) a janela passa a fazer parte da elegibilidade, com prazo por categoria a validar com compradores; (2) o classificador lê a descrição (verbos de troca e instalação) e não só o tipo de obra; (3) os 40 casos avaliados ficam em `avaliacoes/siget_relevancia.csv` como conjunto de teste, e as regras novas são medidas numa amostra nova.
**Revisar quando:** houver 60 casos avaliados ou a primeira avaliação feita por comprador.

### D32 · 04/11/2026 · Motor de oportunidades determinístico: evidência por regra, score separado do nível de evidência
**Como:** `rotzx/intelligence/` gera evidências por empreendimento e categoria (regras R1–R5: campo de módulo novo, texto com verbo de fornecimento, quantidades de manobra, inferência de bay e de linha), filtra pela elegibilidade (em andamento, concessionária, janela, tensão) e calcula o score 40/25/20/15 com os componentes e a explicação em cada linha. Só inferência tem teto de 60; pendência na descrição limita o estágio. Detalhes em `docs/06-motor-de-oportunidades.md`.
**Catálogo e perfis:** `catalog/product_categories.json` é versionado (`categorias_v1`). O perfil de demonstração fica em `catalog/perfil_demo.json`; perfis de clientes reais ficam em `privado/perfis/`, fora do git e do site.
**Normalização:** o CNPJ da fonte perde os zeros à esquerda; ele é completado até 14 dígitos e formatado. Essa é a única transformação de valor da fonte.
**Limite reconhecido:** com perfil amplo, o score satura (mediana 92). Ele separa o confirmado do inferido e o que está perto da janela, não os bons casos entre si.
**Verificação:** concordância de 39/40 com as avaliações humanas, que porém inspiraram as regras. A precisão fora da amostra ainda precisa de uma amostra nova.
**Sem IA:** nada aqui depende de modelo de linguagem.

### D33 · 04/11/2026 · Histórico do SIGET em CSV no git, com coleta semanal pelo GitHub Actions
**Motivo:** o valor recorrente do radar é dizer o que mudou (empreendimento novo, data adiada, obra nova). Isso exige histórico, e o histórico precisa sobreviver a containers temporários e a máquinas diferentes.
**Como:** `intelligence/historico.py` grava uma versão por empreendimento a cada coleta que trouxe arquivos diferentes e os eventos de mudança (só acréscimos, com gatilhos). `historico/*.csv` guarda coletas e eventos (só acréscimos, com verificação na exportação) e o estado da última coleta. O workflow `radar-siget.yml` roda toda segunda-feira: importa, coleta, exporta, gera o relatório como artefato e faz o commit de `historico/`.
**Coleta seletiva:** só os 7 arquivos usados, e só quando a data de modificação declarada pelo portal mudou.
**Licença:** dados da ANEEL sob ODbL, com atribuição em `historico/LEIAME.md`; a base derivada fica sob a mesma licença.
**Limite:** em 04/11/2026 só existe a linha de base; a detecção de mudanças ainda não foi exercitada com dados reais.
**Revisar quando:** o tamanho de `historico/` passar de alguns MB (o estado tem ~0,7 MB) ou houver clientes com perfis próprios, que precisarão de relatórios privados, fora do Actions público.

### D34 · 04/11/2026 · Contexto econômico no relatório, fora do score
**Como:** `intelligence/contexto.py` + `catalog/contexto_radar.json`. O relatório ganha a seção "Contexto de mercado", com o pipeline do próprio SIGET (contagens por ano), nove indicadores públicos do BCB e do IBGE (cada um com canal possível e limite, escritos antes de ver os valores) e a última previsão setorial registrada, com o aviso sobre a margem. O comando `contexto-atualizar` baixa só as séries usadas e entrou no workflow semanal.
**Por que fora do score:** a relação entre esses indicadores e uma compra específica não foi medida. Ordenar oportunidades por eles seria associação frágil.
**Elo concreto encontrado:** a receita de 370 dos 411 contratos de transmissão é reajustada pelo IPCA (e a de 41 pelo IGP-M), segundo o SIGET.
**Achado da fonte:** nenhum contrato assinado em 2025. O relatório mostra o zero em vez de esconder o ano.

### D35 · 04/11/2026 · Repositório, site, pacote e comandos passam a se chamar rotzx (revisa D25)
**Escolha do Lucas:** o repositório foi renomeado para `lcgalera/rotzx`; com isso, o site passa a ser `lcgalera.github.io/rotzx` e o pacote, os comandos, os links e os identificadores internos também mudam (`rotzx/`, `python -m rotzx`, `ROTZX_STATIC`, `rotzx_publico.sqlite`, `.rotzx-publico`, `rotzx-theme`).
**Compatibilidade:** `econatlas/` virou um pacote de redirecionamento (`python -m econatlas …` e `import econatlas…` funcionam, com aviso); o banco `data/econatlas.sqlite` é renomeado no primeiro uso; o tema salvo com a chave antiga continua sendo lido; uma pasta `site/` gerada com o marcador antigo pode ser regerada.
**O que não muda:** o registro de previsões, o histórico do SIGET e a versão do código registrada em cada previsão (`versao_codigo`). Nenhuma linha de `registro/` nem de `historico/` foi tocada. O texto de D25 fica como estava, como registro da decisão da época.
**Efeito externo:** o endereço antigo do site (`lcgalera.github.io/econatlas`) deixa de funcionar; o GitHub não redireciona sites do Pages. O repositório antigo redireciona.

### D36 · 04/11/2026 · Actions em Node 24, na menor versão de cada uma que já roda nele
**Motivo:** o GitHub avisou que o Node 20 foi descontinuado nas actions (`checkout@v4`, `setup-python@v5`, `upload-artifact@v4`).
**Versões** (conferidas no `action.yml` de cada tag): `checkout@v5`, `setup-python@v6`, `upload-artifact@v6`, `upload-pages-artifact@v5` (usa `upload-artifact@v7` por dentro) e `deploy-pages@v5`, todas em Node 24.
**Por que não a mais nova:** o `setup-python@v7` remove versões do Python fora de suporte, e o projeto usa a 3.9 (igual ao Mac, D23). A migração do Python é outra decisão.
**Efeito conhecido:** desde a v4, o `upload-pages-artifact` deixa de fora arquivos que começam com ponto (`.nojekyll`, `.rotzx-publico`). Nenhum deles faz falta no site publicado pelo Actions, que não passa pelo Jekyll.

### D37 · 04/11/2026 · Leilões de transmissão como sinal antecipado, com ligação lote → contrato conferida à mão
**Fonte:** a planilha oficial da Central de Conteúdos da ANEEL vai até o Leilão 04/2026 (30/10/2026); o conjunto do portal parou em 09/2024. O download automático da planilha é barrado por desafio anti-robô e não é contornado: a planilha é baixada à mão e importada com `rotzx leiloes-importar`. A tabela por lote fica em `historico/leiloes_transmissao.csv` (versionada, com atribuição).
**Ligação:** sem número de contrato nem código do ONS na planilha, cada lote recente foi ligado ao contrato do SIGET por nome, UF, vencedor e data, com evidência e status (`conferido`, `provavel`, `ambiguo`) em `catalog/leiloes_contratos.json`. Lotes nunca são unidos só por nome parecido.
**No relatório:** lotes arrematados nos últimos 24 meses sem contrato identificado, com categorias pela regra R6 (instalação nova confirma; continuidade fica como não verificado) e operação estimada (leilão + prazo). Os prazos até a assinatura (68 a 115 dias nos 19 lotes ligados) são medidos a partir do mapa.
**Achados:** o "nenhum contrato em 2025" do SIGET é efeito do calendário (leilão em 10/2025, contratos em 02/2026); duas fontes oficiais da ANEEL divergem na receita de dois lotes do Leilão 01/2023.

### D38 · 04/11/2026 · Nova direção em teste: "o mundo visto do Brasil", com globo interativo
**Escolha do Lucas:** um site para pessoas comuns em que cada país, clicado num globo, mostra a relação com o Brasil, a economia e as manchetes (economia, política, geopolítica e o que afeta o mundo). Monetização fica para depois.
**Por que esse recorte:** notícia internacional por país já existe em vários produtos. O diferencial possível é ligar a notícia ao efeito no Brasil com dado oficial (comércio, câmbio, juros), que é o que este projeto já sabe fazer. Começa com 20 países, não 195.
**Regras herdadas:** manchete só com título, veículo e link (sem copiar matérias); cada número com fonte; o que for interpretação aparece marcado.
**Estado:** protótipo de navegação em `prototipos/globo/`, sem dados reais. O radar do SIGET e os robôs continuam rodando como estão.

### D39 · 04/11/2026 · Globo com dados reais: Comex Stat, Banco Mundial e GDELT; FMI fora; manchetes coletadas no GitHub Actions
**Fontes:** comércio do Brasil com cada país (Comex Stat, último ano completo, 5 principais produtos SH4 de cada lado), indicadores do Banco Mundial (CC BY 4.0) e manchetes em português do GDELT (só título, veículo, data e link). O FMI barra acesso automatizado e ficou de fora.
**Regras:** o resumo de cada país só descreve números do Comex Stat; os produtos ficam numa tabela com o nome oficial completo (abreviar o SH4 enganava); manchete só entra se citar o país no título, comparando com acento (sem acento, "França" casaria com Franca, SP); categorias por palavras-chave, avisadas como automáticas.
**Operação:** o Comex Stat limita o ritmo (uma consulta a cada ~12 s; só o formato antigo de consulta por GET passou) e o GDELT bloqueou o IP compartilhado do ambiente de desenvolvimento. Por isso a coleta roda no workflow `globo.yml`: manchetes todo dia, comércio e economia todo dia 15.

### D40 · 04/11/2026 · Manchetes do globo: feeds RSS como fonte principal, GDELT como complemento
**Motivo:** o GDELT limitou o ambiente de desenvolvimento e também o GitHub Actions (429 e respostas em texto), e uma consulta em lote voltou vazia sem explicação. Uma fonte que falha assim não sustenta o produto.
**Como:** `rotzx/mundo/rss.py` lê feeds de mundo e economia de veículos em português (g1, Folha, BBC News Brasil, DW, Agência Brasil, CNN Brasil, RFI); cada manchete vai para os países que o título cita. O GDELT continua em lotes, quando responde. Cada coleta acumula com a anterior (7 dias por país; 2 dias em "Em alta no mundo", que reúne geopolítica e temas globais). Toda falha fica em `falhas` e quantos itens cada fonte trouxe fica em `diagnostico`.
**Regra mantida:** só título, veículo, data e link; o texto da matéria fica no site do veículo.

### D41 · 04/11/2026 · Globo publicado no site, com dados frescos lidos do repositório
**Como:** o build público copia `prototipos/globo/` para `site/globo/`, e o menu do site ganha o link "O mundo visto do Brasil". O globo vem com uma cópia dos dados do dia da publicação e, ao abrir, busca a versão mais nova em `raw.githubusercontent.com/lcgalera/rotzx/main/prototipos/globo/dados/`, que o workflow Globo atualiza todo dia. Se essa busca falhar, fica a cópia. Assim as manchetes ficam frescas sem republicar o site todo dia (a rotina mensal, que publica, roda nos dias 12 e 20).
**Segurança:** a varredura anti-vazamento do build passa a ler também arquivos `.js`; os dados do globo são só de fontes abertas.
**Operação:** a rotina mensal passa a fazer `git pull --rebase` antes do push, porque o workflow Globo também grava na `main`.

### D42 · 04/11/2026 · Relação de cada país com o Brasil por sinais medidos, não por veredito
**Pedido:** mostrar se a relação de cada país com o Brasil é positiva ou negativa, e também os conflitos de cada país com o resto do mundo.
**Decisão:** não há nota de "boa" ou "ruim", porque isso seria opinião apresentada como dado. O painel mostra três sinais, cada um com a fonte:
comércio (superávit ou déficit, Comex Stat), votos na ONU e disputas na OMC.
- **ONU** (`rotzx/mundo/onu.py`): índice de concordância de Lijphart nas votações nominais da Assembleia Geral (Voeten, Strezhnev e Bailey,
  Harvard Dataverse, CC0). Mostra o valor do último ano, a média de 5 anos (o índice muda com a pauta do ano, como avisam os autores) e a posição
  entre todos os países. O sinal diz em que terço da tabela o país está.
- **OMC** (`rotzx/mundo/omc.py`): a lista oficial de disputas do site da OMC, lida como texto, sem executar o JavaScript. Para países da UE, as
  disputas são da UE, e o painel avisa. O sinal conta as disputas com o Brasil abertas nos últimos 5 anos, e não as "em aberto", porque casos
  antigos muitas vezes ficam sem encerramento formal. A "visão externa" lista as disputas do país com outros países no mesmo período.
**Ficou de fora, por enquanto:**
- Blocos e alianças pelo Wikidata: a consulta trouxe o México como membro do Mercosul e deixou de fora a Holanda, na OTAN e na UE.
- Conflitos armados (UCDP, Uppsala): a API agora exige chave de acesso e o site de downloads continuou bloqueado na rede do ambiente.
**Operação:** `rotzx mundo-atualizar --so-relacoes`; a coleta mensal do workflow Globo já inclui as duas fontes. Se uma falhar, a falha fica em `falhas` e a outra segue.

### D43 · 04/11/2026 · Conflitos armados pela base de Uppsala (UCDP/PRIO)
**Fonte:** UCDP/PRIO Armed Conflict Dataset (Uppsala Conflict Data Program, CC BY 4.0), versão mais recente da página de downloads
(26.1, que cobre até 2025). A API da UCDP agora pede chave; o arquivo de download não pede.
**O que a base mede:** conflitos armados em que um dos lados é um governo e que deixaram 25 ou mais mortes em combate no ano. Para cada
um, informa os lados, quem apoia com tropas, o que está em disputa (território, governo ou os dois), o tipo (entre Estados, interno,
interno com tropas estrangeiras) e a intensidade (25 a 999, ou 1.000 ou mais mortes em combate no ano). Protestos, crises diplomáticas e
violência abaixo desse limite não entram, e o painel avisa isso.
**Como aparece:**
- No painel de cada país, os conflitos dos últimos 5 anos em que o país foi lado principal, apoiou com tropas ou que ocorreram no território
  dele, com os anos de participação do país.
- No "Mundo agora", a aba "Conflitos" lista os do último ano, os mais intensos primeiro.
**Cuidado de leitura:** a base registra como "apoio com tropas" também os países que mandam tropas para missões multinacionais, como as de paz
da ONU (o Brasil aparece assim na República Centro-Africana, ao lado de outros 38 países). Quando há mais de 5 países do mesmo lado, o painel
mostra quantos são e explica isso. Os nomes ficam como na base, em inglês.
**Códigos:** os países do protótipo foram ligados aos códigos Gleditsch & Ward da UCDP e conferidos contra os nomes "Government of …" da própria base.

### D44 · 04/11/2026 · Manchetes organizadas por assunto, dia e lugar
**Pedido:** as quatro formas sugeridas de organizar as notícias: por assunto, destaques no topo, linha do tempo e pelo mapa.
**Como:**
- **Assuntos mais cobertos (topo):** manchetes que dividem pelo menos duas palavras do título (fora as vazias e os nomes de países) viram um
  grupo. Os grupos cobertos por mais veículos diferentes sobem, até 4. O critério é o número de veículos, não uma opinião sobre importância.
  O grupo mostra as palavras em comum, para dar para conferir, e nada é resumido nem reescrito.
- **Linha do tempo:** o resto, por dia (Hoje, Ontem, data), com a hora de Brasília quando o feed informa o fuso. Sem fuso, a hora fica em branco.
- **Pelo mapa:** cada manchete é marcada com os países que o título cita, os 21 do protótipo e mais 34 frequentes no noticiário (`MENCOES`
  em `paises.py`, com os mesmos cuidados: acento e palavra inteira, sem termos ambíguos como "peru", "sírio" ou "libanês"). O globo pinta
  os países pelo número de manchetes da aba aberta (camada "Notícias"; a outra, "Países com dados", volta às cores de antes). Os botões
  "Onde" filtram a lista por país. Os países de `MENCOES` abrem um painel só com as manchetes que os citam.
- **Coleta:** a marcação roda junto com a de categorias, sobre todas as manchetes guardadas. Cada coleta guarda até 60 manchetes por país e
  100 em "Em alta no mundo" (antes, 30).

### D45 · 05/11/2026 · Notícias pausadas; o globo vira retrato histórico (portfólio)
**Pedido:** voltar o rotzx para projeto pessoal e portfólio. As notícias saem por ora (voltam no futuro como frente principal), e o globo passa
a mostrar a relação histórica e geopolítica de todos os países com o Brasil, sem coleta recorrente.
**Como:** `NOTICIAS = false` no topo do script do globo esconde abas, filtros, mapa de calor e blocos de manchetes, e o globo não busca mais
`noticias.json`. Os agendamentos do workflow Globo saíram (ficam comentados no arquivo, para reativar); a coleta passa a ser só à mão.
O código das notícias (`rss.py`, `gdelt.py`, marcação de países e assuntos) e os testes continuam no repositório.

### D46 · 05/11/2026 · Retrato histórico de todos os países com o Brasil, com seletor de ano
**Pedido:** portfólio com a relação histórica e geopolítica de todos os países com o Brasil, mais interativo, sem atualização recorrente.
**Tabela de países** (`rotzx/mundo/codigos.py` → `catalog/paises_mundo.csv`, versionada): 249 países com ISO numérico (id do mapa), ISO3,
nome em português de uso comum, códigos do Comex Stat, COW (ONU) e GW (UCDP). ISO e nomes oficiais vêm do pycountry (iso-codes do Debian).
O casamento por nome tem exceções escritas à mão e testadas: o "Congo" do Comex é a República do Congo; Dubai soma nos Emirados e Inglaterra
no Reino Unido; Alemanhas, Iêmens e Vietnã do Sul vão para os países de hoje (o painel avisa: fronteiras atuais).
**Coleta de uma vez** (`rotzx mundo-atualizar --historico` → `prototipos/globo/dados/historia.json|js`):
- comércio por país e ano de 1997 a 2025 numa consulta por fluxo (a API devolve `coAno`);
- produtos de todos os países num ano numa consulta (pares país × SH4), para 2000 e 2025;
- concordância na ONU de 1946 a 2024, com a mediana anual;
- conflitos por ano de 1946 a 2025: no território, como lado, com tropas;
- disputas na OMC com o Brasil;
- Banco Mundial para todos os países.
Ano sem dado fica nulo, nunca zero.
**Interface:**
- Embaixo do globo: indicador (Comércio, Saldo, Votos na ONU, Conflitos), ano de 1946 a 2025 e ▶. O globo pinta os países pelo indicador
  no ano e avisa quando o ano está fora da cobertura da fonte.
- À direita: ranking do ano, conflitos do ano e fontes.
- Painel de qualquer país, com gráficos (ECharts 5.5.0, a mesma versão do resto do site). Clicar num ponto muda o ano.
**Itamaraty:** o site responde com um desafio anti-robô (página de JavaScript), então não dá para ler nem conferir a página de cada país. O painel
leva ao índice oficial de relações bilaterais e diz para procurar o país lá; nenhuma "história" é escrita de cabeça.

### D47 · 06/11/2026 · Atlas "Como o Brasil se conecta ao mundo": o globo organizado pela relação comercial
**Pedido:** transformar o globo num atlas das relações e dependências comerciais do Brasil, guiado pela pergunta "de quem o Brasil depende
para vender e para comprar — e como isso mudou?". Diplomacia, conflitos e economia viram contexto.
**Dados:**
- A composição por produto passou a ter denominador exato. A consulta do Comex Stat traz todos os pares país × SH4 do ano, e para cada país
  em 2000, 2010 e 2025 ficam o total bilateral, o número de posições e os 10 maiores produtos.
- O explorador por produto (`produtos.json`) tem:
  - séries do Brasil por SH4 de 1997 a 2025, para 695 posições que passaram de US$ 50 milhões num ano;
  - 4 grupos somados sobre a distribuição completa: fertilizantes, petróleo e derivados, carnes, veículos e partes;
  - os 12 maiores parceiros de cada produto, mais o total do produto, em 2000, 2010 e 2025.
- Nomes curtos revisados para 79 posições (`rotzx/mundo/produtos_nomes.py`). O nome oficial e o código ficam sempre à mão. O código 9998 não
  tem descrição no Comex e aparece assim.
- A tabela de países ganhou o ISO de 2 letras (para as bandeiras) e o tipo (país ou território), com nomes ambíguos corrigidos ("Ilhas Virgens").
**Interface:** a página foi reescrita na mesma stack.
- Início com resumo do ano e perguntas que executam ações reais.
- Métricas do mapa (exportações, importações, corrente, participação, mudança em p.p.) com escalas fixas para todos os anos.
- Painel do país em três partes (relação comercial, produtos e concentração, contexto diplomático), com resumo por regras fixas.
- Explorar por produto e comparar dois parceiros.
- Bandeiras flag-icons 7.5.0 (MIT): bandeira atual, com substituto neutro quando não carrega.
- Estado na URL, com compatibilidade com `#China`.
- Lista funcional sem WebGL.
**Regras:**
- Dado ausente aparece como "sem registro", nunca como zero.
- Participações dizem o denominador. Há quatro, cada um com seu significado: destinos, origens, composição bilateral e fornecedores de um produto.
- Mudança de participação é dada em pontos percentuais, só com comércio registrado nos dois anos.
- Nenhuma nota de risco ou dependência: participação alta indica concentração, não vulnerabilidade.
**Limitações:**
- A composição por produto existe só em 2000, 2010 e 2025.
- O explorador guarda os 12 maiores parceiros de cada produto.
- Valores em dólares correntes, sem correção pela inflação.
- Países que não existem mais aparecem nas fronteiras atuais.
- Países pequenos ficam fora do mapa 1:110m, mas estão na lista e na busca.
**Notícias:** continuam pausadas. A interface delas está no histórico do git (`prototipos/globo/index.html` no commit `d193691`), e os
coletores em Python seguem no repositório.

### D48 · 06/11/2026 · Atlas: espaço de leitura, informação em dois níveis e continuidade da investigação
**Pedido:** refinar a experiência sem mudar o foco nem acrescentar funcionalidades. Mais espaço para as análises, menos detalhe técnico no meio da
leitura e uma pergunta seguida até o fim, sem perder o contexto.
**Espaço:**
- Na entrada, mapa e conteúdo dividem a tela. Nas análises (país, produto, comparação, ranking), o conteúdo ganha mais largura.
- "Ampliar análise" recolhe o mapa, e "Mostrar mapa" o devolve, sem perder nenhum filtro (`amplo=1` na URL). Gráficos e listas de produtos usam
  o espaço liberado.
- Uma barra de análise no fluxo da página mostra onde a pessoa está (ex.: Início › Fertilizantes › Importações › Rússia), o ano e o botão.
  Num ranking com o mapa recolhido, ela mostra também a métrica.
- No celular, a análise já abre com o mapa recolhido; a barra fica presa no topo.
**Dois níveis:**
- Sempre visíveis: nome legível, valor, participação com o que ela representa ("das compras brasileiras desse produto", "das vendas do Brasil a
  esse parceiro"), ano e fonte resumida.
- Sob demanda: "Detalhes" em cada produto (código SH4, descrição oficial, regra do grupo) e "Sobre este dado" em cada bloco (fórmula,
  denominador, cobertura, limitações).
- Avisos indispensáveis ficam visíveis: anos com distribuição por produto, "fora dos 12 maiores" não é zero, sem registro.
**Produto → país:**
- Clicar num fornecedor ou destino no explorador abre o país visto por aquele produto, fluxo e ano (`pais` + `prod` na URL). Mostra:
  - o valor;
  - a parte no total brasileiro do produto e a posição;
  - o peso do produto na relação bilateral;
  - os anos com distribuição por parceiro (2000, 2010, 2025, sem inventar série anual);
  - "Voltar aos fornecedores/destinos", que restaura filtros e a posição de leitura (guardada na sessão do navegador);
  - "Ver a relação comercial completa".
- A busca do topo sempre abre o painel geral, sem herdar o produto.
**Comparação:**
- Os dois parceiros ficam na URL (`a`, `b`; o antigo `vs` vira `b`). "Comparar com outro parceiro" mantém o país atual e deixa o segundo campo
  vazio, com instrução.
- Cada campo não oferece o país do outro. País repetido ou código inválido na URL vira um aviso recuperável.
- Destaque para as exportações (gráfico em US$, mesmo eixo) e para os produtos vendidos a cada um.
**Entrada:** três explorações em destaque, cada uma com título, uma frase calculada dos dados e uma ação:
- a China desde 2000: o painel ganha a tabela "2000 × 2025" em p.p. e os gráficos marcam os dois anos;
- os fornecedores de fertilizantes;
- China × Estados Unidos.
As outras perguntas ficam em "Outras perguntas".

### D49 · 06/11/2026 · Atlas: identidade editorial (tema claro, tipografia, globo cartográfico)
**Pedido:** transformar o atlas numa publicação econômica editorial, sóbria e agradável de explorar.
- **Referências:** a sobriedade e o conforto de leitura da Anthropic e a hierarquia editorial do NYT, sem copiar páginas, marcas ou fontes proprietárias.
- **Escopo:** só design e usabilidade. Dados, cálculos, funções e estado na URL não mudam.

**Identidade:**
- **Tema claro como principal.** Fundo `#F3F0E8`, superfície `#FAF8F3`, texto `#222721`, acento verde `#385344`, ocre `#A16D2F` e linhas `#D8D4C9`.
- **Tema escuro mantido.** Segue o sistema; um botão no cabeçalho alterna entre automático, claro e escuro, e a escolha fica no navegador.
- **Cores só por tokens CSS.** O globo e os gráficos leem os tokens e se redesenham ao trocar o tema.
- **Contraste conferido.** Texto, apoio e acento ficam acima de 4,5:1 nos dois temas. O ocre fica abaixo disso no claro (3,9:1), então só pinta barras e linhas; o texto que usa o ocre é escurecido.
- **Sem ornamento.** Saíram as caixas arredondadas, gradientes e sombras. Fundo preenchido só em seleção, resumo e agrupamento.

**Tipografia:**
- Newsreader (serifa, OFL) para títulos, descobertas e números de destaque.
- IBM Plex Sans (OFL) para texto e controles, com números tabulares em valores e tabelas.
- A IBM Plex Mono saiu.
- A hierarquia vem de tamanho, peso e espaço.

**Composição:**
- **Cabeçalho:** marca "rotzx" em serifa, descrição curta, navegação (Início, Parceiros, Produtos, Comparar), busca, Fontes e método, tema.
- **Entrada:**
  - propósito do projeto;
  - exploração principal (a China) com gráfico da participação 1997–2025, anotado em 2000 e no último ano;
  - duas secundárias em larguras diferentes: fertilizantes, com os três maiores fornecedores calculados quando os dados de produtos chegam, e China × EUA, com as exportações a cada um;
  - "Outras perguntas" em lista compacta e sempre visível.
- **País:** abertura própria com bandeira, nome, ano, leitura curta e uma faixa de indicadores separados por linhas finas, sem caixa por número. Abas com títulos em serifa; Home e End também funcionam.
- **Rankings:** posição, bandeira, nome, barra na própria linha e valor alinhado, com a escala explicada embaixo. Na "Mudança", a barra parte do centro. O país selecionado ganha fundo e marcador lateral.
- **Comparação:**
  - abre com o mapa recolhido no computador;
  - cada parceiro com bandeira, nome e a cor da sua série (A verde, B ocre) em todos os elementos;
  - no celular, cada medida vira um bloco, com o nome do país junto de cada valor.
- **Gráficos:**
  - fundo integrado e grade tracejada fina;
  - nome da série no fim da linha (legenda só quando falta o último ano);
  - rótulos curtos nas marcas do ano e do ano-base;
  - anotação do maior valor da participação nas exportações.
  - Sem animação ornamental; tabelas de dados e "sem registro" mantidos.
- **Globo:**
  - oceano liso e claro, sem a imagem Blue Marble nem relevo;
  - terra neutra para "sem registro" e contornos finos;
  - métricas em rampas de cor com as mesmas escalas fixas;
  - país selecionado em tinta escura e mais alto;
  - Brasil em cinza com contorno, por ser o ponto de vista, como diz a legenda.
- **Lista sem WebGL:** uma nota de uma linha, sem caixa de alerta; países sem registro num grupo próprio.

**Correção de exibição:** um fluxo sem registro no ano aparecia como "0% do total" no painel, na tabela "ano × ano" e na comparação. Agora aparece "sem registro", e a mudança em p.p. vira "—". O cálculo não mudou.

### D50 · 06/11/2026 · Atlas: mais espaço para a leitura, abertura que segue a pergunta, um controle de ano
**Pedido:** acabamento pontual, mantendo a identidade da D49. Dados, cálculos e funções continuam os mesmos.

**Espaço:**
- **Proporção:** na entrada, mapa ou lista ficam com cerca de 35% da largura e a leitura com 65% (mínimo de 340 px para o mapa). Nas análises, 33% e 67%. "Ampliar análise" continua igual.
- **Exploração principal:** o título ocupa a largura toda, com até 30 caracteres por linha (2 linhas em 1280, 1440 e 1920 px). Texto e gráfico ficam embaixo, em 5:7.
- **Lista no painel do mapa:** a barra fica sob o nome e o valor fica à direita, em duas linhas. Nomes e números mantêm o tamanho.

**Abertura que segue a pergunta:**
- **País aberto diretamente** (busca, ranking ou mapa): continua a relação comercial completa, com a posição na métrica.
- **País aberto a partir de um produto:** a abertura mostra o país, o produto ou grupo, o fluxo visto do Brasil, o ano, a posição nesse produto e fluxo, e a parte no total brasileiro desse produto.
  - "Principal fornecedor" ou "principal destino" só aparece quando o país é o 1º.
  - Fora dos 12 maiores, a abertura diz isso e lembra que não é zero.
  - O ranking geral da corrente sai da abertura e continua em "Ver a relação comercial completa".
- **Corpo da análise:** fica só com o que é diferente da abertura (valor, total do produto, peso na relação bilateral) e explica os dois denominadores.

**Controles do produto:**
- **Atalhos com rótulos curtos de navegação:** Soja em grão, Carnes, Veículos e peças, Telefones e redes, Medicamentos. O nome completo continua na dica do atalho, na análise e em "Detalhes"; códigos e filtros não mudam.
- **Um controle de ano**, o "Ano do recorte" na barra da análise, só com 2000, 2010 e 2025.
  - Saíram as faixas de ano do explorador e do painel produto → país.
  - O mapa mostra o ano, mas não oferece uma segunda escolha.
  - A série anual do Brasil diz que sua cobertura é completa, ao contrário da distribuição por parceiro.
- **Ano pedido sem recorte** (por exemplo, um link com 2023): a página usa o recorte anterior e avisa ("Não há distribuição por parceiro em 2023 … Mostrando 2010"). A URL passa a mostrar o ano usado.

### D51 · 06/11/2026 · Atlas: versão estável (cobertura do recorte, coerência, falhas e identidade brasileira)
**Pedido:** última rodada por enquanto. Corrigir a leitura dos dados, a navegação e o acabamento, sem novo redesenho, e dar um toque brasileiro aos detalhes.

**Cobertura do recorte por produto (problema confirmado):**
- **O problema:** a base detalha só os maiores parceiros de cada produto (até 12). Os demais estão somados em "Outros". Em fertilizantes 2010, a lista mostrava 12 países com dado e 236 "sem registro", embora a fonte registre 58 origens.
- **Como fica agora**, perto do resultado e calculado de cada produto, fluxo e ano:
  - texto do recorte: "12 maiores fornecedores detalhados neste recorte. A fonte registra 58 origens no total; as outras 46 estão somadas em 'Outros'";
  - "Outros" com quantidade e valor;
  - quando todos os parceiros estão detalhados (664 casos em que o total é 12 ou menos), o texto diz isso, e quem falta aparece como "sem registro", o que nesse caso é correto.
- **Três estados distintos** em mapa, legenda, dica do globo, lista, painel e tabela de anos:
  - detalhado;
  - fora do recorte detalhado (cinza próprio, "não é zero");
  - sem registro.
- **Lista do mapa:** os países fora do recorte ficam num grupo recolhido "sem detalhamento individual". Quais países estão em "Outros" não é informado, porque a base não diz.
- **Diferença entre totais:** a série anual de um produto pode ser maior que a soma por parceiro, porque inclui operações sem país definido (provisões para navios e aeronaves). Por exemplo, derivados de petróleo em 2010: US$ 3,1 bi contra US$ 2,2 bi. Acima de 1% de diferença, a página explica e diz qual total é o denominador. Conferido em 4.087 recortes: a série nunca é menor, e a mediana da diferença é 0.

**Coerência:**
- O gráfico do produto mostra só o fluxo da análise e se identifica como "Total do Brasil — todos os parceiros". No painel de um país, acrescenta "não só esse país".
- "Peso" virou "Participação" nos títulos. A parte do produto no comércio com o país virou "Parte do comércio com esse parceiro", e os dois denominadores aparecem juntos.
- No lugar de "Grupo de produtos", entra a regra do grupo (ex.: "Reúne posições 3101 a 3105").
- Aviso sobre as revisões do Sistema Harmonizado (2002, 2007, 2012, 2017 e 2022) em Fontes e nos detalhes de cada produto.
- Tabelas alternativas nos gráficos que não tinham: votos na ONU, conflitos e China × EUA da entrada.

**Navegação e estados:**
- **Avisos curtos sob a barra:**
  - ano fora da cobertura da métrica (ex.: votos na ONU em 2025 mostram 2024, com aviso);
  - ano sem recorte por parceiro;
  - país, métrica ou produto inválidos na URL.
- **"Ver todo o comércio com esse parceiro"** deixa clara a mudança de escopo.
- **Falha dos dados de produtos:** não há mais "Carregando…" eterno. Aparece uma mensagem com "Tentar de novo", e o resto do atlas segue funcionando.
- **Acessibilidade:** link "Ir para a análise" para teclado; tabelas largas rolam dentro do próprio componente.
- **Celular:** o mapa da entrada ficou mais baixo (32vh) e ganhou o botão "Ler a análise ↓".

**Identidade brasileira nos detalhes:**
- **Carregamento com a silhueta do Brasil:**
  - contorno do Natural Earth 1:50m (domínio público, o mesmo do mapa), simplificado num SVG embutido, sem serviço externo;
  - a silhueta se traça e se preenche de verde;
  - só aparece depois de cerca de 0,35 s, para não piscar em cargas rápidas;
  - não finge medir progresso;
  - vira desenho estático com movimento reduzido;
  - é anunciada uma vez como status.
- **Assinatura no fim da entrada:** "Pátria amada, Brasil.", em serifa itálica, com o contorno do Brasil, um ponto ocre e a referência do retrato ("coletado em 06/11/2026, sem atualização em tempo real").
