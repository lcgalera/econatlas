# rotzx — Validação de fonte: ANEEL SIGET (Fase 1)

Coleta: 04/11/2026, 13:22 UTC (arquivos gerados pela ANEEL em 02/11/2026 e 04/11/2026). Situação: **fonte validada; decisão: seguir com o SIGET.**

> Contém dados da ANEEL (SIGET, Portal de Dados Abertos), disponibilizados sob a licença ODbL.

## 1. Como foi feito

```bash
.venv/bin/python -m rotzx fonte-explorar siget                                                # lista os recursos
.venv/bin/python -m rotzx fonte-explorar x --conjunto sistema-de-gestao-da-transmissao-siget   # baixa e gera o perfil
.venv/bin/python -m rotzx siget-amostra                                                       # visão por empreendimento + amostra
```

O comando baixou 17 CSVs (~175 MB, sendo 135 MB a lista de módulos do reajuste da RAP) para `data/fontes/aneel/sistema-de-gestao-da-transmissao-siget/brutos/`,
com SHA-256, e os dicionários em PDF para `dicionarios/`. Tudo isso fica fora do git. O perfil completo dos campos está em `relatorio.md`, na mesma pasta.

## 2. Respostas às perguntas da validação

| # | Pergunta | Resposta (com a coluna de origem) |
|---|---|---|
| 1 | Recursos, formato e licença | 17 CSVs, cada um com dicionário em PDF (versão 1.0, 28/04/2023), mais um Parquet. **Licença ODbL**. Atualização **diária**, segundo o dicionário; os arquivos coletados foram gerados em 02/11 e 04/11/2026 (`DatGeracaoConjuntoDados`). |
| 2 | Chaves e ligações | `IdeEpd` (empreendimento), `IdeObr` (obra), `IdeMdl` (módulo) e `IdeCcd` (contrato). Medido: 100% dos módulos de equipamento, manobra e linha estão no arquivo de empreendimentos; 100% dos contratos dos empreendimentos estão no arquivo de agentes; 100% dos empreendimentos de resolução estão no de contrato. `IdeOnsEpd` (ex.: `T2023-161`) é o código do ONS, útil para cruzar com outras fontes. |
| 3 | Equipamento por módulo | **Sim.** Módulos de equipamento com tipo (`DscTipEqp`: transformador de potência, reator de linha e de barra, banco de capacitores, compensador síncrono e estático, conversora, capacitor série, transformador de aterramento, banco de filtros), fases, tensão (`NumTnsMdl`), potência em MVA (`MdaPotAtvMdlEqp`, preenchida em ~51% dos casos em andamento) e UF. Módulos de manobra com tipo (entrada de linha, conexão, interligação de barramento), arranjo e quantidade de disjuntores e de chaves seccionadoras (preenchida em só ~11% dos casos em andamento). Linhas com tensão, circuito, quantidade de torres e cabos (os campos de cabo não estão no dicionário). |
| 4 | Situação | `DscSituacaoEpd`, 100% preenchida: Em Operação 2.029, **Em andamento 754**, Concluído 58, Planejado 19, vazio 1 (de 2.861 empreendimentos). |
| 5 | Datas | `DatOprComEpd` (operação comercial **fixada pelo ato legal**) e `DatCaoCgmAtoLgl` (conclusão prevista no ato legal), 100% preenchidas nos empreendimentos em andamento. 727 deles têm data futura, de 2026 a 2035 (quase todos até 2031); 27 têm data já vencida. **A data prevista pela própria transmissora não está nestes CSVs**: segundo o dicionário, ela sai no Relatório de Monitoramento mensal, e é informada pela concessionária sem interferência da ANEEL. |
| 6 | Concessionária | Razão social, CNPJ e número do contrato (`DscRazaoSocial`, `NumCNPJ`, `NumCnaCcd`) para 100% dos empreendimentos em andamento. Quem mais tem empreendimentos em andamento: ISA Energia Brasil (191), AXIA (98), AXIA Norte (78), AXIA Nordeste (71), CPFL Transmissão (47), CEMIG-GT (34). |
| 7 | Localização | UF das subestações via módulos em 95% dos empreendimentos em andamento (SP 236, MG 87, RS 62, BA 46, PR 43). Não há município nem coordenada. |
| 8 | Frequência de mudança | O dicionário diz que a atualização é diária. **Ainda não medido**: falta uma segunda coleta para comparar SHA-256 e linhas. |
| 9 | Fração não concluída | 754 de 2.861 (26%) em andamento, e 652 deles têm módulo de equipamento ligado a obra em andamento. |

**Descoberta relevante para o produto.** Dos 754 empreendimentos em andamento, **616 são autorizações** (reforços e melhorias autorizados por
resolução ou despacho em concessões que já existem: `CodReg` REA/DSP, com link do documento em `DscLink`) e 138 vêm de contrato de concessão
(leilão). As autorizações quase não aparecem na imprensa, são muitas e são concretas (ex.: "substituição do TR2 e TR3 230/69 kV – 33 MVA por dois TRs de 100 MVA").
A classificação "autorização × contrato" é **inferida** pela presença do empreendimento no arquivo de resolução; confirmar com a ANEEL ou no dicionário.

**Defeitos e limites da fonte encontrados:**
- `DscSituacaoModulo` repete o nome do módulo em vez da situação, nos dois arquivos que têm esse campo. Não usar.
- Campos fora do dicionário: `IdcSitMdl`, `NumOprMdl` e os campos de cabos das linhas. Códigos sem significado documentado não são usados.
- `NumEtnLinTms` é descrito como "número de extensões": a unidade (km?) não está declarada.
- Os links de documentos (`DscLink`) apontam para `www.aneel.gov.br/cedoc/…`, que não pôde ser aberto deste ambiente. É preciso verificar se o domínio antigo redireciona.
- `VlrHisRct` é a **receita** (RAP) atualizada do último ciclo, não o valor de compra nem o investimento.
- Tipo de obra "Adequação" inclui substituições: o tipo sozinho não diz se há equipamento novo, então é preciso ler `DscObr` ou `DscEpd`.
- Contratos novos entram depois da assinatura (o mais recente é de 10/09/2026). Lotes de leilão ainda não assinados não aparecem: o resultado do leilão continua sendo um sinal mais cedo.

## 3. Critério de decisão (fixado antes de ver os dados) e resultado

| Condição | Exigido | Medido | |
|---|---|---|---|
| (a) chave estável ligando ≥ 2 tabelas | sobreposição ≥ 90% | 100% (`IdeMdl`, `IdeCcd`, `IdeEpd`) | ✔ |
| (b) situação preenchida | ≥ 80% das linhas | ~100% | ✔ |
| (c) empreendimentos não concluídos com módulos ou equipamentos | ≥ 10 | 652 com módulo de equipamento | ✔ |

**Decisão: seguir com o SIGET.** Os leilões entram depois, como sinal antecipado, para os lotes ainda não assinados.

## 4. Amostra para avaliação manual

Regra (`aneel_siget.amostra`, reproduzível): empreendimentos **em andamento**, com data de operação do ato legal **no futuro** e pelo menos um
**módulo de equipamento ligado a obra em andamento**; 10 autorizações e 10 contratos, os mais documentados primeiro (mais equipamentos, depois mais módulos de manobra).
O arquivo completo, com descrição, equipamentos, linhas e link do ato, está em `data/fontes/aneel/sistema-de-gestao-da-transmissao-siget/amostra.csv`,
com duas colunas vazias para a avaliação.

| # | Id ONS | Empreendimento | Concessionária | UF | Operação (ato legal) | Origem | Equip. | Ato |
|---|---|---|---|---|---|---|---|---|
| 1 | T2023-001 | Revitalização completa das instalações do Bipolo 1 associada a UHE Itaipu | AXIA | PR,SP | 02/02/2027 | autorização | 8 | REA-2022-11324 |
| 2 | T2024-007 | SE CAMPO BOM: Substituição do TR3 e obras associadas | CPFL Transmissão | RS | 10/02/2028 | autorização | 5 | REA-2025-15838 |
| 3 | T2022-115 | SE São José dos Campos - Substituição de três bancos de transformadores 230/88 kV monofásicos | ISA ENERGIA BRASIL | SP | 31/03/2028 | autorização | 4 | REA-2023-13514 |
| 4 | T2023-161 | Reforço na SE Irecê: Substituição do TR2 e TR3 230/69 kV - 33 MVA por dois TRs de 100 MVA | AXIA Nordeste | BA | 30/12/2027 | autorização | 2 | REA-2023-14970 |
| 5 | T2025-035 | Reforço na SE Várzea Grande 2: instalação do 3º transformador 230/138 kV - 3x50 MVA  | ETVG | MT | 22/10/2027 | autorização | 2 | REA-2025-16079 |
| 6 | T2023-078 | Reforço na SE Canoas 1: substituição do TR1 e TR2, 230/23 kV, de 50 MVA por 75 MVA | CPFL Transmissão | RS | 29/02/2028 | autorização | 2 | REA-2023-14718 |
| 7 | T2023-134 | Reforço na SE Presidente Dutra: substituição do TR1 500/230 kV, (3+1)x100 MVA, por (3+1)x150 MVA. | AXIA Norte | MA | 15/11/2026 | autorização | 2 | REA-2023-14869 |
| 8 | T2023-190 | Reforço na SE Vitória: Substituição do ATR1 345/138 kV por novo banco (3+1)x133,33MVA.  | AXIA | ES | 26/03/2027 | autorização | 2 | REA-2024-14990 |
| 9 | T2026-243 | Reforço na SE Rio Verde Furnas 4° ATF 230/138/13,8 kV, (3+1R) x 75 MVA (225 MVA) | AXIA | GO | 04/03/2029 | autorização | 2 | REA-2026-16762 |
| 10 | T2021-075 | SE Poços de Caldas - Instalação do novo transformador 500/345 kV em paralelo com o ATR51 | AXIA | MG | 04/12/2027 | autorização | 2 | REA-2021-10505 |
| 11 | T2024-146-A | LT ±800 kVCC Graça Aranha – Silvânia e Bipolos | AXIA Nordeste | GO,MA,PI | 30/03/2028 | contrato | 20 | – |
| 12 | T2024-198-C | LT 500 kV Jussiape–São João do Paraíso–Capelinha 3–Itabira 5 e SE 500 kV São João do Paraíso | GSII | BA,MG | 31/05/2027 | contrato | 19 | – |
| 13 | T2024-197-A | LT 500 kV Bom Nome II–Zebu III–Olindina, SE 500/230/138 kV Bom Nome II e SE 500/230 kV Zebu III | Nova Era Integração | AL,BA,PE | 30/12/2029 | contrato | 17 | – |
| 14 | T2024-193-A | LT 500 kV Quixadá-Crateús-Teresina, SE 500 kV Teresina IV, SE 500 kV Crateús e Compensação Síncrona | STN | CE,PI | 30/06/2029 | contrato | 15 | – |
| 15 | T2023-174-A | LT 500 kV Buritirama-Barra II-Correntina-Arinos 2, SE 500 kV Barra II e SE 500 kV Correntina | TAESA | BA,MG | 28/02/2027 | contrato | 15 | – |
| 16 | T2023-178 | LT 500 kV Governador Valadares 6 - Leopoldina 2 - Terminal Rio e SE 500 kV Leopoldina 2 | ISA ENERGIA BRASIL | MG,RJ | 24/09/2028 | contrato | 15 | – |
| 17 | T2022-120-A | LTs 500 kV Pirapora 2 - Buritizeiro 3 - S.Gotardo 2 e Buritizeiro 3 - S.G.do Pará e SE Buritizeiro 3 | CEMIG-GT | MG | 19/12/2026 | contrato | 12 | – |
| 18 | T2025-010-A | LT 525 kV Curitiba Oeste – Abdon Batista 2 - Abdon Batista, SE Curitiba Oeste e SE Abdon Batista 2 | GRALHA AZUL | PR,SC | 30/11/2027 | contrato | 10 | – |
| 19 | T2024-199 | LT 230 kV Dianópolis II -Formosa do Rio Preto-Gilbués II e SE 230/138 kV Formosa do Rio Preto | EDP NORTE NORDESTE 1 | BA,PI,TO | 30/04/2028 | contrato | 10 | – |
| 20 | T2026-229-B | SEs Cachimbo e Novo progresso e LTs Claudia/Cachimbo e Cachimbo/Novo Progresso | CASTANHEIRA | MT,PA | 26/06/2031 | contrato | 9 | – |

Datas: operação comercial fixada pelo ato legal, não previsão da transmissora. "Equip." = módulos de equipamento ligados a obras em andamento.

## 5. Critério de relevância (para a avaliação humana, definido antes dela)

Perfil de demonstração: **fornecedor de equipamentos de subestação de alta tensão** (transformadores de potência, reatores, bancos de capacitores e equipamentos de manobra).
Um empreendimento é **relevante (s)** se as três condições valerem:
1. a fonte (campo estruturado ou texto da descrição) indica **fornecimento novo ou substituição** de pelo menos um equipamento do perfil, e não só adequação de proteção ou de obra civil;
2. a data de operação do ato legal está a **mais de 6 meses** da data da avaliação (ainda há janela de compra);
3. a concessionária está identificada.

Marque **n** se alguma condição falhar e **?** se a fonte não permitir decidir. A precisão é a fração de **s** entre os que não são **?**.
Quem avalia é você (Lucas), não o classificador. A meta experimental do plano mestre é de 80%.

## 6. Próximos passos

1. **Avaliação manual da amostra** (cerca de 1 h): preencher `avaliacao_relevante` e `avaliacao_nota` no `amostra.csv`.
2. **Segunda coleta** daqui a 1–2 semanas, para medir a frequência real de mudança e testar a detecção de mudanças (estágio, datas, obras novas).
3. **Fase 2**: transformar o leitor em coletor com histórico (vintages por arquivo, eventos por empreendimento), reaproveitando `storage.py`.
4. **Leilões**: localizar o resultado oficial do Leilão 4/2026 e ver se ele traz o `IdeOnsEpd` ou um código que ligue ao SIGET depois da assinatura.
5. **Publicação**: a ODbL permite republicar com atribuição e mantendo a mesma licença na base derivada. Antes de colocar projetos no site público, registrar a atribuição na página e no catálogo.

## Fontes

- Conjunto SIGET no Portal de Dados Abertos da ANEEL: https://dadosabertos.aneel.gov.br/dataset/sistema-de-gestao-da-transmissao-siget
- Dicionários de dados (PDF) baixados do mesmo conjunto; ex.: `dm-siget-contrato-empreendimento-obra-modulo.pdf`
- Licença: Open Data Commons Open Database License (ODbL), declarada no portal

## 7. Avaliação 1 (04/11/2026)

- **Avaliador:** Lucas. **Resultado declarado:** os 20 empreendimentos foram considerados relevantes.
- **Conferência contra o critério escrito (§5):** 5 dos 20 não atendem à condição 2, porque operam em menos de 6 meses pelo ato legal:
  T2023-134 (15/11/2026, 11 dias), T2022-120-A (19/12/2026), T2023-001 (02/02/2027), T2023-174-A (28/02/2027) e T2023-190 (26/03/2027).
  **Pelo critério, a precisão seria de 15/20 = 75%, abaixo da meta de 80%.**
- **Por que o número não generaliza:** a amostra pegou os casos mais documentados (viés de seleção), e o avaliador é quem construiu o produto, não o comprador.
- **Aprendizados para as regras:**
  1. O tipo de obra "Adequação" esconde substituições com equipamento novo: 5 casos da amostra só têm módulos em "Adequação", mas a descrição diz "substituição do TR… por novo de 100 MVA". A regra precisa ler a descrição (`DscEpd`/`DscObr`), não só o tipo da obra.
  2. A janela de 6 meses provavelmente é curta para transformadores de potência, que têm prazo de fabricação longo: a janela deve variar por categoria de equipamento. Isso é hipótese a validar com compradores.
- **Próximo:** uma amostra **aleatória** (semente fixa) dos 632 elegíveis, para estimar a precisão sem viés, e os 20 casos atuais como material de demonstração nas conversas.

## 8. Amostra aleatória (avaliação 2)

```bash
.venv/bin/python -m rotzx siget-amostra --aleatoria   # semente 20261104, exclui os 20 da amostra anterior
```

Sorteio simples de 20 entre os **612 elegíveis** (mesma regra de elegibilidade, sem os 20 já avaliados), para estimar a precisão sem o viés da primeira amostra.
Resultado do sorteio: 17 autorizações e 3 contratos, próximo da proporção da população. Em 3 casos a operação está a menos de 6 meses (C2 = n).
A planilha `amostra-aleatoria-avaliacao.xlsx` traz C2 (janela) e C3 (concessionária) calculadas; a pessoa julga só C1 (equipamento novo do perfil),
e o resultado e a precisão saem por fórmula (conferidas no LibreOffice).

### Resultado (04/11/2026, avaliador: Lucas)

| | Casos |
|---|---|
| s | **16** |
| n | 4 (3 por C2, a janela: T2024-097, T2024-002, T2023-153; 1 por C1: T2025-019, "revitalização do transformador conversor") |
| ? | 0 |
| **Precisão = s / (s + n)** | **16/20 = 80%**, intervalo de 95% (Wilson) de **58% a 92%** |

- **Leitura honesta:** a estimativa pontual bate na meta de 80%, mas com 20 casos o intervalo é largo. O resultado é compatível com uma precisão real de 60% ou de 90%. **A meta ainda não foi demonstrada.** Para um intervalo de ±10 pontos seriam precisos ~60 casos.
- **Onde a regra errou:** 3 dos 4 "n" são mecânicos (a operação está perto demais) e só 1 dependeu de julgamento. Só na condição de equipamento (C1), foram 19/20 (IC 76% a 99%).
- **Nenhum "?":** as descrições das autorizações são explícitas o bastante para decidir. É um bom sinal sobre a qualidade da fonte.
- **O avaliador continua sendo quem construiu o produto.** Isso mede se as regras leem a fonte direito, não se o comprador acha o caso útil. Isso só as conversas respondem.

### Regras que saem das duas avaliações (para a Fase 3)

São hipóteses tiradas de 40 casos. Vão ser testadas numa amostra **nova**, nunca nesta mesma (senão o ajuste vira sobreajuste).

1. **A janela entra na elegibilidade.** Empreendimento com operação pelo ato legal a menos de *J* meses não aparece como oportunidade do equipamento principal. Nesta amostra, isso teria dado 16/17. *J* deve variar por categoria (prazo de fabricação), e o valor de cada categoria sai das conversas com compradores.
2. **O texto manda, não o tipo de obra.** "Substituição… por", "instalação do Nº", "novo banco" e "nova unidade" na descrição contam como fornecimento novo, mesmo com a obra marcada como "Adequação" (5 casos na avaliação 1).
3. **"Revitalização" sem verbo de troca ou instalação** não conta como equipamento novo (T2025-019).

**Dados rotulados:** `avaliacoes/siget_relevancia.csv` (40 casos, as duas avaliações) guarda C1, C2, C3 e o resultado por `id_aneel`/`id_ons`.
Serve de conjunto de teste para as regras da Fase 3. Contém identificadores derivados de dados da ANEEL (SIGET), sob a licença ODbL.
