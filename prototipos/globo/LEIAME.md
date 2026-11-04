# Protótipo: o mundo visto do Brasil (D38)

Abra `index.html` no navegador (precisa de internet para as bibliotecas e de WebGL).

**O que funciona:** globo que gira sozinho; arrastar para girar e rolar para aproximar; passar o mouse mostra o nome; clicar num país (ou buscar pelo nome)
dá zoom nele e abre o painel. Fecha com "Voltar ao mundo", com o × ou com Esc. Cada país tem link direto (`index.html#China`).
Um quadro só, dividido em dois, com uma barra em cima. A barra mostra a marca, de quando são os dados (e se alguma fonte de manchetes
não respondeu) e a busca. À esquerda, o globo, com a opção "Lista de países" (que também substitui o globo quando o navegador não tem
WebGL) e botões de zoom. À direita, "Mundo agora": abas Agora (geopolítica e temas globais), No Brasil, Conflitos e Comércio do Brasil, com filtros
por categoria e contagem; a ordem é por data, sem ranking de importância. Ao clicar num país, o painel dele entra no lugar.
No celular, o globo fica em cima e o texto embaixo. Começa com o Brasil de frente, gira devagar, e "Mundo" volta para o Brasil.
O planeta usa a imagem de satélite Blue Marble (NASA, domínio público), tingida de verde-petróleo, com mapa de relevo, servidas pelo pacote `three-globe@2.45.6` (MIT);
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
| Sinais da relação: ONU | votos na Assembleia Geral (Voeten, Strezhnev e Bailey, Harvard Dataverse, CC0) | concordância com o Brasil no último ano e média de 5 anos, posição entre todos os países (D42) |
| Sinais da relação: OMC | lista oficial de disputas do site da OMC | disputas com o Brasil desde 1995 e, na visão externa, as do país com outros países nos últimos 5 anos; para a UE, as da UE |
| Conflitos armados | UCDP/PRIO Armed Conflict Dataset (Uppsala, CC BY 4.0) | conflitos dos últimos 5 anos com um governo de um dos lados e 25+ mortes em combate no ano: lados, apoio com tropas, o que está em disputa, intensidade (D43) |
| Manchetes | feeds RSS de veículos em português (g1, Folha, BBC News Brasil, DW, Agência Brasil, RFI) e GDELT | manchetes dos últimos 7 dias que citam o país no título; só título, veículo, data e link |

- O FMI ficou de fora: o servidor dele barra acesso automatizado ("Access Denied").
- O resumo de cada país é gerado dos números do Comex Stat e só descreve: posição, valores, participação e saldo. Os produtos ficam
  fora da frase porque os nomes oficiais dos grupos SH4 são longos e abreviá-los pode enganar (ex.: "Barcos-faróis…", que inclui plataformas).
- As manchetes são classificadas por palavras-chave no título (`rotzx/mundo/gdelt.py`), e isso pode errar.
- O workflow `.github/workflows/globo.yml` atualiza as manchetes todo dia e o comércio, os votos na ONU, as disputas na OMC e os conflitos armados todo dia 15.
- Não há nota de relação "boa" ou "ruim": o painel mostra sinais medidos, cada um com a fonte (D42).
- Manchetes (D44): em cima, os assuntos cobertos por mais veículos (agrupados pelas palavras do título); embaixo, o resto por dia, com a hora de Brasília. Cada manchete é marcada com os países que o título cita, e o globo pinta os países por número de manchetes (camada "Notícias"). Tudo automático, pode errar, e a página avisa.
