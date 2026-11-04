# rotzx — Avaliação inicial (Fase 1)

*Data: 02/11/2026 · Autor: Claude (assistente de desenvolvimento) para Lucas Faria Galera*

Este documento responde aos oito pontos da "primeira tarefa" do prompt mestre. Onde algo **não pôde ser verificado**, isso está dito explicitamente.

---

## 1. Avaliação crítica da proposta

**Veredito curto:** a proposta é boa como *laboratório pessoal de pesquisa* e viável como *portfólio*. Como *negócio*, ainda é uma hipótese. O plano com quatro módulos é grande demais para 2 a 3 horas por semana se for tratado como um único produto.

Conta rápida: 2,5 h/semana dão cerca de 130 h/ano. Uma versão honesta dos quatro módulos, com IA, previsões com backtesting e atlas internacional, leva facilmente de 600 a 1.000 h, mesmo com IA escrevendo boa parte do código. O gargalo não é digitar código. É **revisar, entender e validar** o que foi feito, e isso não se terceiriza.

### Avaliação por módulo

| Módulo | Utilidade para você | Diferenciação possível | Risco/esforço | Recomendação |
|---|---|---|---|---|
| **Radar Brasil** | Alta | Média: indicadores existem em todo lugar; o diferencial é a leitura (IPFF, poder de compra bem feito) | Baixo | **Começar aqui** (já iniciado) |
| **MacroForecast** | Alta | **Alta**: quase ninguém publica um *placar* honesto de previsões contra o Focus | Médio | **Segundo**, e começar a *registrar previsões cedo*, porque o histórico de acertos só se acumula em tempo real |
| **Radar Setorial** | Alta (FP&A, energia/elétrico) | **Alta para B2B**: ligar indicadores à demanda de uma empresa | Médio-alto (dados setoriais têm licença restrita) | Terceiro. É o módulo com mais chance de gerar receita |
| **Brasil x Mundo** | Média | **Baixa**: Our World in Data, FMI DataMapper e Banco Mundial já fazem isso de graça e muito bem | Médio | **Adiar.** Fazer só estudos pontuais, sem "atlas" genérico |

### Riscos principais

1. **Licença dos dados da Macrodados.** O acesso via CORECON quase certamente é de uso pessoal/profissional, não de redistribuição. Nada que dependa desses dados pode ir para um produto público sem autorização escrita. **Consequência de arquitetura:** a base do produto deve ser formada por fontes públicas primárias (BCB, IBGE, Ipea, Banco Mundial). A Macrodados fica como ferramenta de descoberta e análise pessoal.
2. **Escopo.** Quatro módulos mais IA mais monetização é um risco real de abandono. A mitigação são entregas pequenas e utilizáveis a cada mês.
3. **IA que "inventa números".** O risco é real e só se resolve na arquitetura: a IA só fala de números que vieram de uma chamada de ferramenta, com a série e a versão citadas.
4. **Ilusão de rigor.** Gráficos bonitos com correlações espúrias são piores que nenhum gráfico. Cada análise precisa declarar o método e as limitações (o protótipo já mostra fonte, data de coleta e transformação aplicada).
5. **Monetização B2C de dados econômicos no Brasil é difícil**, porque há muita coisa gratuita de boa qualidade (BCB, IBGE, relatórios de bancos). A receita mais provável no início é **serviço** (estudos de demanda, boletins para empresas), com a plataforma como alavanca.

### Recomendações que mudam o plano original

- **Inverter parte da ordem:** a Fase 5 (MacroForecast) deve começar *em paralelo e pequena*, com o registro mensal de uma previsão simples de IPCA a partir de já. Em 12 meses você terá um placar real. Um placar não se compra nem se acelera.
- **Brasil x Mundo deixa de ser um módulo-produto** e vira uma série de estudos.
- **A IA vem depois do motor analítico** (como você mesmo previu) e deve ser enxuta: um assistente com ferramentas, não um chatbot genérico.
- **Simplificar a stack** (ver seção 4).

---

## 2. Pesquisa de mercado: concorrentes e diferenciação

> Observação: não verifiquei preços atuais. A busca pública trouxe poucas informações de preço; os valores devem ser confirmados nos sites oficiais.

| Categoria | Exemplos | O que oferecem | Lacuna explorável |
|---|---|---|---|
| Fontes oficiais gratuitas | BCB (SGS, Focus), IBGE (SIDRA), Ipeadata | Dados primários, APIs abertas | Pouca interpretação; navegação difícil para não especialistas |
| Agregadores globais gratuitos/freemium | Trading Economics, Our World in Data, FMI DataMapper, Banco Mundial | Comparação internacional, mapas | Pouca profundidade sobre o Brasil e nenhuma ligação com setores e empresas |
| Terminais profissionais | Macrobond, CEIC, Bloomberg, LSEG, Economatica, Broadcast | Cobertura enorme, Excel add-in | Caros e feitos para quem já sabe o que procura |
| Plataformas brasileiras de dados | Macrodados, FGV IBRE (dados pagos) | Séries históricas organizadas | Pouca camada analítica e de previsão aberta |
| Consultorias e research | LCA, Tendências, 4intelligence, research de bancos | Projeções, cenários, estudos setoriais | Caros (consultorias) ou genéricos (bancos); metodologia opaca |

**Diferenciais realistas (em ordem de defensabilidade):**

1. **Placar público de previsões** com metodologia aberta, erros registrados e comparação com o Focus. Credibilidade verificável é rara.
2. **Indicadores autorais documentados** (IPFF e outros), com testes de sensibilidade publicados.
3. **Inteligência de demanda para empresas médias**: "quais indicadores antecedem as *suas* vendas", um serviço que consultorias grandes cobram caro.
4. **Explicação em português, com rigor**: um economista registrado assinando as análises (o CORECON é um ativo de credibilidade).

O que **não** é diferencial: ter as séries (todo mundo tem) e ter IA (vira commodity rapidamente).

---

## 3. Macrodados: o que foi possível verificar

**Verificado publicamente:**
- O certificado do domínio `macrodados.com` cobre os subdomínios `web.`, `desktop.` e `abimaq.`. Isso indica que existem uma **versão web com login**, uma **versão desktop** e uma **instância ligada à ABIMAQ** (associação da indústria de máquinas, relevante para o Radar Setorial).
- A página `web.macrodados.com` é uma aplicação com tela de login; não há documentação pública de API nem termos de uso visíveis sem autenticação.
- Um termo de referência de contratação do Senado Federal (2023) cita assinatura de R$ 890/mês para 5 licenças, consultada em nov/2023. É um valor antigo e não confirmado hoje.

**Atualização de 02/11/2026 (verificado com acesso logado):** são 1.321 tabelas; a exportação é manual (XLSX, XLS ou CSV) e não há API visível. Os Termos de uso proíbem copiar, redistribuir ou republicar o conteúdo. Ver D13 em `DECISOES.md`.

**Não verificado na época (você precisava conferir dentro do seu acesso):**
- Se o acesso via CORECON-SP permite exportar para Excel/CSV, e em quais formatos.
- Se existe API e se ela está incluída no seu tipo de acesso (provavelmente não).
- Os termos de uso: uso pessoal × profissional × redistribuição × uso comercial de dados derivados.

**Perguntas para enviar por escrito à Macrodados (ou ao CORECON-SP):**
1. Meu acesso via CORECON-SP permite exportar séries para Excel/CSV para análise própria?
2. Posso publicar gráficos ou análises derivados (por exemplo, um índice calculado) citando a Macrodados como fonte? Com que restrições?
3. Existe API? Em que plano, e com que licença de uso?
4. Há licença específica para uso comercial ou redistribuição em uma plataforma própria?

**Integração adotada (já implementada no protótipo):**
- **Importador de arquivos** (CSV/Excel) com metadados obrigatórios: fonte de aquisição, restrição de uso e o arquivo original guardado com hash SHA-256. Séries importadas da Macrodados recebem `uso = pessoal` por padrão e a interface sinaliza isso.
- **Fontes públicas primárias** via API oficial: BCB/SGS e IBGE/SIDRA (licenças abertas, com citação da fonte).
- **Provedor de API Macrodados**: apenas uma interface prevista, a ser implementada se houver licença. Nenhum scraping.

---

## 4. Arquitetura proposta

### Crítica à stack sugerida

- **Next.js + React + TypeScript + FastAPI** são duas linguagens, dois ecossistemas e duas ferramentas de build. Para quem não é desenvolvedor e tem 2 a 3 h/semana, isso dobra a superfície de manutenção sem ganho no estágio atual. (O Node nem está instalado na sua máquina.)
- **PostgreSQL** não é necessário antes de existirem usuários concorrentes.
- **Plotly × ECharts:** ECharts é leve, bonito, funciona por CDN e lida bem com séries longas. Escolhido.

### Stack adotada (proporcional)

| Camada | Escolha | Por quê | Quando trocar |
|---|---|---|---|
| Núcleo analítico | **Pacote Python** (`econatlas/`) com pandas | É onde fica a propriedade intelectual; independe da interface | Nunca: é o ativo |
| Armazenamento | **SQLite** (biblioteca padrão) + arquivos brutos imutáveis | Zero instalação; um arquivo; versionável | DuckDB para análises pesadas; Postgres com multiusuário |
| API | **FastAPI** | Simples, documentação automática em `/docs` | — |
| Interface | **HTML + JavaScript puro + ECharts (CDN)** servidos pela própria API | Nenhum passo de build; fácil de entender | Next.js quando houver login, páginas públicas com SEO ou equipe |
| Estatística | statsmodels / scikit-learn (Fase 3+) | Padrão da área | — |
| IA | API de LLM com *tool calling* sobre as funções do núcleo (Fase 4) | Números vêm sempre de ferramentas | — |
| Testes | pytest | — | — |
| Hospedagem | Local agora; depois uma VPS pequena (US$ 5–10/mês) | Custo mínimo | — |

### Camadas de dados

```
Provedor (BCB, IBGE, arquivo Macrodados...)
   │  coleta
   ▼
data/raw/<provedor>/<série>/<timestamp>.<ext>   ← resposta original, imutável, com SHA-256
   │  normalização
   ▼
SQLite: vintages (cada coleta = uma versão) + observations (série, data, valor, versão)
   │  transformações declaradas (var. 12m, acumulado, média móvel...)
   ▼
API → interface / IA / relatórios      (toda resposta informa série, fonte, versão e transformação)
```

Guardar **cada coleta como uma versão** permite rastrear revisões (o PIB é revisado, por exemplo) e, no futuro, fazer backtests "em tempo real", usando apenas o dado disponível na data.

---

## 5. Catálogo inicial de indicadores (28)

Legenda: ✅ = já no protótipo, com código testado na API · 🔎 = fonte identificada, código/tabela a localizar · ⚠️ = licença restrita, verificar antes de publicar.

### Radar Brasil

| # | Indicador | Fonte (código) | Period. | Justificativa |
|---|---|---|---|---|
| 1 | IPCA – variação mensal | BCB/SGS 433 ✅ | Mensal | Inflação oficial; base do poder de compra |
| 2 | IPCA – acumulado 12 meses | BCB/SGS 13522 ✅ | Mensal | Comparação com a meta; teste de consistência com a série 433 |
| 3 | Meta Selic | BCB/SGS 432 ✅ | Diária | Instrumento da política monetária |
| 4 | Selic acumulada no mês, anualizada | BCB/SGS 4189 ✅ | Mensal | Versão mensal para cruzar com outras séries |
| 5 | Câmbio R$/US$ (média mensal) | BCB/SGS 3698 ✅ | Mensal | Repasse cambial, comércio exterior |
| 6 | IBC-Br dessazonalizado | BCB/SGS 24364 ✅ | Mensal | Proxy mensal da atividade |
| 7 | PIB – variação contra o mesmo trimestre do ano anterior | IBGE/SIDRA 5932 ✅ | Trimestral | Crescimento oficial |
| 8 | Taxa de desocupação | BCB/SGS 24369 (PNAD Contínua) ✅ | Mensal (trim. móvel) | Mercado de trabalho |
| 9 | Rendimento médio real habitual | IBGE/SIDRA 5436 ✅ | Trimestral | Poder de compra do trabalho |
| 10 | Massa de rendimento real | IBGE/SIDRA (PNAD Contínua) 🔎 | Trimestral | Renda agregada: "o PIB vira renda?" |
| 11 | Taxa média de juros – PF | BCB/SGS 20716 ✅ | Mensal | IPFF |
| 12 | Inadimplência – PF | BCB/SGS 21084 ✅ | Mensal | IPFF (validação) |
| 13 | Comprometimento de renda das famílias | BCB/SGS 29034 ✅ | Mensal | IPFF |
| 14 | Endividamento das famílias | BCB/SGS 29037 ✅ | Mensal | IPFF |
| 15 | Saldo de crédito – PF | BCB/SGS 20541 ✅ | Mensal | Ciclo de crédito |
| 16 | IPCA por grupos (alimentação, habitação...) | IBGE/SIDRA 7060 🔎 | Mensal | Inflação desigual entre categorias |

### MacroForecast

| # | Indicador | Fonte | Period. | Justificativa |
|---|---|---|---|---|
| 17 | Expectativas Focus (IPCA, Selic, PIB, câmbio) | BCB – API Olinda de Expectativas 🔎 | Diária/semanal | Benchmark obrigatório das previsões |
| 18 | Produção industrial (PIM-PF) | IBGE/SIDRA 🔎 | Mensal | Alvo de previsão e indicador antecedente |
| 19 | Vendas no varejo (PMC) | IBGE/SIDRA 🔎 | Mensal | Consumo |
| 20 | Volume de serviços (PMS) | IBGE/SIDRA 🔎 | Mensal | Setor mais pesado do PIB |

### Radar Setorial

| # | Indicador | Fonte | Period. | Justificativa |
|---|---|---|---|---|
| 21 | Produção industrial por atividade (incl. máquinas e materiais elétricos) | IBGE/SIDRA (PIM-PF por seção/atividade) 🔎 | Mensal | Base do painel setorial |
| 22 | Emprego formal por setor | Novo Caged (MTE) 🔎 | Mensal | Antecipa atividade setorial |
| 23 | Carga de energia elétrica | ONS – dados abertos 🔎 | Diária/mensal | Proxy de atividade de alta frequência; ligado ao seu setor |
| 24 | Custo da construção (SINAPI) | IBGE/SIDRA 🔎 | Mensal | Construção civil (o INCC da FGV tem licença restrita ⚠️) |
| 25 | Utilização da capacidade / confiança industrial | CNI / FGV ⚠️ | Mensal | Antecedentes clássicos; verificar licença |

### Brasil x Mundo

| # | Indicador | Fonte (código) | Period. | Justificativa |
|---|---|---|---|---|
| 26 | PIB per capita PPC, preços constantes | Banco Mundial WDI `NY.GDP.PCAP.PP.KD` | Anual | Convergência de renda |
| 27 | Formação bruta de capital fixo (% PIB) | Banco Mundial WDI `NE.GDI.FTOT.ZS` | Anual | Investimento × crescimento |
| 28 | PIB por pessoa ocupada / PTF | Banco Mundial WDI `SL.GDP.PCAP.EM.KD`; Penn World Table | Anual | Produtividade |

> **Pendência de rigor:** a API de metadados do BCB não respondeu durante esta sessão. Os **nomes** das séries do SGS no catálogo foram escritos a partir de conhecimento prévio e de valores plausíveis, mas não foram conferidos contra a ficha oficial. Elas estão marcadas como "a conferir" no catálogo e na interface. As séries do IBGE vieram com descrição oficial da própria API.

### Proposta do IPFF (Índice de Pressão Financeira das Famílias), experimental

- **Componentes candidatos** (sinal: ↑ = mais pressão): juros PF (↑), comprometimento de renda (↑), endividamento (↑), variação real do rendimento (↓), inflação de itens essenciais (alimentação + habitação) (↑).
- **Inadimplência fica de fora da composição** e é usada para **validação**. Se ela fosse componente, a validação seria circular.
- **Normalização:** z-score em janela **expansiva** (cada ponto usa apenas o passado), para evitar olhar o futuro. Alternativa: percentil histórico.
- **Pesos:** (a) iguais, como referência; (b) primeira componente principal; (c) pesos que maximizam o poder de antecipar a inadimplência, *estimados fora da amostra*. Publicar os três e explicar as diferenças.
- **Sensibilidade:** retirar um componente por vez, trocar a janela de normalização, trocar a série de juros.
- **Validação:** o IPFF antecipa a inadimplência PF e as vendas no varejo de 3 a 6 meses? (correlação com defasagem e regressão fora da amostra, sem afirmar causalidade).
- **Limitação declarada:** é um índice de *pressão financeira agregada*, construído a partir de médias nacionais. Não mede a situação de famílias específicas nem a distribuição entre faixas de renda.
- **Cobertura:** limitada pela série mais curta (comprometimento/endividamento começam em 2005). Na prática, a análise começa por volta de 2012, com a PNAD Contínua.

---

## 6. MVP: a menor versão útil

**MVP = "Radar Brasil v0 + caderno de previsões"**

Entra agora (✅ já feito no protótipo de hoje):
- ✅ Navegação entre os 4 módulos (3 deles como páginas estruturais honestas, sem dados falsos)
- ✅ 14 séries públicas reais com metadados completos, versões e arquivo bruto
- ✅ Painel com cartões (último valor, data, fonte) e gráficos com filtro de período e transformações
- ✅ Página de série com metadados, histórico de coletas e restrições de uso
- ✅ Comparação de duas séries (eixo duplo)
- ✅ Importador de CSV/Excel (para exportações da Macrodados) com rastreabilidade
- ✅ Teste de consistência entre fontes (IPCA 12m calculado × publicado)
- ✅ Modo claro/escuro, layout responsivo

Próximas entregas do MVP:
- IPFF v0 com documentação metodológica
- Previsão mensal de IPCA (modelo sazonal ingênuo + SARIMA) registrada em log imutável, comparada ao Focus

**Fica para depois:** assistente de IA, PDF, login/assinaturas, mapas, Setorial completo, dados de empresas, Postgres, deploy público.

---

## 7. Cronograma (≈ 10 h/mês)

| Período | Entrega | Horas aprox. |
|---|---|---|
| Nov/2026 (sem. 1–2) | Rodar o protótipo; conferir os rótulos do SGS; enviar perguntas à Macrodados/CORECON | 4 |
| Nov–Dez/2026 | Radar Brasil v0.2: linha do tempo de eventos, deflação de séries, poder de compra | 15 |
| Dez/2026–Jan/2027 | **IPFF v0** (cálculo + sensibilidade + nota metodológica) | 15 |
| Jan–Mar/2027 | **MacroForecast v0**: benchmarks para o IPCA, backtest com origem móvel, comparação com o Focus, log de previsões | 25 |
| Mar–Abr/2027 | Assistente de IA v0 (ferramentas sobre a API, citações obrigatórias) | 15 |
| Abr–Jun/2027 | Radar Setorial v0 (indústria, materiais elétricos, construção, energia) + **5 a 10 entrevistas de validação** | 25 |
| Jul–Set/2027 | Primeiro produto testável: boletim mensal ou estudo de demanda piloto | 20 |
| 2027 S2+ | Brasil x Mundo (estudos), deploy público, decisão sobre monetização | — |

Regra de ouro: **cada mês termina com algo que funciona**, mesmo que pequeno.

---

## 8. Monetização: públicos e hipóteses a testar

**Públicos com maior necessidade (em ordem de prioridade):**
1. **FP&A e planejamento comercial em indústrias médias** (energia, materiais elétricos, máquinas): precisam de cenários e de "drivers" de demanda, e não têm economista na equipe.
2. **Consultores e analistas independentes**: querem velocidade e indicadores prontos.
3. **Associações setoriais e câmaras de comércio**: boletins e estudos.
4. **Público amplo interessado em economia** (newsletter): audiência, pouca receita direta.

**Hipóteses (cada uma testável e barata):**

| Hipótese | Teste | Critério de sucesso |
|---|---|---|
| H1. Gestores de FP&A pagariam por um estudo "indicadores × suas vendas" | 5 a 10 entrevistas + 1 piloto gratuito com dados reais de uma empresa | ≥ 2 pedem proposta paga |
| H2. Um boletim mensal com IPFF + placar de previsões atrai audiência qualificada | Publicar 6 edições (LinkedIn/Substack) | ≥ 300 inscritos, ≥ 30% de abertura |
| H3. O placar de previsões gera credibilidade | 12 meses de previsões registradas, com erro competitivo ante o Focus | Erro dentro da faixa do Focus |
| H4. Indivíduos pagariam assinatura | Página de lista de espera com preço indicativo | Taxa de conversão; só testar depois de H2 |

**Avaliação honesta:** a receita mais provável nos primeiros 12–18 meses é **serviço** (estudos e boletins sob demanda), não assinatura de software. A plataforma reduz o custo de produzir esses serviços e sustenta a credibilidade.

---

## Fontes consultadas
- [web.macrodados.com](https://web.macrodados.com/) (estrutura da aplicação web; certificado do domínio)
- [Termo de referência do Senado Federal (2023)](https://www12.senado.leg.br/transparencia/licitacoes-e-contratos/sadcon/tr-7.pdf) (preço e posicionamento da Macrodados)
- [Trading Economics – sobre](https://tradingeconomics.com/about-te.aspx) · [ipeadatar (CRAN)](https://packages.oit.ncsu.edu/cran/web/packages/ipeadatar/index.html) · [Macrobond (The Wealth Mosaic)](https://www.thewealthmosaic.com/vendors/macrobond/)
- APIs testadas nesta sessão: `api.bcb.gov.br/dados/serie/bcdata.sgs.*`, `apisidra.ibge.gov.br`, `servicodados.ibge.gov.br`
