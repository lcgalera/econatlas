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
