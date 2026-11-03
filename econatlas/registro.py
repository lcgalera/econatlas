"""Registro público em texto (CSV), só com acréscimos: a prova de que nenhuma previsão foi alterada.

Arquivos em registro/ (versionados no git):
- previsoes_ipca.csv        previsões do IPCA (tabela previsoes)
- previsoes_setoriais.csv   previsões setoriais de séries PÚBLICAS (tabela previsoes_setoriais)
- coletas.csv               cada versão distinta dos dados públicos usada (série + SHA-256 dos dados)

Regras (D23):
- exportar nunca reescreve: as linhas existentes ficam byte a byte, as novas vão para o fim;
- a identidade de uma previsão é a chave natural (modelo, série, origem, alvo), não o id do banco,
  porque o GitHub Actions monta um banco novo a cada execução;
- verificar falha se (1) alguma linha da versão anterior no git mudou ou sumiu, ou (2) o banco
  tem, para a mesma chave, valores diferentes dos do CSV.
"""
import csv
import io
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import catalog as cat
from . import config, storage

DIR = config.ROOT / "registro"

TABELAS = {
    "previsoes_ipca.csv": {
        "tabela": "previsoes",
        "chave": ["modelo", "serie_id", "origem", "alvo"],
        "colunas": ["registrado_em", "serie_id", "modelo", "especificacao", "versao_codigo", "origem", "alvo",
                    "horizonte", "valor", "lo80", "hi80", "metodo_faixa", "dados_sha256"],
        "vintage": "vintage_id",
    },
    "previsoes_setoriais.csv": {
        "tabela": "previsoes_setoriais",
        "chave": ["setor", "modelo", "origem", "alvo"],
        "colunas": ["registrado_em", "setor", "serie_id", "transformacao", "modelo", "especificacao", "versao_codigo",
                    "origem", "alvo", "horizonte", "valor", "lo80", "hi80", "n_erros", "dados_sha256", "selic_sha256"],
        "vintage": "vintage_alvo",
    },
}
COLETAS = "coletas.csv"
COLETAS_COLS = ["series_id", "fetched_at", "source_url", "raw_sha256", "data_sha256", "n_obs", "first_date", "last_date"]


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(v)
    return str(v)


def _ensure(conn):
    from .forecast import registry, setorial
    registry.ensure_schema(conn)
    setorial.ensure_schema(conn)


def _rows(conn, nome: str, publicas: set) -> List[Dict[str, str]]:
    spec = TABELAS[nome]
    sha = {r["id"]: r["data_sha256"] for r in conn.execute("SELECT id, data_sha256 FROM vintages")}
    out = []
    for r in conn.execute(f"SELECT * FROM {spec['tabela']} ORDER BY id"):
        r = dict(r)
        if r["serie_id"] not in publicas:
            continue  # previsão de série de uso pessoal: nunca vai para o registro público
        r["dados_sha256"] = sha.get(r.get(spec["vintage"]), r.get("dados_sha256"))
        if nome == "previsoes_setoriais.csv":
            r["selic_sha256"] = sha.get(r.get("vintage_x"))
        out.append({c: _fmt(r.get(c)) for c in spec["colunas"]})
    return out


def _read(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        return [], []
    text = path.read_text(encoding="utf-8")
    return text.splitlines(), list(csv.DictReader(io.StringIO(text)))


def _line(cols, row) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow([row.get(c, "") for c in cols])
    return buf.getvalue()


def exportar(conn=None, pasta: Path = None, catalog: Optional[Dict] = None) -> Dict[str, int]:
    """Acrescenta ao fim de cada CSV as linhas novas do banco. Nunca reescreve as existentes."""
    conn = conn or storage.connect()
    pasta = Path(pasta or DIR)
    pasta.mkdir(parents=True, exist_ok=True)
    _ensure(conn)
    catalog = catalog if catalog is not None else cat.load_catalog()
    publicas = {k for k, m in catalog.items() if m.uso == "publico"}
    novos = {}
    for nome, spec in TABELAS.items():
        path = pasta / nome
        linhas, existentes = _read(path)
        vistos = {tuple(r[c] for c in spec["chave"]) for r in existentes}
        add = [r for r in _rows(conn, nome, publicas) if tuple(r[c] for c in spec["chave"]) not in vistos]
        with path.open("a", encoding="utf-8", newline="") as f:
            if not linhas:
                f.write(_line(spec["colunas"], {c: c for c in spec["colunas"]}) + "\n")
            for r in add:
                f.write(_line(spec["colunas"], r) + "\n")
        novos[nome] = len(add)
    # coletas: cada versão distinta (série + hash dos dados) das séries públicas
    path = pasta / COLETAS
    linhas, existentes = _read(path)
    vistos = {(r["series_id"], r["data_sha256"]) for r in existentes}
    add = []
    for v in conn.execute("SELECT * FROM vintages ORDER BY id"):
        v = dict(v)
        if v["series_id"] in publicas and (v["series_id"], v["data_sha256"]) not in vistos:
            vistos.add((v["series_id"], v["data_sha256"]))
            add.append({c: _fmt(v[c]) for c in COLETAS_COLS})
    with path.open("a", encoding="utf-8", newline="") as f:
        if not linhas:
            f.write(_line(COLETAS_COLS, {c: c for c in COLETAS_COLS}) + "\n")
        for r in add:
            f.write(_line(COLETAS_COLS, r) + "\n")
    novos[COLETAS] = len(add)
    return novos


def importar(conn=None, pasta: Path = None) -> Dict[str, int]:
    """Carrega o registro dos CSVs no banco (ex.: banco novo no GitHub Actions). Ignora o que já existe."""
    conn = conn or storage.connect()
    pasta = Path(pasta or DIR)
    _ensure(conn)
    n = {}
    for nome, spec in TABELAS.items():
        _, rows = _read(pasta / nome)
        cols = [c for c in spec["colunas"] if c not in ("dados_sha256", "selic_sha256")]
        before = conn.total_changes
        conn.executemany(
            f"INSERT OR IGNORE INTO {spec['tabela']} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [[(r[c] if r[c] != "" else None) for c in cols] for r in rows])
        conn.commit()
        n[nome] = conn.total_changes - before
    return n


def _git_show(ref: str, path: Path) -> Optional[str]:
    """Conteúdo do arquivo no commit `ref` (None se não houver git ou o arquivo não existia)."""
    try:
        res = subprocess.run(["git", "show", f"{ref}:./{path.name}"], cwd=path.parent, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return res.stdout if res.returncode == 0 else None


def verificar(conn=None, pasta: Path = None, contra: Optional[str] = "HEAD") -> List[str]:
    """Lista de problemas (vazia = ok)."""
    pasta = Path(pasta or DIR)
    problemas = []
    for nome in list(TABELAS) + [COLETAS]:
        path = pasta / nome
        atual, _ = _read(path)
        if contra:
            antigo = _git_show(contra, path)
            if antigo is not None:
                old = antigo.splitlines()
                if atual[:len(old)] != old:
                    for i, (a, b) in enumerate(zip(old, atual + [""] * len(old))):
                        if a != b:
                            problemas.append(f"{nome}: linha {i + 1} mudou ou sumiu em relação a {contra}")
                            break
    if conn is not None:
        _ensure(conn)
        for nome, spec in TABELAS.items():
            _, rows = _read(pasta / nome)
            cols = [c for c in spec["colunas"] if c not in ("dados_sha256", "selic_sha256", "registrado_em")]
            for r in rows:
                cond = " AND ".join(f"{c} = ?" for c in spec["chave"])
                db = conn.execute(f"SELECT {','.join(cols)} FROM {spec['tabela']} WHERE {cond}",
                                  [r[c] for c in spec["chave"]]).fetchone()
                if db is None:
                    continue
                dbv = [_fmt(x) for x in db]
                if dbv != [r[c] for c in cols]:
                    problemas.append(f"{nome}: banco diverge do CSV em {tuple(r[c] for c in spec['chave'])}")
    return problemas
