"""Histórico do radar (Fase 2): uma versão por empreendimento a cada coleta do SIGET e eventos de mudança.

Mesmo princípio das séries (storage.py, D3): só acrescenta, nunca reescreve, e não cria versão se nada mudou.
  siget_coletas       uma linha por coleta que trouxe arquivos diferentes (SHA-256 de cada arquivo)
  siget_versoes       os campos acompanhados de cada empreendimento naquela coleta (+ hash da linha)
  siget_eventos       diferenças entre a coleta e a anterior: novo, saiu da fonte, mudança de campo
Os gatilhos impedem UPDATE e DELETE, como no registro de previsões (D10).
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Optional

import pandas as pd

ACOMPANHADOS = {  # campo da visão por empreendimento → rótulo do evento
    "situacao": "situação",
    "operacao_ato_legal": "data de operação (ato legal)",
    "conclusao_ato_legal": "data de conclusão (ato legal)",
    "operacao_efetiva": "operação efetiva",
    "concessionaria": "concessionária",
    "contrato": "contrato",
    "n_obras": "número de obras",
    "n_obras_em_andamento": "obras em andamento",
    "equipamentos": "equipamentos em obras em andamento",
    "ato": "ato autorizativo mais recente",
    "nome": "nome",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS siget_coletas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coletado_em TEXT NOT NULL,
    gerado_em TEXT,                -- DatGeracaoConjuntoDados do arquivo de empreendimentos
    arquivos TEXT NOT NULL,        -- JSON {tabela: nome do arquivo com prefixo SHA-256}
    assinatura TEXT NOT NULL UNIQUE,  -- SHA-256 do conjunto de arquivos: a mesma coleta não entra duas vezes
    n_empreendimentos INTEGER NOT NULL,
    n_eventos INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS siget_versoes (
    coleta_id INTEGER NOT NULL REFERENCES siget_coletas(id),
    id_aneel TEXT NOT NULL,
    dados TEXT NOT NULL,           -- JSON com os campos acompanhados
    hash TEXT NOT NULL,
    PRIMARY KEY (coleta_id, id_aneel)
);
CREATE TABLE IF NOT EXISTS siget_eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coleta_id INTEGER NOT NULL REFERENCES siget_coletas(id),
    id_aneel TEXT NOT NULL,
    id_ons TEXT,
    tipo TEXT NOT NULL,            -- novo | saiu_da_fonte | mudou
    campo TEXT,
    antes TEXT,
    depois TEXT
);
CREATE INDEX IF NOT EXISTS ix_siget_eventos ON siget_eventos(coleta_id, id_aneel);
CREATE TRIGGER IF NOT EXISTS siget_versoes_sem_update BEFORE UPDATE ON siget_versoes
BEGIN SELECT RAISE(ABORT, 'histórico do SIGET só aceita acréscimos'); END;
CREATE TRIGGER IF NOT EXISTS siget_versoes_sem_delete BEFORE DELETE ON siget_versoes
BEGIN SELECT RAISE(ABORT, 'histórico do SIGET só aceita acréscimos'); END;
CREATE TRIGGER IF NOT EXISTS siget_eventos_sem_update BEFORE UPDATE ON siget_eventos
BEGIN SELECT RAISE(ABORT, 'histórico do SIGET só aceita acréscimos'); END;
CREATE TRIGGER IF NOT EXISTS siget_eventos_sem_delete BEFORE DELETE ON siget_eventos
BEGIN SELECT RAISE(ABORT, 'histórico do SIGET só aceita acréscimos'); END;
"""


def ensure_schema(conn) -> None:
    conn.executescript(SCHEMA)


def _linha(r: pd.Series) -> Dict[str, str]:
    return {c: str(r.get(c, "") if pd.notna(r.get(c, "")) else "") for c in ACOMPANHADOS}


def _hash(d: Dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ultima_versao(conn) -> Optional[int]:
    r = conn.execute("SELECT MAX(id) FROM siget_coletas").fetchone()
    return r[0]


def _versao(conn, coleta_id: int) -> Dict[str, dict]:
    rows = conn.execute("SELECT id_aneel, dados, hash FROM siget_versoes WHERE coleta_id = ?", (coleta_id,)).fetchall()
    return {r[0]: {"dados": json.loads(r[1]), "hash": r[2]} for r in rows}


def registrar(conn, emp: pd.DataFrame, agora: Optional[datetime] = None) -> Dict:
    """Grava a visão por empreendimento como nova coleta e os eventos em relação à anterior.

    Se o conjunto de arquivos for o mesmo da última coleta registrada, nada é gravado (status 'sem_alteracao').
    A primeira coleta é a linha de base: grava as versões, sem eventos.
    """
    ensure_schema(conn)
    fontes = emp.attrs.get("fontes") or {}
    assinatura = hashlib.sha256(json.dumps(fontes, sort_keys=True).encode()).hexdigest()
    ja = conn.execute("SELECT id FROM siget_coletas WHERE assinatura = ?", (assinatura,)).fetchone()
    if ja:
        return {"status": "sem_alteracao", "coleta_id": ja[0], "eventos": 0}
    anterior = ultima_versao(conn)
    velhas = _versao(conn, anterior) if anterior else {}
    novas = {}
    for _, r in emp.iterrows():
        d = _linha(r)
        novas[str(r.id_aneel)] = {"dados": d, "hash": _hash(d), "id_ons": str(r.get("id_ons", ""))}
    eventos = []
    if anterior:
        for i, n in novas.items():
            v = velhas.get(i)
            if v is None:
                eventos.append((i, n["id_ons"], "novo", None, None, n["dados"]["situacao"]))
            elif v["hash"] != n["hash"]:
                for campo in ACOMPANHADOS:
                    a, b = v["dados"].get(campo, ""), n["dados"].get(campo, "")
                    if a != b:
                        eventos.append((i, n["id_ons"], "mudou", campo, a, b))
        for i in set(velhas) - set(novas):
            eventos.append((i, None, "saiu_da_fonte", None, velhas[i]["dados"].get("situacao", ""), None))
    agora = agora or datetime.now(timezone.utc)
    gerado = emp.attrs.get("gerado_em")
    cur = conn.execute(
        "INSERT INTO siget_coletas (coletado_em, gerado_em, arquivos, assinatura, n_empreendimentos, n_eventos) VALUES (?,?,?,?,?,?)",
        (agora.isoformat(timespec="seconds"), gerado, json.dumps(fontes, ensure_ascii=False), assinatura, len(novas), len(eventos)))
    cid = cur.lastrowid
    conn.executemany("INSERT INTO siget_versoes (coleta_id, id_aneel, dados, hash) VALUES (?,?,?,?)",
                     [(cid, i, json.dumps(n["dados"], ensure_ascii=False), n["hash"]) for i, n in novas.items()])
    conn.executemany("INSERT INTO siget_eventos (coleta_id, id_aneel, id_ons, tipo, campo, antes, depois) VALUES (?,?,?,?,?,?,?)",
                     [(cid, *e) for e in eventos])
    conn.commit()
    return {"status": "linha_de_base" if not anterior else "nova_coleta", "coleta_id": cid, "anterior": anterior,
            "eventos": len(eventos)}


def eventos(conn, coleta_id: Optional[int] = None) -> pd.DataFrame:
    """Eventos da coleta pedida (padrão: a mais recente), com a data da coleta e da anterior."""
    ensure_schema(conn)
    coleta_id = coleta_id or ultima_versao(conn)
    if not coleta_id:
        return pd.DataFrame(columns=["id_aneel", "id_ons", "tipo", "campo", "rotulo", "antes", "depois"])
    df = pd.read_sql_query("SELECT id_aneel, id_ons, tipo, campo, antes, depois FROM siget_eventos WHERE coleta_id = ? ORDER BY id",
                           conn, params=(coleta_id,))
    df["rotulo"] = df.campo.map(ACOMPANHADOS).fillna("")
    meta = conn.execute("SELECT coletado_em, (SELECT coletado_em FROM siget_coletas WHERE id < ? ORDER BY id DESC LIMIT 1) "
                        "FROM siget_coletas WHERE id = ?", (coleta_id, coleta_id)).fetchone()
    df.attrs.update(coleta_id=coleta_id, coletado_em=meta[0] if meta else None, anterior_em=meta[1] if meta else None)
    return df


# ---------- persistência em CSV (versionada no git; o GitHub Actions monta um banco novo a cada execução, D23) ----------
from pathlib import Path  # noqa: E402

from .. import config  # noqa: E402

DIR = config.ROOT / "historico"
COLETAS_COLS = ["id", "coletado_em", "gerado_em", "assinatura", "n_empreendimentos", "n_eventos", "arquivos"]
EVENTOS_COLS = ["coleta_id", "id_aneel", "id_ons", "tipo", "campo", "antes", "depois"]
ESTADO_COLS = ["coleta_id", "id_aneel", "hash"] + list(ACOMPANHADOS)


class HistoricoAlterado(RuntimeError):
    """Uma linha antiga do CSV não confere com o banco: o histórico só aceita acréscimos."""


def _ler(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, dtype=str, keep_default_na=False) if p.exists() else pd.DataFrame()


def _acrescentar(p: Path, novo: pd.DataFrame, cols: list) -> int:
    """Grava `novo` mantendo as linhas existentes byte a byte; falha se alguma divergir. Devolve quantas entraram."""
    novo = novo[cols].astype(str).replace({"None": "", "nan": ""})
    velho = _ler(p)
    if len(velho):
        if len(velho) > len(novo) or not velho[cols].equals(novo.head(len(velho)).reset_index(drop=True)):
            raise HistoricoAlterado(f"{p.name}: linhas antigas divergem do banco")
    extra = novo.iloc[len(velho):]
    if not p.exists():
        pd.DataFrame(columns=cols).to_csv(p, index=False, lineterminator="\n")  # cabeçalho, mesmo sem linhas
    if len(extra):
        extra.to_csv(p, mode="a", header=False, index=False, lineterminator="\n")
    return len(extra)


def exportar(conn, pasta: Optional[Path] = None) -> Dict[str, int]:
    """Acrescenta coletas e eventos novos aos CSVs e regrava o estado da última coleta (arquivo derivado)."""
    ensure_schema(conn)
    pasta = Path(pasta or DIR)
    pasta.mkdir(parents=True, exist_ok=True)
    col = pd.read_sql_query(f"SELECT {', '.join(COLETAS_COLS)} FROM siget_coletas ORDER BY id", conn)
    ev = pd.read_sql_query(f"SELECT {', '.join(EVENTOS_COLS)} FROM siget_eventos ORDER BY id", conn)
    out = {"coletas": _acrescentar(pasta / "siget_coletas.csv", col, COLETAS_COLS),
           "eventos": _acrescentar(pasta / "siget_eventos.csv", ev, EVENTOS_COLS)}
    ult = ultima_versao(conn)
    if ult:
        linhas = [{"coleta_id": ult, "id_aneel": i, "hash": v["hash"], **v["dados"]} for i, v in sorted(_versao(conn, ult).items(),
                  key=lambda kv: (len(kv[0]), kv[0]))]
        pd.DataFrame(linhas, columns=ESTADO_COLS).to_csv(pasta / "siget_estado.csv", index=False, lineterminator="\n")
        out["estado"] = len(linhas)
    return out


def importar(conn, pasta: Optional[Path] = None) -> Dict[str, int]:
    """Carrega os CSVs num banco sem histórico: coletas, eventos e o estado da última coleta (para comparar a próxima)."""
    ensure_schema(conn)
    pasta = Path(pasta or DIR)
    if ultima_versao(conn):
        return {"status": "banco_ja_tem_historico"}
    col, ev, est = (_ler(pasta / f) for f in ("siget_coletas.csv", "siget_eventos.csv", "siget_estado.csv"))
    if col.empty:
        return {"status": "sem_historico"}
    conn.executemany(f"INSERT INTO siget_coletas ({', '.join(COLETAS_COLS)}) VALUES ({','.join('?' * len(COLETAS_COLS))})",
                     col[COLETAS_COLS].replace({"": None}).values.tolist())
    if len(ev):
        conn.executemany(f"INSERT INTO siget_eventos ({', '.join(EVENTOS_COLS)}) VALUES ({','.join('?' * len(EVENTOS_COLS))})",
                         ev[EVENTOS_COLS].replace({"": None}).values.tolist())
    if len(est):
        conn.executemany("INSERT INTO siget_versoes (coleta_id, id_aneel, dados, hash) VALUES (?,?,?,?)",
                         [(r["coleta_id"], r["id_aneel"], json.dumps({c: r[c] for c in ACOMPANHADOS}, ensure_ascii=False), r["hash"])
                          for _, r in est.iterrows()])
    conn.commit()
    return {"status": "importado", "coletas": len(col), "eventos": len(ev), "estado": len(est)}
