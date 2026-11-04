"""Catálogo de séries: metadados obrigatórios de cada série.

O catálogo público fica em catalog/series.json (versionado).
Séries importadas de arquivos (ex.: exportações da Macrodados) ficam em
data/catalogo_local.json, que não é versionado nem publicado.
"""
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from . import config

PERIODICIDADES = ("diaria", "mensal", "trimestral", "anual")
USOS = ("publico", "pessoal", "restrito")
MODULOS = {
    "radar_brasil": "Radar Brasil",
    "macroforecast": "MacroForecast",
    "radar_setorial": "Radar Setorial",
    "brasil_mundo": "Brasil x Mundo",
}


@dataclass
class SeriesMeta:
    id: str
    nome: str
    modulo: str
    tema: str
    instituicao: str          # quem produz a estatística
    provedor: str             # de onde adquirimos (bcb_sgs, ibge_sidra, arquivo...)
    codigo: str               # identificador no provedor
    unidade: str
    periodicidade: str
    geografia: str
    licenca: str
    uso: str                  # publico | pessoal | restrito
    descricao: str = ""
    inicio: Optional[str] = None
    metadados_conferidos: bool = False
    extra: Dict = field(default_factory=dict)

    def validate(self) -> None:
        if self.periodicidade not in PERIODICIDADES:
            raise ValueError(f"{self.id}: periodicidade inválida '{self.periodicidade}'")
        if self.uso not in USOS:
            raise ValueError(f"{self.id}: uso inválido '{self.uso}'")
        if self.modulo not in MODULOS:
            raise ValueError(f"{self.id}: módulo inválido '{self.modulo}'")
        for campo in ("id", "nome", "instituicao", "provedor", "codigo", "unidade", "licenca"):
            if not getattr(self, campo):
                raise ValueError(f"{self.id}: campo obrigatório vazio '{campo}'")

    def to_dict(self) -> Dict:
        return asdict(self)


def _load_file(path) -> List[SeriesMeta]:
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    metas = [SeriesMeta(**item) for item in items]
    for m in metas:
        m.validate()
    return metas


def load_catalog() -> Dict[str, SeriesMeta]:
    metas = _load_file(config.CATALOG_FILE) + _load_file(config.LOCAL_CATALOG_FILE)
    catalog: Dict[str, SeriesMeta] = {}
    for m in metas:
        if m.id in catalog:
            raise ValueError(f"id de série duplicado no catálogo: {m.id}")
        catalog[m.id] = m
    return catalog


def save_local_series(meta: SeriesMeta) -> None:
    """Adiciona ou substitui uma série no catálogo local (importações de arquivo)."""
    meta.validate()
    items = []
    if config.LOCAL_CATALOG_FILE.exists():
        items = json.loads(config.LOCAL_CATALOG_FILE.read_text(encoding="utf-8"))
    public_ids = {m.id for m in _load_file(config.CATALOG_FILE)}
    if meta.id in public_ids:
        raise ValueError(f"'{meta.id}' já existe no catálogo público; escolha outro id")
    items = [i for i in items if i["id"] != meta.id] + [meta.to_dict()]
    config.LOCAL_CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.LOCAL_CATALOG_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
