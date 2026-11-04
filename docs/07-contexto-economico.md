# rotzx — Contexto econômico do radar (Fase 5)

Data: 04/11/2026. Código: `econatlas/intelligence/contexto.py`. Configuração: `catalog/contexto_radar.json` (`contexto_v1`).

```bash
.venv/bin/python -m econatlas contexto-atualizar   # só as séries públicas usadas no contexto
.venv/bin/python -m econatlas oportunidades        # o relatório ganha a seção "Contexto de mercado"
```

## Princípios

1. **O contexto não entra no score nem filtra oportunidades.** As associações entre indicadores macro e compras específicas de equipamento
   não foram medidas; usá-las para ordenar a lista seria uma associação frágil (plano, Fase 5).
2. **Cada indicador traz o canal possível com o mercado do radar e o que ele não permite concluir.** Os dois textos foram escritos na configuração
   antes de olhar os valores.
3. **As frases são descritivas:** valor, data e comparação com 12 meses antes, com sinal. Não há "portanto", "vai" nem "causa" (há teste para isso).
4. **Só séries públicas do catálogo.** Série de uso pessoal (Macrodados) nunca entra, nem por engano de configuração (há teste).

## O que a seção mostra

**A expansão que o radar acompanha (do próprio SIGET):** empreendimentos em andamento por ano de operação (ato legal), atos autorizativos
publicados por ano (reforços e melhorias) e contratos de concessão assinados por ano. São contagens, não valores. Anos sem registro aparecem como 0.

**Indicadores econômicos** (BCB e IBGE, com código e data de coleta):

| Grupo | Indicador | Métrica |
|---|---|---|
| Custo e oferta de capital | Meta Selic; juros médios do crédito PJ | nível e diferença em 12 meses (p.p.) |
| | Concessões de crédito PJ | soma de 12 meses, real (IPCA), contra os 12 anteriores |
| | Saldo do crédito PJ | real, contra 12 meses antes |
| Custos e reajustes | Dólar | nível e variação em 12 meses |
| | IPCA em 12 meses | nível e diferença em 12 meses: a RAP de 370 dos 411 contratos de transmissão é reajustada pelo IPCA e a de 41 pelo IGP-M (SIGET, campo `SigIndice`) |
| Atividade da indústria fornecedora | Produção CNAE 27, máquinas (CNAE 28), IBC-Br | média de 12 meses contra os 12 anteriores |

**Previsão registrada da indústria CNAE 27:** a última linha do registro público (`setorial_v1`), com a margem de 80% e o aviso de que ela quase
não informa a direção.

## Leitura em 04/11/2026 (dados reais)

- Meta Selic de 13,75% a.a. (11/2026), 1,25 p.p. abaixo de 12 meses antes; juros médios PJ de 19,36% a.a. (09/2026), 1,19 p.p. abaixo.
- Concessões de crédito PJ: +7,2% reais na soma de 12 meses; saldo PJ: +1,9% real.
- Dólar a R$ 5,13 (10/2026), −4,8% em 12 meses; IPCA de 4,58% em 12 meses (09/2026).
- Produção da CNAE 27: −1,0% na média de 12 meses (até 08/2026); máquinas (CNAE 28): −4,8%; IBC-Br: +1,4%.
- SIGET: 220 empreendimentos em andamento com operação prevista pelo ato legal para 2027, 166 para 2028 e 177 para 2029. 72 atos autorizativos em 2026 (até 04/11).
  **Nenhum contrato de concessão foi assinado em 2025** segundo a fonte (0 de 413; a numeração pula de `/2024` para `/2026`). Os nove contratos
  de 23/02/2026 podem ser do leilão anterior, mas isso **não foi verificado**.

Essas frases descrevem; não recomendam nem preveem nada.

## Limites

- Os indicadores são nacionais e de todos os setores. Nenhum mede o investimento em transmissão nem as compras das concessionárias.
- A defasagem dos dados é a de cada fonte (produção industrial até 08/2026, crédito até 09/2026). A data aparece em cada linha.
- O canal "câmbio → custo do equipamento" é descrito, mas a fração importada de cada equipamento não é medida.
