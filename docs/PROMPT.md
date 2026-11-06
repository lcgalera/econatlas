# Prompt para continuar o rotzx com um assistente de IA

Copie o bloco abaixo como primeira mensagem de uma conversa nova (Claude Code ou outro assistente com acesso ao repositório).
Ele resume o projeto, as regras e o estado em 05/11/2026; a documentação completa está em [`PROJETO.md`](PROJETO.md).

---

```text
Você vai trabalhar no rotzx (repositório lcgalera/rotzx, site https://lcgalera.github.io/rotzx/).
Escreva e responda em português do Brasil. O nome do produto é "rotzx", sempre em minúsculas.

## O que é
Projeto pessoal de inteligência econômica com dados abertos e rastreáveis, com três frentes ativas:
1. Radar econômico e setorial: séries do BCB, IBGE e Focus; previsões do IPCA e da indústria de máquinas e
   materiais elétricos (IBGE 3.27) registradas antes de os dados saírem, com placar público (registro/*.csv, só acréscimos).
2. Radar de oportunidades em transmissão de energia (B2B): projetos do SIGET/ANEEL com evidência por regra (R1–R5),
   score explicado, histórico semanal (historico/*.csv), leilões e contexto econômico.
3. Atlas "Como o Brasil se conecta ao mundo" (https://lcgalera.github.io/rotzx/globo/): de quem o Brasil depende para vender e
   comprar, e como isso mudou desde 1997 — parceiros, produtos (SH4), concentração e comparação, com o contexto diplomático
   (ONU, OMC, conflitos) em segundo plano. É a frente em foco; as notícias estão pausadas.

## Leia antes de mudar qualquer coisa
- docs/PROJETO.md (visão geral, fontes, arquitetura, esquemas dos dados do globo, automação, limitações)
- docs/DECISOES.md (D1–D48: cada escolha e o motivo; registre uma decisão nova para cada mudança relevante)
- README.md e prototipos/globo/LEIAME.md

## Regras que não podem ser quebradas
1. Só dado real, com fonte e data. Nunca invente número, nem em exemplo de interface. Fixture de teste usa o formato
   real da fonte com valores marcados como inventados.
2. Interpretação nunca passa por fato. Frases geradas de números só descrevem; interpretação aparece marcada.
   Nada de nota de relação "boa" ou "ruim" entre países: mostre sinais medidos, cada um com a fonte.
3. Mantenha a proveniência: arquivo bruto + SHA-256, vintages, fonte e licença de cada dado.
4. Previsões: especificação fixa antes do backtest; o registro só recebe acréscimos (registro-verificar).
5. Séries da Macrodados são de uso pessoal: nunca no git, no site ou em automação. Não automatize área logada de ninguém.
6. Notícias: só título, veículo, data e link. Manchete só entra num país se o título o cita, com acento e palavra inteira;
   evite termos ambíguos (ex.: "peru", "sírio", "libanês").
7. O que for automático (categorias, assuntos, países citados) pode errar e a página precisa avisar.
8. Comunicação sem exagero: frases de comparação dizem a direção; associação não é causalidade.
9. Créditos e licenças das fontes sempre visíveis na página (ex.: CC BY 4.0 da UCDP e do Banco Mundial).

## Como trabalhar
- Python 3.9, dependências fixas em requirements.txt; .venv/bin/python -m rotzx <comando>; testes: .venv/bin/python -m pytest -q
  (147 passam e 1 é pulado em 06/11/2026). Rode os testes antes de cada commit.
- Interface sem build: HTML/JS com bibliotecas por CDN com versão exata (globe.gl@2.46.2, topojson-client@3.1.0,
  world-atlas@2.0.2, three-globe@2.45.6 para as texturas). O globo é uma página só: prototipos/globo/index.html.
- Teste a interface num navegador sem tela (Playwright/Chromium com WebGL por software) em desktop e celular
  (1440×900 e 390×844), sem erros de página e sem rolagem horizontal.
- Dados do globo: rotzx mundo-atualizar [--so-noticias | --so-relacoes | --sem-noticias]. Coletores em rotzx/mundo/.
  Cada fonte que falha vai para "falhas" e não derruba as outras nem apaga dados bons.
- Automação: .github/workflows/globo.yml (só à mão: retrato histórico; agendamentos pausados),
  rotina-mensal.yml (publica o site; dias 12 e 20), radar-siget.yml (segundas). O site só muda quando a rotina
  mensal roda; o globo lê os dados frescos do repositório ao abrir.
- Git: trabalhe numa branch, commits em português com mensagem clara (o quê e por quê). Não reescreva histórico
  de branch compartilhada. PR, merge e publicação só quando o dono pedir.
- Antes de usar uma fonte nova: confira licença e termos, se ela permite acesso automatizado e se o ambiente alcança o
  domínio; documente na tabela de fontes (docs/PROJETO.md) e numa decisão nova.
- Escreva para pessoas comuns: frases curtas, sem jargão; números no formato brasileiro (US$ 1,2 bi; 28,7%).

## Estado e próximos passos (06/11/2026)
- Atlas publicado (D47): início com perguntas que executam ações, métricas no mapa com escalas fixas, painel do país em três
  partes com resumo por regras fixas, explorar por produto, comparar dois parceiros, bandeiras (flag-icons 7.5.0), estado na URL,
  lista funcional sem WebGL. Dados: prototipos/globo/dados/historia.json e produtos.json (rotzx mundo-atualizar --historico),
  catalog/paises_mundo.csv (rotzx mundo-codigos).
- Limitações: composição por produto só em 2000, 2010 e 2025; explorador com os 12 maiores parceiros por produto; valores em
  dólares correntes; fronteiras atuais para países extintos.
- Próximos passos possíveis: mais anos de composição por produto (a consulta do Comex é uma por ano e fluxo); séries em valores
  reais ou volume (kg) para separar preço de quantidade; mapa 2D leve como alternativa visual ao globo.
- Radar: setorial_v2; primeiras avaliações do IPCA (nov/2026) e da indústria (dez/2026).

Comece lendo os arquivos indicados, confirme em poucas linhas o que entendeu e proponha o próximo passo antes de codar.
```

---

## Como usar

- **Continuar o projeto:** cole o bloco como está e, logo depois, diga o que quer (ex.: "vamos fazer o 'Por que importa para o Brasil'").
- **Tarefa pontual:** cole o bloco e troque o último parágrafo pelo pedido.
- **Atualize este arquivo** quando o estado mudar (nova frente, nova fonte, nova regra), junto com `PROJETO.md` e `DECISOES.md`.
