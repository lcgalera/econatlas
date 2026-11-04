# rotzx — Kit de validação com compradores (Fase 6, antecipada)

Objetivo: descobrir, com 5 conversas de cerca de 30 minutos, se existe uma dor que alguém pague para resolver, **antes** de construir a interface.
Nenhuma entrevista foi feita até agora. Este documento é só o roteiro: resultados reais entram em `privado/validacao/` (fora do git),
porque envolvem pessoas e empresas identificadas.

## 1. Quem procurar (perfil ideal, a testar)

Por ordem de prioridade:
1. **Representante comercial ou gerente comercial** de fabricante **médio** de equipamentos para subestação ou linha
   (para-raios, isoladores, seccionadoras, transformadores de instrumento, ferragens, cabos, estruturas).
2. **Distribuidor técnico** de materiais elétricos industriais que atende EPCistas de transmissão ou distribuição.
3. **Responsável por desenvolvimento de negócios** em empresa de engenharia ou montagem eletromecânica.
4. Uma conversa de **controle** com alguém de grande fabricante: serve para confirmar ou derrubar a hipótese de que eles não precisam do produto.

Como chegar: LinkedIn (cargo + "subestação", "transmissão", "materiais elétricos"), associações e feiras do setor e a sua própria rede.
Pedido de conversa: "Estou pesquisando como fornecedores acompanham obras de transmissão. Não vou vender nada; 30 minutos para entender como vocês fazem hoje."

## 2. Roteiro (perguntar sobre o passado, não pedir opinião sobre o futuro)

**Contexto (5 min)**
1. O que vocês vendem e para quem? Quem é o cliente final: transmissora, EPCista, distribuidora?
2. Como chega uma oportunidade nova até você hoje?

**Dor (15 min)**
3. Conte a última vez que vocês souberam de um projeto tarde demais. O que aconteceu? Quanto isso custou?
4. Quem na empresa acompanha leilões, obras e cronogramas? Quantas horas por semana?
5. Que fontes vocês usam? (ANEEL, imprensa, plataforma paga, contatos, cadastro de fornecedor)
6. Vocês pagam por alguma fonte de informação de mercado hoje? Quanto? Quem aprovou?
7. O que vocês gostariam de saber sobre um empreendimento e não conseguem descobrir?

**Teste do conceito (8 min)**, só depois das perguntas acima
8. Mostrar **uma** página de relatório, com dados reais e o nível de evidência marcado.
   Perguntar: "O que aqui você já sabia? O que é novo? O que você faria com isso amanhã?"
9. "Se eu te mandasse isso todo mês para os seus produtos, quem decidiria a compra? Como seria o processo?"

**Fechamento (2 min)**
10. "Posso te mandar um relatório piloto com os projetos que combinam com o seu catálogo, em troca de 20 minutos de retorno?"
    Se já houver relatório pronto: oferecer o piloto pago (seção 4).

**Não fazer:** explicar a ideia antes da pergunta 8, perguntar "você pagaria?", aceitar elogio como validação ou mencionar o modelo de juros.

## 3. O que conta como evidência

| Sinal | Peso |
|---|---|
| Elogio, "ideia interessante", "eu usaria" | **Nenhum** |
| Descreve um caso concreto e recente de oportunidade perdida | Médio |
| Já gasta tempo ou dinheiro com o problema (pessoa dedicada, assinatura) | Alto |
| Aceita gastar mais 20 minutos para avaliar um piloto | Alto |
| Apresenta quem aprova a compra ou aceita piloto pago com data | **Validação** |

Critério de continuidade (fixado antes das conversas): seguir com transmissão se **≥ 3 de 5** descreverem caso concreto **e** **≥ 2**
aceitarem piloto (gratuito ou pago). Se a dor aparecer mais em distribuição, rever o nicho (ver `04-mercado-e-posicionamento.md` §4c).

## 4. Proposta de piloto (modelo)

- **Entrega:** relatório com os empreendimentos de transmissão compatíveis com o catálogo do cliente: situação, datas previstas,
  módulos e equipamentos (confirmados × inferidos), mudanças desde o último relatório, fonte de cada linha e CSV.
- **Prazo:** 2 entregas mensais.
- **Preço experimental:** R$ 500–1.500, a definir pelo escopo. Primeiro piloto pode ser gratuito em troca de retorno estruturado.
- **Critério de sucesso combinado com o cliente:** número de projetos considerados relevantes pelo cliente / total entregue
  (a meta experimental do plano é 80%, medida com esse critério e não com a confiança do classificador).
- **Limites ditos por escrito:** projeto não é pedido de compra; inferência não é confirmação; não fornecemos contatos pessoais.

## 5. Registro das conversas

Uma linha por conversa em `privado/validacao/conversas.csv` (fora do git), com consentimento para anotar:
`data, empresa_tipo, cargo, caso_concreto (s/n), gasto_atual, fontes_atuais, o_que_falta, aceitou_piloto (s/n/pago), proximo_passo`.
Não registrar dados pessoais além do necessário. Nome e contato ficam só se a pessoa concordar.
