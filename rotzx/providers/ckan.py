"""Exploração de conjuntos de dados em portais CKAN (ANEEL Dados Abertos) — Fase 1, validação de fonte.

Não é um coletor de produção nem conhece os campos do SIGET de antemão: busca o conjunto pela
API padrão do CKAN (package_search / package_show), baixa os recursos tabulares, guarda cada
arquivo bruto com SHA-256 e escreve um relatório de campos (preenchimento, valores distintos,
exemplos, colunas que parecem chave e colunas compartilhadas entre tabelas) para avaliação humana.

Tudo vai para data/fontes/<portal>/<conjunto>/, que está fora do git (data/ no .gitignore).
O relatório não decide nada sozinho: é a base para escolher identificadores e campos do coletor real.
"""
import csv
import hashlib
import io
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .. import config

PORTAIS = {"aneel": "https://dadosabertos.aneel.gov.br"}
FORMATOS_TABULARES = {"csv", "zip", "xlsx", "xls", "json"}
NULOS = {"", "null", "nan", "none", "-", "n/a", "na"}


def _get(url: str, tries: int = 4) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("inalcançável")


def _api(portal: str, acao: str, **params) -> dict:
    base = PORTAIS.get(portal, portal).rstrip("/")
    url = f"{base}/api/3/action/{acao}?{urllib.parse.urlencode(params)}"
    resp = json.loads(_get(url))
    if not resp.get("success"):
        raise RuntimeError(f"CKAN recusou {acao}: {resp.get('error')}")
    return resp["result"]


def _resumo_conjunto(p: dict) -> dict:
    return {
        "nome": p.get("name"), "titulo": p.get("title"), "licenca": p.get("license_title") or p.get("license_id"),
        "organizacao": (p.get("organization") or {}).get("title"), "modificado": p.get("metadata_modified"),
        "descricao": (p.get("notes") or "").strip(),
        "recursos": [{"id": r.get("id"), "nome": r.get("name"), "formato": (r.get("format") or "").lower(),
                      "url": r.get("url"), "modificado": r.get("last_modified") or r.get("created"),
                      "tamanho": r.get("size"), "descricao": (r.get("description") or "").strip()}
                     for r in p.get("resources", [])],
    }


def buscar(portal: str, termo: str, linhas: int = 20) -> List[dict]:
    """Conjuntos que casam com o termo, com licença e lista de recursos."""
    return [_resumo_conjunto(p) for p in _api(portal, "package_search", q=termo, rows=linhas)["results"]]


def conjunto(portal: str, nome: str) -> dict:
    return _resumo_conjunto(_api(portal, "package_show", id=nome))


def baixar(url: str, pasta: Path, max_mb: float = 300) -> Tuple[Path, str, int]:
    """Baixa um recurso para a pasta, com SHA-256. Recusa arquivos acima de max_mb (proteção do disco)."""
    pasta.mkdir(parents=True, exist_ok=True)
    corpo = _get(url)
    if len(corpo) > max_mb * 1e6:
        raise ValueError(f"{url}: {len(corpo) / 1e6:.0f} MB, acima do limite de {max_mb} MB")
    sha = hashlib.sha256(corpo).hexdigest()
    nome = Path(urllib.parse.urlparse(url).path).name or "recurso"
    destino = pasta / f"{sha[:12]}_{nome}"
    if not destino.exists():  # mesmo conteúdo → mesmo arquivo; nada é sobrescrito
        destino.write_bytes(corpo)
    return destino, sha, len(corpo)


def _decodificar(corpo: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return corpo.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("codificação não reconhecida")


def ler_csv(corpo: bytes) -> pd.DataFrame:
    """CSV como texto (sem conversão de tipos), com codificação e separador detectados."""
    texto = _decodificar(corpo)
    try:
        sep = csv.Sniffer().sniff(texto[:65536], delimiters=";,\t|").delimiter
    except csv.Error:
        sep = ";"
    return pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)


def tabelas(caminho: Path) -> Dict[str, pd.DataFrame]:
    """Tabelas de um arquivo baixado: CSV, ZIP com CSVs, Excel ou JSON tabular."""
    suf = caminho.suffix.lower()
    if suf == ".zip":
        out = {}
        with zipfile.ZipFile(caminho) as z:
            for n in z.namelist():
                if n.lower().endswith(".csv"):
                    out[n] = ler_csv(z.read(n))
        return out
    if suf in (".xlsx", ".xls"):
        return {f"{caminho.name}:{k}": v.astype(str) for k, v in pd.read_excel(caminho, sheet_name=None, dtype=str).items()}
    if suf == ".json":
        dados = json.loads(caminho.read_bytes())
        if isinstance(dados, dict):
            dados = next((v for v in dados.values() if isinstance(v, list)), [])
        return {caminho.name: pd.DataFrame(dados).astype(str)}
    return {caminho.name: ler_csv(caminho.read_bytes())}


def _norm(nome: str) -> str:
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def perfil(df: pd.DataFrame, exemplos: int = 3) -> List[dict]:
    """Por coluna: % preenchido, nº de valores distintos, se parece chave e os valores mais comuns."""
    n = len(df)
    out = []
    for col in df.columns:
        v = df[col].astype(str).str.strip()
        cheios = v[~v.str.lower().isin(NULOS)]
        distintos = cheios.nunique()
        out.append({
            "coluna": col, "preenchido_pct": round(100 * len(cheios) / n, 1) if n else 0.0,
            "distintos": int(distintos), "parece_chave": bool(n and len(cheios) == n and distintos == n),
            "exemplos": [str(x) for x in cheios.value_counts().head(exemplos).index],
        })
    return out


def colunas_compartilhadas(tabs: Dict[str, pd.DataFrame]) -> List[dict]:
    """Colunas com o mesmo nome (normalizado) em duas tabelas e quanto os valores se sobrepõem.

    Sobreposição alta sugere um identificador que liga as tabelas; é só um indício,
    a ligação precisa ser confirmada na documentação da fonte.
    """
    nomes = list(tabs)
    out = []
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            cols_b = {_norm(c): c for c in tabs[b].columns}
            for ca in tabs[a].columns:
                cb = cols_b.get(_norm(ca))
                if cb is None:
                    continue
                va = set(tabs[a][ca].astype(str).str.strip()) - {""}
                vb = set(tabs[b][cb].astype(str).str.strip()) - {""}
                if not va or not vb:
                    continue
                inter = len(va & vb)
                out.append({"tabela_a": a, "coluna_a": ca, "tabela_b": b, "coluna_b": cb,
                            "distintos_a": len(va), "distintos_b": len(vb), "em_comum": inter,
                            "cobertura_a_pct": round(100 * inter / len(va), 1)})
    return sorted(out, key=lambda r: -r["em_comum"])


def relatorio(meta: dict, arquivos: List[dict], tabs: Dict[str, pd.DataFrame]) -> str:
    """Relatório em Markdown para avaliação humana dos campos da fonte."""
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = [f"# Perfil da fonte: {meta['titulo']} (`{meta['nome']}`)", "",
         f"- Coletado em: {agora}", f"- Organização: {meta.get('organizacao') or '–'}",
         f"- Licença declarada no portal: {meta.get('licenca') or 'não declarada'}",
         f"- Metadados modificados em: {meta.get('modificado') or '–'}", "",
         "Relatório gerado automaticamente a partir dos arquivos oficiais; não contém interpretação.", "",
         "## Arquivos", "", "| Recurso | Formato | Modificado (portal) | Bytes | SHA-256 |", "|---|---|---|---|---|"]
    for a in arquivos:
        L.append(f"| {a['nome']} | {a['formato']} | {a.get('modificado') or '–'} | {a.get('bytes', '–')} | "
                 f"`{(a.get('sha256') or a.get('erro', '–'))[:16]}` |")
    for nome, df in tabs.items():
        L += ["", f"## Tabela `{nome}`", "", f"{len(df)} linhas, {len(df.columns)} colunas.", "",
              "| Coluna | Preenchido | Distintos | Parece chave | Valores mais comuns |", "|---|---|---|---|---|"]
        for c in perfil(df):
            ex = "; ".join(e.replace("|", "/")[:40] for e in c["exemplos"])
            L.append(f"| {c['coluna']} | {c['preenchido_pct']}% | {c['distintos']} | {'sim' if c['parece_chave'] else ''} | {ex} |")
    comp = colunas_compartilhadas(tabs)
    if comp:
        L += ["", "## Colunas com o mesmo nome em tabelas diferentes (candidatas a ligação)", "",
              "| Tabela A · coluna | Tabela B · coluna | Distintos A | Distintos B | Em comum | % de A em B |", "|---|---|---|---|---|---|"]
        for r in comp[:40]:
            L.append(f"| {r['tabela_a']} · {r['coluna_a']} | {r['tabela_b']} · {r['coluna_b']} | {r['distintos_a']} | "
                     f"{r['distintos_b']} | {r['em_comum']} | {r['cobertura_a_pct']}% |")
    return "\n".join(L) + "\n"


def explorar(portal: str, nome: str, pasta: Optional[Path] = None, max_mb: float = 300) -> Path:
    """Baixa os recursos tabulares do conjunto e grava relatorio.md + metadados.json. Devolve o relatório."""
    meta = conjunto(portal, nome)
    pasta = pasta or config.DATA_DIR / "fontes" / portal / nome
    arquivos, tabs = [], {}
    for r in meta["recursos"]:
        if r["formato"] not in FORMATOS_TABULARES or not r["url"]:
            continue
        item = dict(r)
        try:
            caminho, sha, nbytes = baixar(r["url"], pasta / "brutos", max_mb=max_mb)
            item.update(arquivo=str(caminho), sha256=sha, bytes=nbytes)
            for t, df in tabelas(caminho).items():
                tabs[f"{r['nome']} / {t}" if t != caminho.name else r["nome"]] = df
        except Exception as e:  # um recurso quebrado não impede o perfil dos outros
            item["erro"] = f"{type(e).__name__}: {e}"
        arquivos.append(item)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "metadados.json").write_text(json.dumps({"conjunto": meta, "arquivos": arquivos}, ensure_ascii=False, indent=1))
    saida = pasta / "relatorio.md"
    saida.write_text(relatorio(meta, arquivos, tabs), encoding="utf-8")
    return saida
