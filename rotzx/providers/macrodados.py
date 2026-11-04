"""Leitura de exportações da Macrodados Web (CSV/XLS/XLSX, uma ou várias séries).

Formato observado (exportação CSV, nov/2026): UTF-8 com BOM, separador vírgula,
tudo entre aspas, decimal com ponto, primeira coluna "Data", uma coluna por série
com o nome completo (ex.: "ABINEE - Faturamento ... - Total (R$ M)") e um rodapé
"Fonte : Macrodados Web". O código da série (md####) não vem no arquivo.

Os Termos de uso da Macrodados proíbem copiar, redistribuir ou republicar o
conteúdo; por isso toda série importada daqui é marcada como `uso = pessoal`.
"""
import io
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .arquivo import _to_date, _to_number

LICENCA = "Macrodados Web – Termos de uso proíbem cópia, redistribuição e republicação; somente uso pessoal"


@dataclass
class ExportedSeries:
    coluna: str
    nome: str
    instituicao: str
    unidade: str
    periodicidade: str
    data: pd.DataFrame


def norm(col: str) -> str:
    """Normaliza o nome da coluna (a Macrodados mistura espaços comuns e não separáveis)."""
    return re.sub(r"\s+", " ", col.replace("\xa0", " ")).strip()


def load_manifest(path) -> Dict[str, Dict]:
    """Manifesto da cesta: nome da coluna -> código md####, instituição, tema, unidade e nome legível."""
    if not path.exists():
        return {}
    return {norm(item["coluna"]): item for item in json.loads(path.read_text(encoding="utf-8"))}


def slug(text: str, max_len: int = 60) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t[:max_len].rstrip("_")


def split_name(col: str):
    """'ABINEE - Faturamento ... (R$ M)' -> ('ABINEE - Faturamento ...', 'ABINEE', 'R$ M')."""
    nome = col.strip()
    unidade = "a confirmar"
    m = re.search(r"\(([^()]*)\)\s*$", nome)
    if m:
        unidade = m[1].strip()
        nome = nome[: m.start()].strip()
    first = nome.split(" - ", 1)[0].strip()
    instituicao = first if " - " in nome and len(first) <= 30 else "a confirmar"
    return nome, instituicao, unidade


def infer_frequency(dates: pd.Series) -> str:
    gap = dates.sort_values().diff().dt.days.median()
    if gap >= 300:
        return "anual"
    if gap >= 80:
        return "trimestral"
    if gap >= 27:
        return "mensal"
    if gap <= 4:
        return "diaria"
    raise ValueError(f"periodicidade não suportada (intervalo típico de {gap:.0f} dias, ex.: semanal)")


def read_export(raw: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw), dtype=str)
    text = raw.decode("utf-8-sig", errors="replace")
    first = text.splitlines()[0]
    sep = ";" if first.count(";") > first.count(",") else ","
    return pd.read_csv(io.StringIO(text), sep=sep, dtype=str, skip_blank_lines=True)


def parse_export(raw: bytes, filename: str) -> List[ExportedSeries]:
    df = read_export(raw, filename)
    date_col = df.columns[0]
    dates = _to_date(df[date_col])
    if dates.notna().sum() == 0:
        raise ValueError(f"não reconheci as datas da coluna '{date_col}' (ex.: {df[date_col].iloc[0]!r})")
    out = []
    for col in df.columns[1:]:
        values = _to_number(df[col])
        data = pd.DataFrame({"date": dates, "value": values}).dropna()
        if data.empty:
            continue
        if data["date"].duplicated().any():
            raise ValueError(f"datas duplicadas na coluna '{col}'")
        nome, inst, unidade = split_name(col)
        out.append(ExportedSeries(col, nome, inst, unidade, infer_frequency(data["date"]),
                                  data.sort_values("date").reset_index(drop=True)))
    if not out:
        raise ValueError("nenhuma série com dados encontrada no arquivo")
    return out
