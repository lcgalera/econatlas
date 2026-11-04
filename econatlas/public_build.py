"""Build público: site estático (HTML + JSON) só com séries de uso público.

    .venv/bin/python -m econatlas publicar            # gera ./site
    .venv/bin/python -m econatlas publicar --saida X  # gera em X

O resultado pode ser hospedado como está (GitHub Pages, Cloudflare Pages): não depende
do servidor FastAPI. A interface é a mesma de web/, em modo estático (window.ECONATLAS_STATIC).

Regras (D20):
- entram só séries com uso == "publico" no catálogo; tudo que é pessoal (Macrodados) fica de fora
  do banco, dos JSON, dos gráficos e dos CSV;
- números derivados também: a análise setorial é REFEITA só com candidatos públicos (e com a
  correção de Holm sobre essa família), em vez de filtrar um resultado calculado com dados pessoais;
- ao final, `verificar` varre a saída e falha se encontrar identificador, código, nome ou sequência
  de valores de qualquer série de uso pessoal.
"""
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from . import __version__, config, payloads, storage, transforms
from . import catalog as cat

MARCA = ".econatlas-publico"  # arquivo que identifica uma pasta gerada por este build (só ela pode ser apagada)
JANELA = 6                    # tamanho da sequência de valores usada na detecção de vazamento


class VazamentoPublico(Exception):
    """A saída pública contém algo de uma série de uso pessoal."""


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")


def _prepare_dir(out: Path) -> None:
    if out.exists():
        if not (out / MARCA).exists() and any(out.iterdir()):
            raise RuntimeError(f"{out} existe e não foi gerada por este build; escolha outra pasta")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARCA).write_text("pasta gerada por econatlas publicar; pode ser apagada e refeita\n")


def _public_db(conn, dest: Path, permitidas: set) -> Dict:
    """Cópia do banco só com o que é público. Mantém versões, hashes e os gatilhos de imutabilidade."""
    from .forecast import focus, registry, setorial
    from .analysis import leading
    pub = storage.connect(dest)
    registry.ensure_schema(pub)
    setorial.ensure_schema(pub)
    focus.ensure_schema(pub)
    ids = sorted(permitidas)
    marks = ",".join("?" * len(ids))
    conn.row_factory = sqlite3.Row
    vint = conn.execute(f"SELECT * FROM vintages WHERE series_id IN ({marks})", ids).fetchall()
    pub.executemany(f"INSERT INTO vintages VALUES ({','.join('?' * len(vint[0].keys()))})", [tuple(r) for r in vint])
    obs = conn.execute(f"SELECT * FROM observations WHERE series_id IN ({marks})", ids).fetchall()
    pub.executemany("INSERT INTO observations VALUES (?,?,?,?)", [tuple(r) for r in obs])
    registry.ensure_schema(conn)
    prev = conn.execute("SELECT * FROM previsoes").fetchall()  # IPCA e Focus: dados públicos
    if prev:
        pub.executemany(f"INSERT INTO previsoes VALUES ({','.join('?' * len(prev[0].keys()))})", [tuple(r) for r in prev])
    setorial.ensure_schema(conn)
    setores_pub = [s for s, c in leading.SETORES.items() if c["alvo"] in permitidas]
    ps = conn.execute(f"SELECT * FROM previsoes_setoriais WHERE setor IN ({','.join('?' * len(setores_pub)) or 'NULL'}) "
                      f"AND serie_id IN ({marks})", setores_pub + ids).fetchall()
    if ps:
        pub.executemany(f"INSERT INTO previsoes_setoriais VALUES ({','.join('?' * len(ps[0].keys()))})", [tuple(r) for r in ps])
    focus.ensure_schema(conn)
    fc = conn.execute("SELECT * FROM focus_ipca_mensal").fetchall()
    if fc:
        pub.executemany("INSERT INTO focus_ipca_mensal VALUES (?,?,?,?,?,?)", [tuple(r) for r in fc])
    pub.commit()
    pub.close()
    return {"vintages": len(vint), "observacoes": len(obs), "previsoes_ipca": len(prev),
            "previsoes_setoriais": len(ps), "focus": len(fc)}


def _static_assets(out: Path) -> None:
    for name in ("styles.css", "texto.js", "app.js"):
        shutil.copy2(config.WEB_DIR / name, out / name)
    html = (config.WEB_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace('href="/static/', 'href="').replace('src="/static/', 'src="')
    html = html.replace('<script src="app.js', '<script>window.ECONATLAS_STATIC = true;</script>\n  <script src="app.js', 1)
    html = html.replace("Dados de fontes públicas oficiais (Banco Central do Brasil e IBGE), citados em cada indicador.",
                        "Versão pública: somente dados abertos (Banco Central do Brasil e IBGE), citados em cada indicador.")
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / ".nojekyll").write_text("")  # GitHub Pages: servir arquivos como estão


def build(out: Optional[Path] = None, conn=None, catalog: Optional[Dict] = None) -> Dict:
    from .analysis import leading
    from .forecast import setorial
    out = Path(out or config.PUBLIC_SITE_DIR)
    conn = conn or storage.connect()
    full = catalog if catalog is not None else cat.load_catalog()
    pub_cat = {k: m for k, m in full.items() if m.uso == "publico"}
    permitidas = set(pub_cat)
    _prepare_dir(out)
    data = out / "data"

    _write(data / "catalogo.json", payloads.catalogo(conn, pub_cat))
    n_series = 0
    for sid, meta in pub_cat.items():
        if storage.latest_vintage(conn, sid) is None:
            continue
        n_series += 1
        for t in transforms.available(meta):
            try:
                _write(data / "series" / sid / f"{t['id']}.json", payloads.series(conn, pub_cat, sid, t["id"]))
            except (ValueError, LookupError):
                continue
        _write(data / "series" / sid / "versoes.json", payloads.versoes(conn, sid))
    _write(data / "qualidade.json", payloads.qualidade(conn, pub_cat))
    _write(data / "previsoes_ipca.json", payloads.previsoes_ipca(conn))

    setores_pub = [s for s, c in leading.SETORES.items() if c["alvo"] in permitidas
                   and storage.latest_vintage(conn, c["alvo"]) is not None]
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    analises = []
    for s in setores_pub:
        a = leading.run(conn, s, permitidas=permitidas)
        a["executado_em"] = agora
        analises.append(a)
    _write(data / "analises_setores.json", analises)
    prev_setores = [s for s in setorial.SETORES_PREVISAO if s in setores_pub]
    _write(data / "previsoes_setoriais.json", payloads.previsoes_setoriais(conn, prev_setores))

    db_stats = _public_db(conn, data / "econatlas_publico.sqlite", permitidas)
    _static_assets(out)
    meta = {"gerado_em": agora, "versao_codigo": __version__, "series": n_series, "setores_analise": setores_pub,
            "setores_previsao": prev_setores, "banco": db_stats,
            "aviso": "Somente dados abertos. Séries de uso pessoal (Macrodados) não entram nesta versão."}
    _write(data / "meta.json", meta)
    verificar(out, full, conn)
    return meta


# ---------------------------------------------------------------- verificação

def _proibidos(catalog: Dict) -> Dict[str, List[str]]:
    """Textos que não podem aparecer na saída pública: ids, códigos, nomes de séries pessoais."""
    out = {}
    for m in catalog.values():
        if m.uso == "publico":
            continue
        tokens = {m.id, m.nome, m.extra.get("codigo_md") or "", m.extra.get("arquivo_original") or "",
                  m.extra.get("coluna_valor") or ""}
        out[m.id] = sorted(t for t in tokens if t and len(t) >= 5)
    return out


def _windows(values, n=JANELA):
    v = [round(float(x), 6) for x in values if x is not None and not np.isnan(x)]
    return {tuple(v[i:i + n]) for i in range(len(v) - n + 1)}


def _numeric_runs(obj, acc):
    """Coleta sequências de valores das listas [[data, valor], ...] em qualquer JSON."""
    if isinstance(obj, list):
        if obj and all(isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) for p in obj):
            acc.append([p[1] for p in obj if isinstance(p[1], (int, float))])
        else:
            for x in obj:
                _numeric_runs(x, acc)
    elif isinstance(obj, dict):
        for x in obj.values():
            _numeric_runs(x, acc)


def verificar(out: Path, catalog: Dict, conn=None) -> None:
    """Falha (VazamentoPublico) se a saída contiver qualquer rastro de série de uso pessoal."""
    from .analysis import leading
    out = Path(out)
    problemas = []
    proibidos = _proibidos(catalog)
    texto = {p: p.read_text(encoding="utf-8", errors="ignore") for p in out.rglob("*")
             if p.is_file() and p.suffix in (".json", ".html")}
    for sid, toks in proibidos.items():
        for p, t in texto.items():
            for tok in toks:
                if tok in t:
                    problemas.append(f"{p.relative_to(out)}: contém '{tok}' (série pessoal {sid})")
    for p in out.rglob("*.sqlite"):
        db = sqlite3.connect(p)
        for sid in proibidos:
            for tabela, col in (("vintages", "series_id"), ("observations", "series_id"), ("previsoes_setoriais", "serie_id")):
                try:
                    n = db.execute(f"SELECT COUNT(*) FROM {tabela} WHERE {col} = ?", (sid,)).fetchone()[0]
                except sqlite3.OperationalError:
                    n = 0
                if n:
                    problemas.append(f"{p.relative_to(out)}: tabela {tabela} tem {n} linhas da série pessoal {sid}")
        db.close()
    if conn is not None and proibidos:
        runs = []
        for p, t in texto.items():
            if p.suffix == ".json":
                _numeric_runs(json.loads(t), runs)
        publicadas = set().union(*(_windows(r) for r in runs)) if runs else set()
        for sid in proibidos:
            s = storage.load_observations(conn, sid)
            if s.empty:
                continue
            for nome, serie in (("nível", s), ("var. 12m", leading.transform(s, "log12").dropna())):
                hits = _windows(serie.values) & publicadas
                if hits:
                    problemas.append(f"valores da série pessoal {sid} ({nome}) aparecem na saída ({len(hits)} sequências)")
    if problemas:
        raise VazamentoPublico("saída pública contém dados de uso pessoal:\n  " + "\n  ".join(problemas[:30]))
