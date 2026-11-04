# rotzx — Motor de oportunidades (Fase 3)

Data: 04/11/2026. Código: `econatlas/intelligence/` (`evidencia.py`, `scoring.py`, `relatorio.py`).
Catálogo: `catalog/product_categories.json` (versão `categorias_v1`). Perfil de demonstração: `catalog/perfil_demo.json`.

```bash
.venv/bin/python -m econatlas fonte-explorar x --conjunto sistema-de-gestao-da-transmissao-siget   # baixa o SIGET (uma vez por coleta)
.venv/bin/python -m econatlas oportunidades [--perfil arquivo.json] [--top 30]                    # relatório HTML + CSV
```

Saída em `data/relatorios/<perfil>_<data>/` (fora do git): `relatorio.html` (abre no navegador e imprime em PDF), `oportunidades.csv`
(uma linha por oportunidade, com o score e a explicação) e `evidencias.csv` (cada evidência, com a regra que a gerou).

## 1. Categorias de produto

Onze categorias, cada uma com a origem possível da evidência no SIGET:

| Categoria | Campo estruturado | Texto | Inferência |
|---|---|---|---|
| Transformadores de potência | tipo de equipamento do módulo | TR, ATR, ATF, TF, TRR, transformador, trafo | – |
| Transformadores de aterramento | tipo de equipamento | "transformador de aterramento" | – |
| Reatores | reator de linha, barra, série e neutro | reator, RT, RTB, RTL, RTR | – |
| Bancos de capacitores | banco de capacitores, capacitor série | capacitor, BC | – |
| Compensadores | síncrono, estático | compensador, CS, CER | – |
| Equipamentos HVDC | conversora, banco de filtros | conversora, filtro, kVcc | – |
| Disjuntores | quantidade no módulo de manobra | disjuntor (exceto "disjuntor e meio", que é arranjo) | módulo de manobra novo sem quantidade |
| Chaves seccionadoras | quantidade no módulo de manobra | seccionadora | módulo de manobra novo sem quantidade |
| Para-raios | – | para-raios | bay novo |
| Transformadores de instrumento | – | TC, TP, TPC, "transformador de corrente/potencial" | bay novo |
| Materiais de linha | – | recondutoramento, cabo, isolador, torre | linha nova |

## 2. Regras de evidência

Só **obras em andamento** geram evidência.

| Regra | O que verifica | Nível |
|---|---|---|
| R1 | Módulo de equipamento ligado a obra de **instalação ou ampliação** | confirmado (campo) |
| R1 | Módulo de equipamento ligado a obra de adequação, recapacitação ou reconstrução | não verificado: o módulo existe, mas a fonte não diz se há equipamento novo |
| R2 | Texto (nome, descrição, obra): **verbo de fornecimento** ("substituição", "subst.", "troca", "instalação", "novo", "ampliação", "recondutoramento"…) seguido do termo da categoria em até 120 caracteres | confirmado (texto) |
| R3 | Módulo de manobra novo com quantidade de disjuntores ou seccionadoras declarada (> 0) | confirmado (campo) |
| R3 | Módulo de manobra novo sem quantidade declarada | inferência técnica |
| R4 | Bay novo (módulo de equipamento ou de manobra) → para-raios e transformadores de instrumento | inferência técnica |
| R5 | Linha nova → materiais de linha | inferência técnica |

Cada evidência guarda a regra, o trecho ou campo que a sustenta e a tensão (kV), quando a fonte a declara.
"Revitalização" ou "reforma" sem verbo de fornecimento não confirmam nada (avaliação 2, T2025-019).

## 3. Elegibilidade e score

**Elegível** = situação "Em andamento" + concessionária identificada + evidência (confirmada ou inferida) para uma categoria do perfil + operação
pelo ato legal a pelo menos `janela_meses` da categoria (6 meses em todas, **hipótese** a validar por categoria com compradores) + tensão declarada ≥
`tensao_min_kv` do perfil, quando o perfil a define.

**Score (0–100)** = 100 × (0,40 · compatibilidade + 0,25 · estágio + 0,20 · evidência + 0,15 · geografia). Os pesos ficam no perfil.

| Componente | Regra |
|---|---|
| Compatibilidade | 1,0 se categoria do perfil confirmada com tensão declarada; 0,85 se confirmada sem tensão; 0,5 se só inferida |
| Estágio | 0,5 na janela, subindo até 1,0 seis meses depois (perto da janela, a compra pode já ter sido feita); 1,0 até a janela + 30 meses; 0,7 depois disso (acompanhar). **Máximo de 0,5** se a descrição indica pendência ("aguardar", "em estudo", "suspens…", "cancelad…", "paralisad…", "revog…") |
| Evidência | 1,0 se confirmada por campo **e** texto; 0,8 por um dos dois; 0,4 só inferência. Metade se o arquivo da fonte tiver mais de 30 dias |
| Geografia | 1,0 se o perfil não restringe UF ou se alguma UF das subestações está no perfil; 0,5 se a UF é desconhecida; 0 fora |

Só inferência: **teto de 60**. O score é reproduzível (mesma entrada, mesma saída), aparece explicado em cada oportunidade e **não é probabilidade de venda**.
O nível de evidência ("confirmado" ou "inferência técnica") é mostrado à parte e não se mistura com o score.

## 4. Resultado com os dados de 04/11/2026 (perfil de demonstração)

- **524 oportunidades** de 80 concessionárias: 502 com categoria confirmada e 22 só por inferência. 441 são autorizações e 83 vêm de contrato de concessão.
- Mais frequentes: transformadores de potência (324 empreendimentos), reatores (129), bancos de capacitores (54), disjuntores (52, depois de excluir "disjuntor e meio").
- 5 oportunidades têm pendência na descrição e aparecem com alerta e estágio reduzido.
- **Limite do score:** com um perfil Brasil inteiro e uma fonte só, a maior parte das oportunidades confirmadas é parecida de verdade.
  Metade fica entre 90 e 96 pontos. O score separa bem o confirmado do inferido e o que está perto demais da janela, mas não ordena com precisão
  os casos bons entre si. Ordenação mais fina exige informação que a fonte não tem (relação com o comprador, porte da compra, previsão
  da transmissora), ou um perfil de cliente mais restrito (UF, tensão, categorias).

## 5. Verificação

- **Testes** (`tests/test_intelligence.py`, fixtures sintéticas): texto com e sem verbo de fornecimento, "disjuntor e meio", "transformador de corrente"
  como transformador de instrumento, níveis por regra, janela, teto de inferência, pendência, filtros de UF e de tensão, atualidade e o conteúdo
  obrigatório do relatório (atribuição ODbL, "não é pedido de compra").
- **Contra as 40 avaliações humanas** (`avaliacoes/siget_relevancia.csv`): a regra de equipamento concorda em 39/40 casos. A divergência é T2023-001
  (revitalização do Bipolo 1), marcada como relevante na avaliação 1, que foi global e sem critério por caso. A regra segue o "julgue pelo que está escrito".
  No resultado final (com janela e concessionária), concorda em 40/40.
- **Atenção:** essas 40 avaliações inspiraram as regras. A concordância mede coerência, **não precisão fora da amostra**. A próxima medida honesta é
  uma **amostra nova** (outra semente) avaliada sem olhar o que o motor diz, de preferência por um comprador.
- **Bugs encontrados pelos testes antes do commit:** a expressão de "transformador" aceitava "transformador**es** de corrente"; a inferência de bay não
  levava a tensão e passava pelo filtro de tensão mínima.

## 6. O que ainda não existe

- Janela por categoria baseada em prazo real de fabricação (hoje, 6 meses para todas).
- Detecção de mudanças entre coletas (estágio, datas, obras novas): precisa do histórico da Fase 2.
- Leilões ainda não assinados.
- Previsão da transmissora (Relatório de Monitoramento mensal).
- Interface de oportunidades no site: fica para depois dos pilotos (D29).
