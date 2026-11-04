# Protótipo: o mundo visto do Brasil (D38)

Abra `index.html` no navegador (precisa de internet para as bibliotecas e de WebGL).

**O que funciona:** globo que gira sozinho; arrastar para girar e rolar para aproximar; passar o mouse mostra o nome; clicar num país (ou buscar pelo nome)
dá zoom nele e abre o painel. Fecha com "Voltar ao mundo", com o × ou com Esc. Cada país tem link direto (`index.html#China`).
A tela é dividida: o globo à esquerda e, à direita, um resumo fixo (comércio do Brasil no ano, 5 maiores parceiros clicáveis, manchetes em alta
no mundo). Ao clicar num país, o painel dele abre por cima do resumo e o globo encolhe para a área livre; no celular, o resumo e o painel
viram gavetas embaixo e o globo fica em cima. Começa com o Brasil de frente, gira devagar, e "Voltar ao mundo" volta para o Brasil.
O planeta usa a imagem de satélite Blue Marble (NASA, domínio público) com mapa de relevo, servidas pelo pacote `three-globe@2.45.6` (MIT);
os países são camadas translúcidas por cima: Brasil em verde, os 20 países do protótipo em azul-acinzentado, o selecionado em branco.

**O que não é real ainda:** nenhum número, manchete ou texto do painel. Os blocos mostram só de onde cada coisa vai vir:
Comex Stat (relação comercial com o Brasil), Banco Mundial e FMI (economia), GDELT e feeds RSS (manchetes, só título + veículo + link)
e um texto de "por que importa para o Brasil" marcado como interpretação.

**Os 20 países** foram escolhidos para testar a navegação; a lista final sai dos dados de comércio exterior.
Singapura ficou de fora porque não aparece no mapa nesta escala.

**Bibliotecas** (fixadas por versão, via jsDelivr): `globe.gl@2.46.2` (MIT), `topojson-client@3.1.0` (ISC) e
`world-atlas@2.0.2` (ISC; contornos do Natural Earth 1:110m, domínio público).
Texturas: `three-globe@2.45.6/example/img/earth-blue-marble.jpg` e `earth-topology.png`.

**Testado** em Chromium sem tela (WebGL por software), em 1280×800 e 390×844: carrega o globo, abre por busca e por clique,
troca as abas, fecha com Esc e não tem rolagem horizontal no celular.

**Próximo passo:** liberar na rede do ambiente `api.gdeltproject.org`, `api.worldbank.org`, `www.imf.org` e `api-comexstat.mdic.gov.br`,
conferir licença e termos de uso de cada um e ligar os dados aos 20 países.

## Dados (desde 04/11/2026)

`rotzx mundo-atualizar` gera `dados/mundo.json|js` (comércio e economia) e `dados/noticias.json|js` (manchetes); o globo lê os `.js`,
o que funciona também abrindo o arquivo direto no computador.

| Bloco | Fonte | O que entra |
|---|---|---|
| Relação com o Brasil | Comex Stat (MDIC) | exportações, importações, saldo, posição no ranking e os 5 principais produtos (SH4) de cada lado, no último ano completo |
| Economia | Banco Mundial (CC BY 4.0) | crescimento do PIB, inflação, PIB e população, o valor mais recente de cada um |
| Manchetes | feeds RSS de veículos em português (g1, Folha, BBC News Brasil, DW, Agência Brasil, CNN Brasil, RFI) e GDELT | manchetes dos últimos 7 dias que citam o país no título; só título, veículo, data e link |

- O FMI ficou de fora: o servidor dele barra acesso automatizado ("Access Denied").
- O resumo de cada país é gerado dos números do Comex Stat e só descreve: posição, valores, participação e saldo. Os produtos ficam
  fora da frase porque os nomes oficiais dos grupos SH4 são longos e abreviá-los pode enganar (ex.: "Barcos-faróis…", que inclui plataformas).
- As manchetes são classificadas por palavras-chave no título (`rotzx/mundo/gdelt.py`), e isso pode errar.
- O workflow `.github/workflows/globo.yml` atualiza as manchetes todo dia e o comércio todo dia 15.
