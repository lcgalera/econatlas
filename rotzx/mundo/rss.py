"""Feeds RSS de veículos em português: fonte principal das manchetes do globo (D40).

RSS existe para distribuir manchetes com link; aqui entram só título, veículo, data e link (o texto fica no site do veículo).
Cada feed que falha fica anotado e não derruba os outros. O XML é lido com a biblioteca padrão (expat), que não resolve
entidades externas; feeds são dado externo e nada neles é executado.
"""
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Dict, List, Tuple

from .. import config
from .gdelt import categorias

FEEDS = [
    ("g1 Mundo", "https://g1.globo.com/rss/g1/mundo/"),
    ("g1 Economia", "https://g1.globo.com/rss/g1/economia/"),
    ("Folha Mundo", "https://feeds.folha.uol.com.br/mundo/rss091.xml"),
    ("Folha Mercado", "https://feeds.folha.uol.com.br/mercado/rss091.xml"),
    ("BBC News Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml"),
    ("DW Brasil", "https://rss.dw.com/xml/rss-br-all"),
    ("Agência Brasil Internacional", "https://agenciabrasil.ebc.com.br/rss/internacional/feed.xml"),
    ("Agência Brasil Economia", "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml"),
    ("CNN Brasil Internacional", "https://www.cnnbrasil.com.br/internacional/feed/"),
    ("RFI Brasil", "https://www.rfi.fr/br/rss"),
]
_ATOM = "{http://www.w3.org/2005/Atom}"


def _data(txt: str) -> str:
    """AAAAMMDD a partir de RFC 822 (RSS) ou ISO 8601 (Atom); vazio se não der para ler."""
    txt = (txt or "").strip()
    if not txt:
        return ""
    try:
        return parsedate_to_datetime(txt).strftime("%Y%m%d")
    except (TypeError, ValueError, IndexError):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", txt)
        return "".join(m.groups()) if m else ""


def ler(xml: bytes, veiculo: str) -> List[dict]:
    """Itens de um feed RSS 2.0 ou Atom: título, link, data, veículo e categorias (palavras-chave no título)."""
    raiz = ET.fromstring(xml)
    itens = raiz.findall(".//item") or raiz.findall(f".//{_ATOM}entry")
    out = []
    for it in itens:
        titulo = (it.findtext("title") or it.findtext(f"{_ATOM}title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link:
            a = it.find(f"{_ATOM}link")
            link = a.get("href", "") if a is not None else ""
        data = _data(it.findtext("pubDate") or it.findtext(f"{_ATOM}updated") or it.findtext(f"{_ATOM}published") or "")
        titulo = re.sub(r"\s+", " ", titulo)
        if titulo and link.startswith(("http://", "https://")):
            out.append({"titulo": titulo, "url": link, "veiculo": veiculo, "data": data,
                        "dominio": urllib.parse.urlparse(link).netloc, "categorias": categorias(titulo)})
    return out


def coletar(feeds: List[Tuple[str, str]] = FEEDS, pausa: float = 1.0) -> Tuple[List[dict], Dict[str, str]]:
    """Todos os itens dos feeds e as falhas por feed."""
    itens, falhas = [], {}
    for nome, url in feeds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"})
            with urllib.request.urlopen(req, timeout=30) as r:
                itens += ler(r.read(), nome)
        except (OSError, ET.ParseError) as e:
            falhas[nome] = f"{type(e).__name__}: {e}"[:160]
        time.sleep(pausa)
    return itens, falhas
