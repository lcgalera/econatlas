"""ANEEL — resultados dos leilões de transmissão (planilha da Central de Conteúdos), em formato de tabela.

A planilha oficial `Resultado_leiloes_transmissao.xlsx` (gov.br/aneel › Centrais de Conteúdos › Relatórios e Indicadores › Leilões)
é um relatório para leitura humana: um bloco por leilão, cabeçalhos em três formatos ao longo dos anos, linhas de TOTAL, lotes
"NÃO LEILOADO" e a coluna de deságio ora em %, ora em fração. Este módulo a transforma em uma linha por lote, guardando a linha
de origem e recalculando o deságio a partir das receitas (a coluna da fonte fica ao lado, para conferência).

O download automático é barrado pelo servidor (desafio anti-robô), então a planilha é baixada à mão e importada com
`rotzx leiloes-importar arquivo.xlsx` (D37). O conjunto "Resultado de leilões" do Portal de Dados Abertos (licença ODbL)
traz o mesmo conteúdo, mas parou no leilão 02/2024.
"""
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import config

ARQUIVO_TIDY = config.ROOT / "historico" / "leiloes_transmissao.csv"
ATRIBUICAO = ("Resultados de leilões: ANEEL (Central de Conteúdos, planilha Resultado_leiloes_transmissao.xlsx; "
              "mesmo conteúdo do conjunto 'Resultado de leilões' do Portal de Dados Abertos, licença ODbL).")
COLUNAS = ["leilao", "data_leilao", "etapa", "lote", "empreendimento", "ufs", "extensao_km", "prazo_meses", "prazo_texto",
           "rap_edital", "rap_vencedora", "desagio_pct", "desagio_fonte", "vencedor", "situacao", "linha_planilha"]

_NUM_ANO = re.compile(r"(\d{2,3})\s*/\s*(\d{4})")
_DATA = re.compile(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})")
_ETAPA = re.compile(r"(\d)\s*ª\s*ETAPA", re.I)


def _num(v) -> Optional[float]:
    s = str(v).strip().replace(" ", "")
    if not s or "*" in s or s in ("-", "–"):
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _limpa(v) -> str:
    return re.sub(r"\s*\n\s*", " ", str(v or "")).strip().strip("-").strip()


def _cabecalho(txt: str):
    """(leilão 'NN/AAAA', data ISO) a partir de um cabeçalho em qualquer dos formatos da planilha."""
    m, d = _NUM_ANO.search(txt), _DATA.search(txt)
    if not m:
        return None
    data = f"{int(d.group(3)):04d}-{int(d.group(2)):02d}-{int(d.group(1)):02d}" if d else None
    return f"{int(m.group(1)):02d}/{m.group(2)}", data


def ler_planilha(caminho: Path) -> pd.DataFrame:
    """Uma linha por lote. Linhas de TOTAL e em branco são descartadas; lotes não leiloados ficam, com situação própria."""
    df = pd.read_excel(caminho, sheet_name=0, header=None, dtype=str).fillna("")
    linhas, atual, etapa = [], None, ""
    for i, r in df.iterrows():
        c = [str(x) for x in r.tolist()] + [""] * (10 - len(r))
        c0, c1 = c[0].strip(), c[1].strip()
        if c0 and _NUM_ANO.search(c0):
            atual, etapa = _cabecalho(c0), ""
        lote_txt = c1
        concorrencia = False
        if c1 and _NUM_ANO.search(c1) and not c1.upper().startswith("LOTE"):  # formato antigo: cada linha é uma concorrência
            atual, etapa, concorrencia = _cabecalho(c1), "", True
            lote_txt = "único"
        e = _ETAPA.search(c[2]) or _ETAPA.search(c0)
        if e:
            etapa = e.group(1)
        vencedor = _limpa(c[9])
        if not atual or not lote_txt or not vencedor or _limpa(c[3]).upper() == "TOTAL":
            continue
        empreend = _limpa(c[2])
        if _NUM_ANO.search(empreend) and re.search(r"LEIL[ÃA]O", empreend, re.I):  # a célula repete o cabeçalho, sem descrição
            empreend = ""
        rap_e, rap_v = _num(c[6]), _num(c[7])
        nao = "NÃO LEILOADO" in vencedor.upper() or "NAO LEILOADO" in vencedor.upper()
        prazo = _num(c[5])
        linhas.append({
            "leilao": atual[0], "data_leilao": atual[1], "etapa": etapa,
            "lote": "único" if concorrencia else re.sub(r"(?i)^lote\s*", "", lote_txt).strip(),
            "empreendimento": empreend, "ufs": "/".join(u for u in re.split(r"[\s/,]+", _limpa(c[3])) if u),
            "extensao_km": _num(c[4]), "prazo_meses": prazo, "prazo_texto": _limpa(c[5]),
            "rap_edital": rap_e, "rap_vencedora": rap_v,
            "desagio_pct": round((1 - rap_v / rap_e) * 100, 2) if rap_e and rap_v is not None and not nao else None,
            "desagio_fonte": _num(c[8]),
            "vencedor": "" if nao else vencedor, "situacao": "não leiloado" if nao else "arrematado",
            "linha_planilha": int(i) + 1,
        })
    out = pd.DataFrame(linhas, columns=COLUNAS)
    out.attrs["arquivo"] = Path(caminho).name
    return out


def carregar(caminho: Path = ARQUIVO_TIDY) -> pd.DataFrame:
    if not Path(caminho).exists():
        return pd.DataFrame(columns=COLUNAS)
    return pd.read_csv(caminho, dtype={"leilao": str, "etapa": str, "lote": str, "ufs": str, "vencedor": str}, keep_default_na=False,
                       na_values={c: [""] for c in ("extensao_km", "prazo_meses", "rap_edital", "rap_vencedora", "desagio_pct", "desagio_fonte")})
