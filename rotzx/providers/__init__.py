"""Provedores de dados.

Cada provedor sabe buscar (ou ler) uma série e devolver:
  - o conteúdo bruto exatamente como recebido (para arquivamento e auditoria);
  - a URL/origem;
  - um DataFrame normalizado com colunas `date` (datetime, 1º dia do período) e `value` (float).

Para acrescentar uma fonte nova (ex.: API oficial da Macrodados, se houver licença),
basta criar um módulo com uma função `fetch(meta) -> FetchResult` e registrá-lo abaixo.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass
class FetchResult:
    raw: bytes
    raw_ext: str
    source_url: str
    data: pd.DataFrame


def get_provider(name: str):
    if name == "bcb_sgs":
        from . import bcb_sgs
        return bcb_sgs
    if name == "ibge_sidra":
        from . import ibge_sidra
        return ibge_sidra
    if name == "bcb_expectativas":
        from . import bcb_expectativas
        return bcb_expectativas
    if name == "arquivo":
        from . import arquivo
        return arquivo
    raise ValueError(f"provedor desconhecido: {name}")
