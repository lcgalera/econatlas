"""Nomes curtos revisados dos produtos (SH4) mais negociados pelo Brasil, e grupos de produtos (D47).

O nome oficial do Comex Stat continua disponível em toda a interface (com o código SH4); o nome curto só facilita a leitura.
Regra: o nome curto não pode estreitar a categoria. Quando a posição junta coisas diferentes, o nome diz isso
(ex.: 8905 não é "barcos-faróis": inclui dragas, guindastes flutuantes e plataformas de perfuração).
Conferidos contra os nomes oficiais da posição em 06/11/2026.
"""

CURTOS = {
    "0102": "Bovinos vivos",
    "0201": "Carne bovina fresca ou refrigerada",
    "0202": "Carne bovina congelada",
    "0203": "Carne suína",
    "0207": "Carnes e miudezas de aves",
    "0901": "Café (inclui torrado e descafeinado)",
    "1001": "Trigo",
    "1005": "Milho",
    "1201": "Soja em grão (mesmo triturada)",
    "1507": "Óleo de soja",
    "1602": "Preparações e conservas de carne",
    "1701": "Açúcar de cana ou de beterraba",
    "2009": "Sucos de frutas e de hortaliças",
    "2101": "Café solúvel e extratos de café, chá e mate",
    "2207": "Álcool etílico (inclui etanol)",
    "2304": "Farelo e tortas de soja",
    "2401": "Tabaco não manufaturado",
    "2601": "Minério de ferro",
    "2603": "Minério de cobre",
    "2701": "Carvão mineral (hulha)",
    "2709": "Petróleo bruto",
    "2710": "Derivados de petróleo (exceto óleo bruto)",
    "2711": "Gás natural e outros gases de petróleo (inclui GLP)",
    "2716": "Energia elétrica",
    "2818": "Alumina e corindo (óxido e hidróxido de alumínio)",
    "2933": "Compostos heterocíclicos nitrogenados (química fina)",
    "3002": "Vacinas, sangue e produtos imunológicos",
    "3004": "Medicamentos em doses ou embalagens de venda",
    "3102": "Fertilizantes nitrogenados",
    "3103": "Fertilizantes fosfatados",
    "3104": "Fertilizantes potássicos",
    "3105": "Fertilizantes mistos (NPK e outros)",
    "3808": "Defensivos agrícolas e desinfetantes",
    "3901": "Polietileno e outros polímeros de etileno",
    "4011": "Pneus novos de borracha",
    "4104": "Couros bovinos e equinos curtidos",
    "4407": "Madeira serrada",
    "4703": "Celulose (pasta química de madeira)",
    "4802": "Papel para escrita e impressão (não revestido)",
    "5201": "Algodão em bruto",
    "6403": "Calçados com parte superior de couro",
    "6802": "Pedras de construção trabalhadas (granito, mármore etc.)",
    "7108": "Ouro",
    "7201": "Ferro-gusa",
    "7202": "Ferroligas",
    "7207": "Semimanufaturados de ferro ou aço",
    "7210": "Chapas de aço revestidas",
    "7403": "Cobre refinado e ligas de cobre, em bruto",
    "7601": "Alumínio bruto",
    "8408": "Motores diesel",
    "8409": "Partes de motores a pistão",
    "8411": "Turbinas a gás e turborreatores",
    "8413": "Bombas para líquidos",
    "8414": "Bombas de ar, compressores e ventiladores",
    "8421": "Centrífugas e filtros de líquidos ou gases",
    "8429": "Máquinas de terraplenagem (escavadeiras, niveladoras etc.)",
    "8431": "Partes de máquinas de elevação e terraplenagem",
    "8443": "Impressoras e máquinas de impressão",
    "8471": "Computadores e unidades",
    "8473": "Partes de computadores e máquinas de escritório",
    "8479": "Outras máquinas com função própria",
    "8481": "Torneiras e válvulas",
    "8483": "Eixos, mancais e engrenagens de transmissão",
    "8504": "Transformadores e conversores elétricos",
    "8517": "Telefones, celulares e equipamentos de rede",
    "8529": "Partes de aparelhos de rádio, TV e transmissão",
    "8536": "Interruptores, relés e conectores elétricos",
    "8541": "Diodos, transistores e células fotovoltaicas",
    "8542": "Circuitos integrados (chips)",
    "8544": "Fios e cabos elétricos isolados",
    "8701": "Tratores",
    "8703": "Automóveis de passageiros",
    "8704": "Veículos de carga",
    "8708": "Partes e acessórios de veículos",
    "8802": "Aeronaves (aviões, helicópteros) e veículos espaciais",
    "8905": "Embarcações especiais e plataformas (dragas, guindastes flutuantes, plataformas de perfuração)",
    "9018": "Instrumentos e aparelhos médicos",
    "9032": "Instrumentos de regulação e controle automáticos",
}

# Código que o Comex Stat usa sem descrição na tabela de produtos: nada é inventado sobre ele
SEM_DESCRICAO = {"9998": "Código 9998 (sem descrição no Comex Stat)"}

# Grupos: somas exatas de posições SH4, feitas sobre a distribuição completa por parceiro (não sobre listas de "maiores")
GRUPOS = {
    "g-fertilizantes": {"nome": "Fertilizantes", "sh4": ["3101", "3102", "3103", "3104", "3105"],
                        "regra": "posições 3101 a 3105 (capítulo 31: adubos e fertilizantes)"},
    "g-petroleo": {"nome": "Petróleo e derivados", "sh4": ["2709", "2710"],
                   "regra": "petróleo bruto (2709) + derivados, exceto óleo bruto (2710)"},
    "g-carnes": {"nome": "Carnes (bovina, suína e de aves)", "sh4": ["0201", "0202", "0203", "0207"],
                 "regra": "carne bovina fresca (0201) e congelada (0202), carne suína (0203), carnes e miudezas de aves (0207)"},
    "g-veiculos": {"nome": "Veículos e partes", "sh4": ["8701", "8702", "8703", "8704", "8705", "8706", "8707", "8708"],
                   "regra": "posições 8701 a 8708: tratores, ônibus, automóveis, veículos de carga e especiais, chassis, carrocerias e partes"},
}


def curto(sh4: str, oficial: str = "") -> str:
    if sh4 in CURTOS:
        return CURTOS[sh4]
    if sh4 in SEM_DESCRICAO:
        return SEM_DESCRICAO[sh4]
    return oficial
