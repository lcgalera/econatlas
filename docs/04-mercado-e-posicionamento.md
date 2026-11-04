# rotzx — Mercado, concorrência e posicionamento (crítica das premissas)

Data: 04/11/2026. Base: buscas na web (links no fim). **Nenhuma conversa com cliente foi feita**; tudo aqui é hipótese a testar.
As afirmações sobre concorrentes vêm das páginas e reportagens citadas, não de testes dos produtos.

## 1. O que a pesquisa mudou na minha leitura

### O dado bruto de transmissão é público, gratuito e já é resumido pela própria ANEEL

- A fase de implantação das concessões de transmissão é fiscalizada pela ANEEL por meio do próprio SIGET, e o conjunto está no portal de dados abertos, com API.
- A ANEEL publica editais, cronogramas e resultados dos leilões de transmissão logo após cada leilão.
- A imprensa setorial noticia cada leilão com lote, vencedora, RAP e deságio no mesmo dia (ex.: o Leilão 4/2026, em 30/10/2026, teve oito lotes).

**Consequência:** "lista de projetos de transmissão" não é produto. Um representante comercial do nicho já sabe quem ganhou o último leilão.
O que pode valer dinheiro é o que **não** sai na notícia: o que cada empreendimento vai precisar (módulos e equipamentos), **quando**
(datas previstas, atrasos e antecipações) e **o que mudou** desde a última vez, com isso cruzado com o catálogo do fornecedor.

### O universo é pequeno

Cada leilão de transmissão tem algo como 5 a 15 lotes, e os empreendimentos em implantação acompanhados pela ANEEL somam dezenas, não milhares
(as reportagens falam em ~60 obras num ciclo de acompanhamento). Um fornecedor consegue acompanhar isso numa planilha.
O produto precisa poupar **leitura técnica e acompanhamento de mudanças**, não "descoberta" em volume.

### Os compradores são poucos e grandes

Transmissoras (Axia/Eletrobras, ISA Energia, Taesa, Alupar, Celeo, Neoenergia, EDP, CYMI…) e seus EPCistas compram por cadastro e
homologação de fornecedores e por cotação privada. A maior parte dessas compras não passa por edital público.
Para **grandes fabricantes**, que já têm equipe de key account dentro dessas empresas, o radar tende a valer pouco.
Para **fabricantes médios, distribuidores técnicos e representantes comerciais**, que não têm essa equipe, a hipótese de valor é mais forte.

## 2. Concorrentes e substitutos

| Quem | O que oferece (segundo o próprio material ou reportagens) | Ameaça para o rotzx |
|---|---|---|
| Rede de Obras, Obras Online, ConstruConnect, Conecta Obras | Bases de obras (incluindo infraestrutura e indústria) com fase, responsáveis e contatos, para prospecção B2B. Obras Online diz atuar há mais de duas décadas | **Alta em "lista de obras com contato"**: já fazem isso há anos e com equipe de apuração. Baixa em leitura técnica de módulos e equipamentos da transmissão |
| BNamericas | Base de projetos da América Latina (mais de 31 mil projetos), notícias e empresas, com cobertura dos leilões de transmissão do Brasil; preço sob consulta | **Alta para grandes empresas** com orçamento de assinatura internacional |
| Neoway, Oportunidados | Dados de empresas (Receita, CNO) e analytics de construção | Média: enriquecimento de empresas, não interpretação de projetos |
| Imprensa setorial (CanalEnergia, MegaWhat, eixos, Agência iNFRA, Brasil Energia) | Notícias de leilões, atrasos e contratos | **Substituto gratuito** para a camada de "o que aconteceu" |
| Planilha do próprio fornecedor + portal da ANEEL | O que o comprador faz hoje | **O concorrente real.** O rotzx precisa ser claramente melhor do que isso em tempo gasto e no que se fica sabendo |

Não verifiquei a profundidade de cada produto no setor elétrico. **Nada aqui autoriza dizer que um diferencial é exclusivo do rotzx.**

## 3. Diferenciais que parecem sustentáveis

1. **Leitura técnica dos dados oficiais de transmissão:** módulo → categoria de equipamento, com evidência e nível (confirmado ou inferido).
   As plataformas de obras são generalistas, e a imprensa não chega nesse nível. Isso só se confirma se o SIGET trouxer módulos e equipamentos.
2. **Alertas de mudança**, que são a razão para voltar ao produto: nova obra, nova data prevista, atraso, antecipação, mudança de situação.
   O padrão de vintages com SHA-256 do projeto já é a base técnica disso.
3. **Rastreabilidade**, que o EconAtlas/rotzx já pratica: cada linha com fonte, data de coleta e link. Isso dá confiança, mas sozinho não gera venda.
4. **Contexto econômico do setor** (juros, crédito PJ, produção da CNAE 27): complemento. Sozinho não sustenta preço (ver o diagnóstico: o sinal é fraco).

## 4. Mudanças de rumo que eu recomendo

### a) MVP "concierge": vender o relatório antes de construir a interface

A primeira entrega paga deveria ser um **relatório** (HTML/PDF + CSV) gerado pelo pipeline e revisado por você, e não uma interface SaaS.
Motivos: com 2–3 h por semana, uma interface com filtros, detalhe e acompanhamento custa semanas, e ainda não sabemos o que o comprador quer ver.
O relatório testa a mesma hipótese de valor com uma fração do esforço, e o que o cliente pedir no relatório vira a especificação da interface.

**Ordem revisada:** Fase 2 (pipeline) → Fase 3 (regras e evidência) → **relatório exportável** → conversas e piloto → só então a interface (Fase 4).

### b) Começar as conversas com compradores agora, em paralelo ao código

Hoje o maior risco é não existir comprador, não ser difícil construir. Cinco conversas de descoberta (sem vender nada) custam
cerca de 5 horas e podem invalidar o nicho antes de semanas de código. Roteiro em [`05-validacao-com-compradores.md`](05-validacao-com-compradores.md).

### c) Manter a distribuição como hipótese concorrente, não como "expansão futura"

A distribuição tem **muito mais compradores** (dezenas de distribuidoras, além de permissionárias e cooperativas) e um volume grande
de itens padronizados (transformadores de distribuição, cabos, isoladores, para-raios, medidores), o que pode combinar melhor com fornecedores pequenos e médios.
O PDD da ANEEL é agregado e não lista obra a obra, então o produto seria diferente (inteligência de mercado por distribuidora e região, não radar de projetos).
**Recomendação:** nas conversas da seção b, perguntar também sobre distribuição. Se a dor for maior lá, mudar o nicho antes da Fase 2.

### d) Não liderar o pitch com previsão econômica

A previsão do IPCA e o modelo de juros mostram rigor e servem de prova de método, mas não são o motivo da compra.
Na home e nas demonstrações, o setor e as mudanças nos projetos vêm primeiro, e a macroeconomia entra como contexto.

## 5. Hipótese de preço (a testar, não referência)

As faixas do plano mestre (R$ 500–1.500 por piloto; R$ 700–2.000 por mês) são plausíveis para pequenas e médias empresas,
mas só valem depois de alguém dizer "sim" com dinheiro. Na conversa, o sinal útil não é "eu pagaria", e sim:
(1) quanto tempo ou dinheiro a empresa gasta hoje com isso, (2) quem aprova a compra e (3) se ela aceita um piloto pago com data.

## Fontes

- ANEEL — Portal de Dados Abertos, conjunto SIGET: https://dadosabertos.aneel.gov.br/dataset/sistema-de-gestao-da-transmissao-siget
- ANEEL — Expansão da transmissão: https://www.gov.br/aneel/pt-br/assuntos/transmissao/expansao-da-transmissao
- TCU — auditoria de leilão de transmissão: https://portal.tcu.gov.br/imprensa/noticias/auditoria-analisa-leilao-para-concessao-de-transmissao-de-energia-eletrica
- eixos — atrasos em linhas de transmissão: https://eixos.com.br/energia-eletrica/licenciamento-ambiental-e-responsavel-por-70-dos-atrasos-em-linhas-de-transmissao/
- Cenário Energia — antecipação de obras de transmissão (2025): https://cenarioenergia.com.br/2025/07/11/concessionarias-preveem-antecipar-metade-das-obras-de-transmissao-em-construcao-no-brasil/
- Canal Solar — Leilão de transmissão 4/2026: https://canalsolar.com.br/leilao-de-transmissao-axia-alupar-vencedores/
- Times Brasil — Leilão de transmissão 4/2026: https://timesbrasil.com.br/empresas-e-negocios/energia/leilao-de-transmissao-termina-com-oito-lotes-arrematados/
- Rede de Obras: https://rededeobras.construmarket.com.br/
- Obras Online: https://obrasonline.com.br/
- ConstruConnect (fornecedores): https://construconnect.com.br/fornecedores/
- Conecta Obras: https://www.conectaobrasbr.com/en/internacional
- Neoway, construção civil: https://www.neoway.com.br/vertical/construcao-civil
- Oportunidados: https://oportunidados.com.br/
- BNamericas, transmissão no Brasil: https://www.bnamericas.com/en/news/brazil-power-transmission-tender-attracts-nearly-us3bn-in-investments
