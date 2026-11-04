# rotzx — Leilões de transmissão: o sinal mais cedo do radar

Data: 04/11/2026. Código: `rotzx/providers/aneel_leiloes.py`, `rotzx/intelligence/leiloes.py`. Ligações: `catalog/leiloes_contratos.json`.

```bash
.venv/bin/python -m rotzx leiloes-importar Resultado_leiloes_transmissao.xlsx   # depois de cada leilão
.venv/bin/python -m rotzx oportunidades                                         # o relatório ganha a seção de leilões
```

## Fontes

| Fonte | Cobertura | Acesso |
|---|---|---|
| Planilha `Resultado_leiloes_transmissao.xlsx` (gov.br/aneel › Centrais de Conteúdos › Relatórios e Indicadores › Leilões) | 1999 até o **Leilão 04/2026 (30/10/2026)** | o servidor (`git.aneel.gov.br`) exige um desafio anti-robô: **baixar à mão** pelo navegador e importar |
| Conjunto "Resultado de leilões" do Portal de Dados Abertos (ODbL) | 1999 até o Leilão 02/2024 (27/09/2024), apesar de gerado em 01/11/2026 | API, mas desatualizado |
| Sistema de leilões (`leilao.aneel.gov.br`) | editais e sessões | fecha a conexão a partir deste ambiente de nuvem |

Não contornamos o desafio anti-robô: o plano proíbe automatizar o acesso que o dono do site barra.

## Leitura da planilha

A planilha é um relatório para leitura humana. Ela tem três formatos de cabeçalho ("CONCORRÊNCIA 007/1999 (03/12/1999)",
"LEILÃO Nº 002/2000 (31/08/2000)" e "LEILÃO nº 01/2026 - 27/03/2026"), linhas de TOTAL, lotes "NÃO LEILOADO" e deságio às
vezes em % e às vezes em fração. O leitor gera uma linha por lote (`historico/leiloes_transmissao.csv`), com a linha de origem.

- 522 lotes de 62 leilões; 457 arrematados e 65 não leiloados. O Leilão 07/2012 não tem data no cabeçalho, e ela fica em branco (61 leilões com data).
- **Deságio recalculado** das receitas: bate com a coluna da fonte em 445 de 445 lotes.
- **Conferência contra o portal** (2015–2024): a receita vencedora é igual em 156 dos 158 lotes que casaram. Divergem dois lotes do
  Leilão 01/2023 (lote 1: R$ 283,8 mi no portal e R$ 174,1 mi na planilha; lote 8: R$ 19,60 mi e R$ 19,54 mi). As duas fontes são da ANEEL;
  o radar usa a planilha. Outros 81 lotes antigos não casaram porque as fontes rotulam os lotes de forma diferente (letra × número).
- Defeitos da fonte mantidos como estão: descrição vazia nos lotes do 01/2026; "41310 km" na descrição do lote 4 do 04/2026 (a coluna de
  extensão diz 620 km); texto residual ("C625") no lote 5.

## Lote → contrato do SIGET

A planilha não traz contrato nem código do ONS. Por isso a ligação foi **conferida à mão** contra o SIGET (nome do empreendimento,
UF, vencedor e data de assinatura) e registrada em `catalog/leiloes_contratos.json`, com a evidência de cada uma:

| Leilão | Lotes | Ligação | Assinatura | Dias depois |
|---|---|---|---|---|
| 04/2025 (31/10/2025) | 9 | 9 conferidos (`001/2026` a `009/2026`) | 23/02/2026 | 115 |
| 01/2026, 1ª etapa (27/03/2026) | 8 | 2 conferidos, 4 prováveis, **2 ambíguos** (lotes 1 e 2, SP) | 26/06/2026 | 91 |
| 01/2026, 2ª etapa (03/07/2026) | 4 | 4 prováveis (vencedor e UF; empreendimentos ainda sem cadastro) | 09–10/09/2026 | 68 |
| 04/2026 (30/10/2026) | 8 | **nenhum contrato ainda** | – | – |

Isso explica o "nenhum contrato assinado em 2025" (D34): os lotes do leilão de outubro de 2025 viraram contrato em fevereiro de 2026.
Os prazos são medidos pelo código a partir do mapa (`prazos_observados`), não escritos à mão no relatório.

## O que entra no relatório

**Leilões arrematados, contrato ainda não assinado:** lotes arrematados nos últimos 24 meses sem contrato identificado (ou com ligação
ambígua), com a descrição oficial, a UF, o vencedor, a receita anual, o prazo do edital e a operação **estimada** (data do leilão + prazo).

Categorias por lote (regra **R6**, descrição do lote licitado):
- termo da categoria no texto, ou transformação "kV … MVA" → **confirmado** (o lote licita instalação nova);
- subestação no lote → para-raios e transformadores de instrumento por **inferência**; linha → materiais de linha por **inferência**;
- lote de **continuidade** da prestação do serviço (instalações existentes) → **não verificado**. Em lote misto, só o trecho depois de
  "Novas instalações" confirma.

Em 04/11/2026: 10 lotes (os 8 do 04/2026 e os 2 ambíguos do 01/2026). Os do 04/2026 incluem transformação em seis lotes (por exemplo,
"SE 500/345 kV Santana - (9+1Res) x 400 MVA") e compensação síncrona em um.

## Limites

- Lote não é pedido de compra: o vencedor ainda escolhe EPCista e fornecedores, e parte do equipamento pode já estar contratada.
- A operação estimada não considera atrasos; a data oficial vem no contrato e depois no SIGET.
- A planilha precisa ser importada à mão depois de cada leilão (são uns 2 a 4 por ano).
- A licença da planilha não é declarada na página; o mesmo conteúdo está no conjunto do portal sob ODbL, e a atribuição acompanha o CSV derivado.
