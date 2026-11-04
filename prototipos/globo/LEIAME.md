# Protótipo: o mundo visto do Brasil (D38)

Abra `index.html` no navegador (precisa de internet para as bibliotecas e de WebGL).

**O que funciona:** globo que gira sozinho; arrastar para girar e rolar para aproximar; passar o mouse mostra o nome; clicar num país (ou buscar pelo nome)
dá zoom nele e abre o painel. Fecha com "Voltar ao mundo", com o × ou com Esc. Cada país tem link direto (`index.html#China`).
No computador, o painel fica à direita e a câmera mira ao lado, para o país aparecer na área livre; no celular, o painel vira uma gaveta embaixo.
Brasil em verde, os 20 países do protótipo em âmbar e o resto em azul.

**O que não é real ainda:** nenhum número, manchete ou texto do painel. Os blocos mostram só de onde cada coisa vai vir:
Comex Stat (relação comercial com o Brasil), Banco Mundial e FMI (economia), GDELT e feeds RSS (manchetes, só título + veículo + link)
e um texto de "por que importa para o Brasil" marcado como interpretação.

**Os 20 países** foram escolhidos para testar a navegação; a lista final sai dos dados de comércio exterior.
Singapura ficou de fora porque não aparece no mapa nesta escala.

**Bibliotecas** (fixadas por versão, via jsDelivr): `globe.gl@2.46.2` (MIT), `topojson-client@3.1.0` (ISC) e
`world-atlas@2.0.2` (ISC; contornos do Natural Earth 1:110m, domínio público).

**Testado** em Chromium sem tela (WebGL por software), em 1280×800 e 390×844: carrega o globo, abre por busca e por clique,
troca as abas, fecha com Esc e não tem rolagem horizontal no celular.

**Próximo passo:** liberar na rede do ambiente `api.gdeltproject.org`, `api.worldbank.org`, `www.imf.org` e `api-comexstat.mdic.gov.br`,
conferir licença e termos de uso de cada um e ligar os dados aos 20 países.
