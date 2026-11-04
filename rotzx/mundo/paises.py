"""Países do protótipo (D38). Códigos conferidos em 04/11/2026:
iso_num = mapa (Natural Earth / world-atlas), iso3 = Banco Mundial, comex = tabela de países do Comex Stat.
'termos' = como o país aparece em manchetes em português (minúsculas, COM acento: sem acento, "França" viraria "Franca", a cidade de SP).
Termos ambíguos ficaram de fora (ex.: "Roma", que também é clube; "Paris", que também é time e nome próprio).
A lista dos 20 é a do protótipo de navegação; a final deve vir do ranking de comércio (ver build.py).
"""
PAISES = [
    {"iso_num": "076", "iso3": "BRA", "comex": "105", "nome": "Brasil", "artigo": "o", "termos": ["brasil", "brasileiro", "brasileira"]},
    {"iso_num": "156", "iso3": "CHN", "comex": "160", "nome": "China", "artigo": "a", "termos": ["china", "chinês", "chinesa", "chineses", "pequim", "xi jinping"]},
    {"iso_num": "840", "iso3": "USA", "comex": "249", "nome": "Estados Unidos", "artigo": "os", "termos": ["eua", "estados unidos", "norte-americano", "norte-americana", "casa branca", "washington"]},
    {"iso_num": "032", "iso3": "ARG", "comex": "063", "nome": "Argentina", "artigo": "a", "termos": ["argentina", "argentino", "argentinos", "buenos aires", "milei"]},
    {"iso_num": "528", "iso3": "NLD", "comex": "573", "nome": "Países Baixos", "artigo": "os", "termos": ["países baixos", "holanda", "holandês", "holandesa", "amsterdã", "roterdã"]},
    {"iso_num": "724", "iso3": "ESP", "comex": "245", "nome": "Espanha", "artigo": "a", "termos": ["espanha", "espanhol", "espanhola", "madri"]},
    {"iso_num": "276", "iso3": "DEU", "comex": "023", "nome": "Alemanha", "artigo": "a", "termos": ["alemanha", "alemão", "alemã", "alemães", "berlim"]},
    {"iso_num": "484", "iso3": "MEX", "comex": "493", "nome": "México", "artigo": "o", "termos": ["méxico", "mexicano", "mexicana"]},
    {"iso_num": "152", "iso3": "CHL", "comex": "158", "nome": "Chile", "artigo": "o", "termos": ["chile", "chileno", "chilena"]},
    {"iso_num": "392", "iso3": "JPN", "comex": "399", "nome": "Japão", "artigo": "o", "termos": ["japão", "japonês", "japonesa", "tóquio"]},
    {"iso_num": "356", "iso3": "IND", "comex": "361", "nome": "Índia", "artigo": "a", "termos": ["índia", "indiano", "indiana", "nova délhi", "modi"]},
    {"iso_num": "380", "iso3": "ITA", "comex": "386", "nome": "Itália", "artigo": "a", "termos": ["itália", "italiano", "italiana"]},
    {"iso_num": "410", "iso3": "KOR", "comex": "190", "nome": "Coreia do Sul", "artigo": "a", "termos": ["coreia do sul", "sul-coreano", "sul-coreana", "seul"]},
    {"iso_num": "124", "iso3": "CAN", "comex": "149", "nome": "Canadá", "artigo": "o", "termos": ["canadá", "canadense", "ottawa"]},
    {"iso_num": "250", "iso3": "FRA", "comex": "275", "nome": "França", "artigo": "a", "termos": ["frança", "francês", "francesa", "macron"]},
    {"iso_num": "600", "iso3": "PRY", "comex": "586", "nome": "Paraguai", "artigo": "o", "termos": ["paraguai", "paraguaio", "paraguaia", "assunção"]},
    {"iso_num": "643", "iso3": "RUS", "comex": "676", "nome": "Rússia", "artigo": "a", "termos": ["rússia", "russo", "russa", "russos", "moscou", "kremlin", "putin"]},
    {"iso_num": "682", "iso3": "SAU", "comex": "053", "nome": "Arábia Saudita", "artigo": "a", "termos": ["arábia saudita", "saudita", "riad"]},
    {"iso_num": "826", "iso3": "GBR", "comex": "628", "nome": "Reino Unido", "artigo": "o", "termos": ["reino unido", "britânico", "britânica", "londres"]},
    {"iso_num": "170", "iso3": "COL", "comex": "169", "nome": "Colômbia", "artigo": "a", "termos": ["colômbia", "colombiano", "colombiana", "bogotá"]},
    {"iso_num": "858", "iso3": "URY", "comex": "845", "nome": "Uruguai", "artigo": "o", "termos": ["uruguai", "uruguaio", "uruguaia", "montevidéu"]},
]
POR_ISO_NUM = {p["iso_num"]: p for p in PAISES}
