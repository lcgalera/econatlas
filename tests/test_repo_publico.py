"""O repositório é público (D23): nada de uso pessoal pode estar versionado."""
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CODIGO_MACRODADOS = re.compile(r"\b(?:md|mc|et|st|ce|bo)\d{4}\b")  # duas letras + 4 dígitos: formato dos códigos do catálogo da Macrodados
PROIBIDOS = ("privado/", "data/", "site/", "docs/DIARIO.md")


def _versionados():
    try:
        r = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True)
    except FileNotFoundError:
        pytest.skip("git indisponível")
    if r.returncode != 0:
        pytest.skip("pasta fora de um repositório git")
    return [l for l in r.stdout.splitlines() if l]


def test_no_personal_files_versioned():
    arquivos = _versionados()
    assert not [a for a in arquivos if a.startswith(PROIBIDOS)]


def test_no_macrodados_codes_in_versioned_files():
    achados = []
    for a in _versionados():
        p = RAIZ / a
        if p.suffix in (".png", ".jpg", ".sqlite") or not p.exists():
            continue
        for m in CODIGO_MACRODADOS.finditer(p.read_text(encoding="utf-8", errors="ignore")):
            achados.append(f"{a}: {m.group()}")
    assert not achados, achados[:20]
