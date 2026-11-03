"""API HTTP do EconAtlas (FastAPI). Também serve a interface em web/.

Toda resposta com números inclui: série, fonte, versão (vintage), data de coleta
e transformação aplicada, para que qualquer valor exibido seja rastreável.
A montagem dos dados fica em payloads.py, compartilhada com o build público.
"""
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import catalog as cat
from . import cli, config, payloads, storage

app = FastAPI(title="EconAtlas", version="0.1.0")


def _catalog():
    return cat.load_catalog()


@app.get("/api/modulos")
def modulos():
    return [{"id": k, "nome": v} for k, v in cat.MODULOS.items()]


@app.get("/api/catalogo")
def catalogo():
    return payloads.catalogo(storage.connect(), _catalog())


@app.get("/api/series/{series_id}")
def series(series_id: str, transform: str = "nivel", inicio: Optional[str] = None, fim: Optional[str] = None):
    try:
        return payloads.series(storage.connect(), _catalog(), series_id, transform, inicio, fim)
    except KeyError:
        raise HTTPException(404, f"série desconhecida: {series_id}")
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/series/{series_id}/versoes")
def versoes(series_id: str):
    if series_id not in _catalog():
        raise HTTPException(404, f"série desconhecida: {series_id}")
    return payloads.versoes(storage.connect(), series_id)


@app.get("/api/qualidade")
def qualidade():
    return payloads.qualidade(storage.connect(), _catalog())


@app.get("/api/previsoes/ipca")
def previsoes_ipca():
    return payloads.previsoes_ipca(storage.connect())


@app.get("/api/analises/setores")
def analises_setores():
    """Todas as análises de indicadores antecedentes já executadas, uma por setor."""
    from .analysis import leading
    out = payloads.analises_setores(leading.SETORES)
    if not out:
        raise HTTPException(404, "análise ainda não executada; rode `python -m econatlas analisar-setor`")
    return out


@app.get("/api/previsoes/setoriais")
def previsoes_setoriais():
    from .forecast import setorial
    return payloads.previsoes_setoriais(storage.connect(), setorial.SETORES_PREVISAO)


@app.post("/api/atualizar")
def atualizar():
    """Atualiza as séries públicas (uso local)."""
    return cli.update()


app.mount("/static", StaticFiles(directory=config.WEB_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(config.WEB_DIR / "index.html")
