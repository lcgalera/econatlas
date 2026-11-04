# rotzx — Validação de fonte: ANEEL SIGET e resultados de leilões (Fase 1)

Data: 04/11/2026. Situação: **validação bloqueada por acesso de rede; nada foi baixado.**

## 1. O que aconteceu

Neste ambiente de desenvolvimento (nuvem), o proxy de rede recusa `dadosabertos.aneel.gov.br`, tanto por `curl` quanto por busca de página.
As APIs do BCB e do IBGE também estão bloqueadas aqui. Não houve falha da fonte: é a política de rede do ambiente.

Por isso este documento **não traz exemplos reais nem contagens**. Tudo o que está na seção 2 vem de resultados de busca
na web, que apontam para páginas do próprio portal, e precisa ser confirmado na fonte antes de qualquer uso.

Duas formas de destravar:
- **Liberar o domínio** `dadosabertos.aneel.gov.br` (e `www.gov.br`, para as páginas de leilões) nas configurações de rede do ambiente.
- **Rodar no Mac**, onde a rede é livre:

```bash
.venv/bin/python -m econatlas fonte-explorar siget
.venv/bin/python -m econatlas fonte-explorar x --conjunto sistema-de-gestao-da-transmissao-siget
```

O primeiro comando lista os conjuntos e recursos que casam com "siget", com licença declarada. O segundo baixa os recursos
tabulares (CSV, ZIP, Excel, JSON) para `data/fontes/aneel/<conjunto>/brutos/`, com SHA-256, e escreve
`data/fontes/aneel/<conjunto>/relatorio.md` com, para cada tabela, o preenchimento de cada coluna, os valores distintos, as colunas que parecem chave e as
colunas com o mesmo nome em tabelas diferentes, junto com a sobreposição de valores. Esses são os candidatos a identificador de ligação.
`data/` está fora do git, então nada vai para o repositório nem para o Pages.

## 2. O que a busca indica (a confirmar no portal)

Segundo resultados de busca que apontam para páginas do portal da ANEEL:

- O conjunto se chama **Sistema de Gestão da Transmissão – SIGET** e fica em
  `https://dadosabertos.aneel.gov.br/dataset/sistema-de-gestao-da-transmissao-siget`.
- Recursos citados: *Resolução Empreendimento Obra Módulo* (CSV), *Contrato Módulo Equipamento Subestação* (CSV),
  *Resolução Módulo Linha Transmissão*, *Contrato*, *Novas Instalações em Operação Comercial* e *Obras Concluídas sem Termo de …*.
  Vários vêm com dicionário de dados em PDF.
- Campos citados para *Resolução Empreendimento Obra Módulo*: `IdeEpd`, `IdeOnsEpd`, `NomEpd`, `DscEpd`, `DscSituacaoEpd`
  e `DatGeracaoConjuntoDados`.
- Um recurso de **equipamento por módulo de subestação, ligado a contrato** é exatamente o que tornaria a hipótese do MVP testável
  ("este empreendimento tem módulo X com equipamento Y").
- Uma apresentação da ANEEL de 2022 fala em atualização mensal dos conjuntos abertos, sem confirmar que isso vale para o SIGET.

Nada disso foi verificado. Os nomes dos campos podem estar incompletos ou desatualizados.

**Leilões de transmissão:** a busca só devolveu notícias sobre o Leilão de Transmissão nº 4/2026 (30/10/2026, oito lotes), com
valores divergentes entre os veículos. Notícia não é fonte do produto. O próximo passo é localizar o resultado oficial
(edital, ata ou planilha de resultado da ANEEL) e verificar se ele traz identificador que ligue o lote ao contrato de concessão no SIGET.
Esse leilão recente é um bom caso de teste: os empreendimentos dele estão no começo do ciclo, que é onde um fornecedor ganha com antecedência.

## 3. Perguntas que o perfil real precisa responder

Cada pergunta é decisiva para o MVP. A resposta vai para este documento, com o recurso e a coluna de onde saiu.

| # | Pergunta | Por que importa | Como responder com o relatório |
|---|---|---|---|
| 1 | Quais recursos existem, em que formato e com que licença? | Sem licença que permita republicar, os projetos ficam só no modo local | Cabeçalho e tabela "Arquivos" |
| 2 | Qual é a chave de empreendimento, obra, módulo e contrato? Elas ligam as tabelas? | Sem chave estável não há histórico nem deduplicação | "Parece chave" + "candidatas a ligação" com sobreposição perto de 100% |
| 3 | Há equipamento descrito por módulo (tipo, tensão, quantidade)? | É a diferença entre "confirmado na fonte" e "inferência" | Colunas da tabela de equipamentos e seus valores mais comuns |
| 4 | Há situação ou estágio do empreendimento? Com quais categorias? | Define o estágio acionável do score | Valores distintos de `DscSituacaoEpd` ou equivalente |
| 5 | Há datas previstas (energização, operação comercial) e datas de alteração? | Antecipação é o produto; data prevista distante = janela de venda | Preenchimento das colunas de data |
| 6 | Há a concessionária responsável, com CNPJ? | Comprador potencial, sem confundir com construtora | Colunas de agente e contrato |
| 7 | Há UF e município? | Filtro geográfico do score | Preenchimento das colunas de localização |
| 8 | Com que frequência o arquivo muda? | Define a rotina de coleta e a detecção de mudanças | Duas coletas separadas por semanas: comparar SHA-256 e linhas |
| 9 | Qual a fração de empreendimentos ainda não concluídos? | Se quase tudo já está em operação, o radar tem pouco a oferecer | Contagem por situação |

## 4. Critério de decisão (antes de olhar os dados)

Fixado agora, para não ajustar o critério ao resultado:

- **Seguir com o SIGET** se houver (a) chave estável de empreendimento ligando pelo menos duas tabelas com sobreposição ≥ 90%,
  (b) situação ou estágio preenchido em ≥ 80% das linhas, e (c) pelo menos 10 empreendimentos não concluídos com módulos ou equipamentos descritos.
- **Combinar com leilões** se (a) e (b) valerem mas os empreendimentos novos só aparecerem no SIGET depois da assinatura do contrato.
- **Trocar de fonte** se (a) ou (b) falharem. Alternativas, em ordem: resultados oficiais de leilão + editais (lote, vencedora, UF, prazos);
  planos da EPE (PET/PELP) para obras planejadas; PNCP só para compras públicas, sabendo que concessionárias privadas não compram por ele.

## 5. Licença e uso

O portal declara a licença por conjunto; o relatório registra o que estiver declarado. **Acesso público não equivale a permissão de
redistribuição.** Até a licença do SIGET estar registrada no catálogo, nenhum dado da ANEEL entra no build público.

## 6. Fontes consultadas nesta etapa (só busca; páginas não abertas)

- Portal de Dados Abertos da ANEEL, conjunto SIGET: https://dadosabertos.aneel.gov.br/dataset/sistema-de-gestao-da-transmissao-siget
- Recurso "SIGET – Resolução Empreendimento Obra Módulo.csv": https://dadosabertos.aneel.gov.br/pt_BR/dataset/sistema-de-gestao-da-transmissao-siget/resource/1c345514-893d-44a1-8e7e-a9362137c356
- Recurso "SIGET – Contrato Módulo Equipamento Subestação.csv": https://dadosabertos.aneel.gov.br/pt_BR/dataset/sistema-de-gestao-da-transmissao-siget/resource/caec5e88-c904-45e5-bde4-d7e96ef139b6
- Recurso "SIGET – Novas Instalações em Operação Comercial": https://dadosabertos.aneel.gov.br/dataset/sistema-de-gestao-da-transmissao-siget/resource/dfbf44f7-9fb5-48cb-828d-13c7cbe43067
- Notícia sobre o Leilão de Transmissão 4/2026 (não é fonte oficial): https://canalsolar.com.br/leilao-de-transmissao-axia-alupar-vencedores/
