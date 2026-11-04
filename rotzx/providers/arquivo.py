"""Importação de arquivos CSV/Excel exportados legalmente (ex.: Macrodados).

O formato exato das exportações da Macrodados ainda não foi confirmado, então
o leitor é genérico: uma coluna de datas e uma coluna de valores, com detecção
de separador e de decimal brasileiro ("1.234,56"). O arquivo original é sempre
arquivado sem alterações.

No catálogo, `codigo` guarda o caminho do arquivo e `extra` guarda as colunas.
"""
import io
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from . import FetchResult


def _to_number(s: pd.Series) -> pd.Series:
    if s.dtype.kind in "if":
        return s.astype(float)
    txt = s.astype(str).str.strip()
    br = txt.str.contains(r",\d+$", regex=True)  # decimal com vírgula
    txt = txt.where(~br, txt.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(txt, errors="coerce")


MESES_PT = {m: i for i, m in enumerate(["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"], 1)}


def _parse_date(txt: str):
    """Converte um rótulo de período para o 1º dia do período. Devolve NaT se não reconhecer."""
    t = txt.strip().strip('"').lower()
    if re.fullmatch(r"\d{4}", t):                                   # 2024 (anual)
        return pd.Timestamp(int(t), 1, 1)
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", t)                       # 01/2024
    if m:
        return pd.Timestamp(int(m[2]), int(m[1]), 1)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", t)                       # 2024-01
    if m:
        return pd.Timestamp(int(m[1]), int(m[2]), 1)
    m = re.fullmatch(r"([a-zç]{3})[a-zç]*[/\-. ](\d{2}|\d{4})", t)  # jan/2024, jan/24
    if m and m[1] in MESES_PT:
        y = int(m[2]) + (2000 if len(m[2]) == 2 and int(m[2]) < 50 else 1900 if len(m[2]) == 2 else 0)
        return pd.Timestamp(y, MESES_PT[m[1]], 1)
    m = re.fullmatch(r"([1-4])\s*[ºo]?\s*t(?:ri\w*)?[\s/.\-]*(\d{4})", t) or \
        re.fullmatch(r"t([1-4])[\s/.\-]*(\d{4})", t)                # 1T2024, 1º tri/2024, T1/2024
    if m:
        return pd.Timestamp(int(m[2]), 3 * (int(m[1]) - 1) + 1, 1)
    m = re.fullmatch(r"(\d{4})[\s.\-/]*t([1-4])", t)                # 2024T1
    if m:
        return pd.Timestamp(int(m[1]), 3 * (int(m[2]) - 1) + 1, 1)
    return pd.to_datetime(t, dayfirst=True, errors="coerce")        # 31/01/2024, 2024-01-31...


def _to_date(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    return pd.to_datetime(s.astype(str).map(_parse_date), errors="coerce")


def read_table(raw: bytes, filename: str, date_col: Optional[str] = None, value_col: Optional[str] = None) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(raw))
    else:
        text = raw.decode("utf-8-sig", errors="replace")
        sep = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
        df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
    date_col = date_col or df.columns[0]
    value_col = value_col or df.columns[1]
    out = pd.DataFrame({"date": _to_date(df[date_col]), "value": _to_number(df[value_col])})
    out = out.dropna()
    if out.empty:
        raise ValueError("nenhuma linha válida (data + valor) encontrada no arquivo")
    if out["date"].duplicated().any():
        raise ValueError("datas duplicadas no arquivo; confira a coluna de datas")
    return out.sort_values("date").reset_index(drop=True)


def fetch(meta) -> FetchResult:
    path = Path(meta.codigo)
    raw = path.read_bytes()
    data = read_table(raw, path.name, meta.extra.get("coluna_data"), meta.extra.get("coluna_valor"))
    if meta.inicio:  # corte declarado no catálogo (motivo registrado na descrição)
        data = data[data["date"] >= pd.Timestamp(meta.inicio)].reset_index(drop=True)
    return FetchResult(raw=raw, raw_ext=path.suffix.lstrip(".") or "csv", source_url=f"arquivo:{path.name}", data=data)
