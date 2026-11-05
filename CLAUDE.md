# CLAUDE.md — rotzx

Responda em português do Brasil. O nome do produto é "rotzx", sempre em minúsculas.

## Modelo e esforço
- Tarefas simples (ler/explorar código, buscar arquivo, renomear, formatar):
  delegar pro subagente `explorador`.
- Mudança de tamanho médio: seguir no modelo da sessão.
- Arquitetura, debug difícil ou refatoração grande: entrar em plan mode
  e mostrar o plano antes de editar qualquer coisa.
- Se o pedido estiver vago, perguntar antes de gastar esforço.

## O projeto
Inteligência econômica com dados abertos e rastreáveis, em três frentes:
1. Radar econômico e setorial (BCB, IBGE, Focus; previsões registradas em `registro/`, só acréscimos).
2. Radar de oportunidades em transmissão de energia (SIGET/ANEEL; `rotzx/intelligence`, `historico/`).
3. O mundo visto do Brasil: globo em `prototipos/globo/index.html` (frente em foco), hoje um portfólio histórico de todos os países
   × Brasil, 1946–2025 (`rotzx/mundo/historia.py`, `catalog/paises_mundo.csv`). Notícias pausadas (`NOTICIAS = false`), sem coleta recorrente.

Antes de mudar algo relevante, leia `docs/PROJETO.md` (visão completa) e `docs/DECISOES.md` (D1–D46).
Toda mudança relevante ganha uma decisão nova em `docs/DECISOES.md`.

## Regras que não podem ser quebradas
- Só dado real, com fonte e data. Nunca inventar número, nem em exemplo de interface.
- Interpretação nunca passa por fato; nada de nota "boa/ruim" entre países, só sinais medidos com fonte.
- Séries da Macrodados são de uso pessoal: nunca no git, no site ou em automação.
- Notícias: só título, veículo, data e link; país citado com acento e palavra inteira, sem termos ambíguos.
- Automático (categorias, assuntos, países citados) pode errar, e a página avisa.
- Créditos e licenças das fontes sempre visíveis.

## Como trabalhar
- Python 3.9: `.venv/bin/python -m rotzx <comando>`; testes: `.venv/bin/python -m pytest -q` antes de cada commit.
- Interface sem build, bibliotecas por CDN com versão exata. Teste o globo em Chromium sem tela, em 1440×900 e 390×844.
- Dados do globo: `rotzx mundo-atualizar --historico` (retrato histórico) e `rotzx mundo-codigos` (tabela de países); fonte que falha vai para `falhas`.
- Git: trabalhar numa branch, commits em português; PR, merge e publicação só quando o dono pedir.
- Fonte nova: conferir licença, termos e se o ambiente alcança o domínio; documentar em `docs/PROJETO.md`.
