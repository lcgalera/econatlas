"""Relatório de oportunidades: HTML autocontido (imprimível em PDF pelo navegador) + CSV para revisão.

Separa sempre o que a fonte afirma (confirmado), o que é inferência técnica e o que não foi verificado.
"""
import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from ..providers import aneel_siget as sg
from .evidencia import CONFIRMADO, INFERENCIA, NAO_VERIFICADO

E = lambda s: html.escape(str(s if s is not None else ""))

CSS = """
:root{--ink:#16181d;--ink-2:#454b57;--muted:#6b7280;--rule:#d9dce1;--bg:#fbfaf7;--card:#fff;--ok:#1f6f4a;--ok-bg:#e6f2ec;--inf:#8a5a00;--inf-bg:#fbf1dc;--nv:#5b6270;--nv-bg:#eef0f3;--acc:#1d4f91}
@media (prefers-color-scheme:dark){:root{--ink:#eceae4;--ink-2:#c3c6cc;--muted:#9aa0aa;--rule:#3a3e46;--bg:#15171b;--card:#1d2026;--ok:#7fd1a6;--ok-bg:#183428;--inf:#f0c36b;--inf-bg:#3a2f14;--nv:#b3b8c2;--nv-bg:#2a2e35;--acc:#8fb6ee}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:32px 16px 64px}h1,h2,h3{font-family:"Source Serif 4",Georgia,serif;line-height:1.2}
h1{font-size:34px;margin:4px 0 8px}h2{font-size:22px;margin:40px 0 12px;padding-top:12px;border-top:2px solid var(--ink)}h3{font-size:18px;margin:0 0 6px}
.kicker{font:600 12px/1 "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.lede{color:var(--ink-2);font-size:17px;max-width:760px}.meta{color:var(--muted);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-weight:600;color:var(--ink-2);border-bottom:1px solid var(--ink)}td.r,th.r{text-align:right;font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}.box{background:var(--card);border:1px solid var(--rule);padding:12px 14px}
.big{font:600 28px/1.1 "Source Serif 4",Georgia,serif}.card{background:var(--card);border:1px solid var(--rule);padding:16px 18px;margin:14px 0;break-inside:avoid}
.tag{display:inline-block;font:600 11px/1.6 "IBM Plex Mono",monospace;padding:0 6px;border-radius:3px;margin-right:6px;white-space:nowrap}
.ok{color:var(--ok);background:var(--ok-bg)}.inf{color:var(--inf);background:var(--inf-bg)}.nv{color:var(--nv);background:var(--nv-bg)}
.score{float:right;text-align:right}.score b{font:600 26px/1 "Source Serif 4",Georgia,serif;display:block}
ul.ev{margin:6px 0 10px;padding-left:18px}ul.ev li{margin:2px 0}.small{font-size:12.5px;color:var(--muted)}a{color:var(--acc)}
.aside{border-left:3px solid var(--ink);padding:4px 12px;color:var(--ink-2);background:var(--card)}
@media print{body{background:#fff}.wrap{padding:0}.card{border-color:#999}h2{break-after:avoid}}
@media (max-width:600px){h1{font-size:26px}.score{float:none;text-align:left;margin-bottom:6px}}
"""


def precisao_medida(caminho: Optional[Path] = None) -> str:
    """Frase com a precisão das avaliações humanas ALEATÓRIAS registradas (as enviesadas não entram)."""
    from math import sqrt
    from .. import config
    caminho = caminho or config.ROOT / "avaliacoes" / "siget_relevancia.csv"
    if not Path(caminho).exists():
        return "Ainda não há avaliação humana aleatória registrada."
    a = pd.read_csv(caminho, dtype=str).fillna("")
    a = a[a.avaliacao.str.contains("aleatoria")]
    k, n = int((a.resultado == "s").sum()), int(a.resultado.isin(["s", "n"]).sum())
    if not n:
        return "Ainda não há avaliação humana aleatória registrada."
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (f"{p:.0%} numa amostra aleatória de {n} (intervalo de 95%: {c - h:.0%} a {c + h:.0%}), "
            f"avaliada por quem construiu o produto. Ainda não avaliada por compradores.")


def _lista(evs: pd.DataFrame, nome_cat: dict, classe: str, rotulo: str, por_categoria: int = 2) -> str:
    if evs.empty:
        return ""
    evs = (evs.drop_duplicates(["categoria", "detalhe"]).assign(_o=(evs.origem != "campo").astype(int))
           .sort_values(["categoria", "_o"]).groupby("categoria").head(por_categoria))
    itens = "".join(f"<li><span class='tag {classe}'>{rotulo}</span><b>{E(nome_cat.get(r.categoria, r.categoria))}</b>: "
                    f"{E(r.detalhe)} <span class='small'>({E(r.regra)})</span></li>"
                    for r in evs.drop_duplicates(["categoria", "detalhe"]).itertuples())
    return f"<ul class='ev'>{itens}</ul>"


def _tabela_contagem(s: pd.Series, titulo: str, n: int = 10) -> str:
    c = s.value_counts().head(n)
    linhas = "".join(f"<tr><td>{E(k)}</td><td class='r'>{v}</td></tr>" for k, v in c.items())
    return f"<div class='box'><div class='kicker'>{E(titulo)}</div><table>{linhas}</table></div>"


def _secao_mudancas(eventos: Optional[pd.DataFrame], op: pd.DataFrame) -> str:
    """'O que mudou': eventos da última coleta para os empreendimentos do relatório (e os novos)."""
    if eventos is None or eventos.attrs.get("coleta_id") is None:
        return ("<p class='small'>O histórico ainda não foi iniciado. Rode <code>econatlas siget-atualizar</code> a cada coleta "
                "para ver aqui o que mudou de uma vez para a outra.</p>")
    quando = (eventos.attrs.get("coletado_em") or "")[:10]
    if not eventos.attrs.get("anterior_em"):
        return (f"<p class='small'>Primeira coleta registrada em {E(quando)}: é a linha de base. A partir da próxima coleta, "
                f"esta seção mostra empreendimentos novos e mudanças de situação, datas, obras e equipamentos.</p>")
    ev = eventos[eventos.id_aneel.isin(op.id_aneel)]
    antes = (eventos.attrs.get("anterior_em") or "")[:10]
    if ev.empty:
        return f"<p class='small'>Nenhuma mudança nos empreendimentos deste relatório entre {E(antes)} e {E(quando)}.</p>"
    nomes = op.set_index("id_aneel").nome
    linhas = "".join(
        f"<tr><td>{E(r.id_ons)}</td><td>{E(nomes.get(r.id_aneel, ''))}</td><td>"
        + ("<span class='tag ok'>novo</span>" if r.tipo == "novo" else E(r.rotulo))
        + f"</td><td>{E(r.antes)}</td><td>{E(r.depois)}</td></tr>" for r in ev.itertuples())
    return (f"<p class='small'>Coleta de {E(quando)} comparada com a de {E(antes)}: {ev.id_aneel.nunique()} empreendimentos com mudança.</p>"
            f"<div style='overflow-x:auto'><table><tr><th>Id ONS</th><th>Empreendimento</th><th>O que mudou</th><th>Antes</th><th>Depois</th></tr>{linhas}</table></div>")


def gerar(op: pd.DataFrame, ev: pd.DataFrame, cats: dict, perfil: dict, pasta: Path, top: int = 30,
          hoje: Optional[pd.Timestamp] = None, fontes: Optional[dict] = None,
          eventos: Optional[pd.DataFrame] = None) -> dict:
    """Grava oportunidades.csv, evidencias.csv e relatorio.html na pasta. Devolve os caminhos."""
    hoje = hoje or pd.Timestamp.today().normalize()
    pasta.mkdir(parents=True, exist_ok=True)
    nome_cat = {c["id"]: c["nome"] for c in cats["categorias"]}
    ev_op = ev[ev.id_aneel.isin(op.id_aneel)]
    cols = ["score", "nivel_evidencia", "id_aneel", "id_ons", "nome", "concessionaria", "cnpj", "contrato", "ufs",
            "operacao_ato_legal", "meses_ate_operacao", "origem", "categorias_confirmadas", "categorias_inferidas", "tensoes_kv",
            "explicacao_score", "alerta_texto", "ato", "ato_link", "descricao"]
    op[cols].to_csv(pasta / "oportunidades.csv", index=False, encoding="utf-8-sig")  # BOM: Excel abre os acentos certos
    ev_op.assign(categoria_nome=ev_op.categoria.map(nome_cat)).to_csv(pasta / "evidencias.csv", index=False, encoding="utf-8-sig")

    conf = op[op.nivel_evidencia == "confirmado"]
    ev_perfil = ev_op[ev_op.categoria.isin(perfil["categorias"])]
    cat_conf = ev_perfil[ev_perfil.nivel == CONFIRMADO].drop_duplicates(["id_aneel", "categoria"]).categoria.map(nome_cat)
    ano = sg.data(op.operacao_ato_legal).dt.year.astype("Int64").astype(str)
    gerado = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    fontes_txt = ", ".join(f"{E(v)}" for v in (fontes or {}).values() if v)

    mudou = {}
    if eventos is not None and eventos.attrs.get("anterior_em"):
        for r in eventos.itertuples():
            mudou.setdefault(r.id_aneel, set()).add("novo" if r.tipo == "novo" else r.rotulo)
    cards = []
    for r in op.head(top).itertuples():
        evs = ev_op[ev_op.id_aneel == r.id_aneel]
        perfil_ev = evs[evs.categoria.isin(perfil["categorias"])]
        ja_conf = set(perfil_ev[perfil_ev.nivel == CONFIRMADO].categoria)
        perfil_ev = perfil_ev[(perfil_ev.nivel == CONFIRMADO) | ~perfil_ev.categoria.isin(ja_conf)]
        alerta = (f"<p class='aside' style='margin:8px 0'><b>Atenção:</b> a descrição oficial contém “{E(r.alerta_texto)}”. "
                  f"Confira a situação antes de abordar o comprador.</p>") if r.alerta_texto else ""
        ato = (f" · Ato: <a href='{E(r.ato_link)}'>{E(r.ato)}</a>" if r.ato else "")
        cards.append(f"""
<div class="card"><div class="score"><b>{r.score}</b><span class="small">score</span></div>
<span class="tag {'ok' if r.nivel_evidencia == 'confirmado' else 'inf'}">{E(r.nivel_evidencia)}</span>{''.join(f"<span class='tag inf'>{E(m)}</span>" for m in sorted(mudou.get(r.id_aneel, [])))}<span class="small">{E(r.id_ons)}</span>
<h3>{E(r.nome)}</h3>
<div class="meta">{E(r.concessionaria)} (CNPJ {E(r.cnpj)}, contrato {E(r.contrato)}) · UF {E(r.ufs or '–')} ·
operação pelo ato legal em <b>{E(r.operacao_ato_legal)}</b> ({r.meses_ate_operacao:g} meses) · {E(r.origem)}{ato}</div>
<p class="small" style="margin:8px 0">{E(r.descricao)}</p>{alerta}
<div class="kicker" style="margin-top:8px">O que a fonte afirma</div>{_lista(perfil_ev[perfil_ev.nivel == CONFIRMADO], nome_cat, 'ok', 'confirmado') or "<p class='small'>Nada confirmado para as categorias do perfil.</p>"}
{('<div class="kicker">Inferência técnica (a fonte não cita)</div>' + _lista(perfil_ev[perfil_ev.nivel == INFERENCIA], nome_cat, 'inf', 'inferência')) if (perfil_ev.nivel == INFERENCIA).any() else ''}
{('<div class="kicker">Não verificado</div>' + _lista(perfil_ev[perfil_ev.nivel == NAO_VERIFICADO], nome_cat, 'nv', 'não verificado')) if (perfil_ev.nivel == NAO_VERIFICADO).any() else ''}
<p class="small"><b>Por que este score:</b> {E(r.explicacao_score)}</p></div>""")

    tabela = "".join(f"<tr><td class='r'>{r.score}</td><td>{E(r.id_ons)}</td><td>{E(r.nome)}</td><td>{E(r.concessionaria)}</td>"
                     f"<td>{E(r.ufs)}</td><td>{E(r.operacao_ato_legal)}</td><td>{E(r.categorias_confirmadas or '(inferência) ' + r.categorias_inferidas)}</td></tr>"
                     for r in op.itertuples())
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>rotzx — Radar de oportunidades</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="wrap">
<div class="kicker">rotzx · radar de oportunidades · transmissão de energia</div>
<h1>Empreendimentos de transmissão com fornecimento de equipamento em andamento</h1>
<p class="lede">Perfil: <b>{E(perfil['nome'])}</b>. Lista gerada a partir dos dados oficiais do SIGET (ANEEL), com a evidência de cada
categoria separada entre o que a fonte afirma e o que é inferência. Data de referência: {hoje:%d/%m/%Y}.</p>
<p class="aside"><b>Como ler.</b> Empreendimento não é pedido de compra. "Confirmado" quer dizer que a fonte oficial descreve o equipamento numa obra
em andamento, não que a compra está aberta ou que ainda não foi feita. As datas são as de operação fixadas no <b>ato legal</b>,
não a previsão da transmissora. O <b>score</b> (0–100) só ordena o que olhar primeiro: não é probabilidade de venda.</p>

<h2>Resumo</h2>
<div class="grid">
<div class="box"><div class="kicker">Oportunidades</div><div class="big">{len(op)}</div><div class="small">{len(conf)} com categoria confirmada na fonte; {len(op) - len(conf)} só por inferência</div></div>
<div class="box"><div class="kicker">Concessionárias</div><div class="big">{op.concessionaria.nunique()}</div><div class="small">com ao menos uma oportunidade</div></div>
<div class="box"><div class="kicker">Origem</div><div class="big">{(op.origem.str.startswith('aut')).sum()}</div><div class="small">autorizações (reforços e melhorias); {(~op.origem.str.startswith('aut')).sum()} de contrato de concessão</div></div>
</div><div class="grid" style="margin-top:16px">
{_tabela_contagem(cat_conf, 'Categorias do perfil confirmadas')}
{_tabela_contagem(op.concessionaria, 'Concessionárias')}
{_tabela_contagem(op.ufs.str.split(',').explode().replace('', '–'), 'UF das subestações')}
{_tabela_contagem(ano, 'Ano de operação (ato legal)')}
</div>

<h2>O que mudou desde a última coleta</h2>
{_secao_mudancas(eventos, op)}

<h2>As {min(top, len(op))} primeiras, com evidências</h2>
{''.join(cards)}

<h2>Lista completa</h2>
<div style="overflow-x:auto"><table><tr><th class="r">Score</th><th>Id ONS</th><th>Empreendimento</th><th>Concessionária</th><th>UF</th><th>Operação</th><th>Categorias</th></tr>{tabela}</table></div>

<h2>Método e limitações</h2>
<ul>
<li><b>Elegível:</b> empreendimento "em andamento", com concessionária identificada, com evidência para uma categoria do perfil e com a operação pelo ato legal a pelo menos a janela da categoria ({', '.join(sorted({str(c['janela_meses']) for c in cats['categorias']}))} meses; hipótese a validar).</li>
<li><b>Confirmado:</b> módulo de equipamento ou de manobra novo (obra de instalação ou ampliação) com o tipo ou a quantidade declarados, ou texto oficial com verbo de fornecimento ("substituição", "instalação", "novo"…) seguido do equipamento.</li>
<li><b>Inferência técnica:</b> bay novo → para-raios e transformadores de instrumento; módulo de manobra sem quantidade → disjuntores e seccionadoras; linha nova → materiais de linha. A fonte não cita esses itens.</li>
<li><b>Score</b> = 40% compatibilidade + 25% estágio + 20% qualidade da evidência + 15% geografia. Só inferência: teto de 60. Detalhes em <code>docs/06-motor-de-oportunidades.md</code>.</li>
<li><b>Limites da fonte:</b> sem previsão da transmissora, sem município, potência declarada em cerca de metade dos equipamentos, quantidades de manobra raras. Lotes de leilão ainda não assinados não aparecem.</li>
<li><b>Precisão medida:</b> {E(precisao_medida())}</li>
</ul>
<p class="small">Gerado em {gerado} por <code>econatlas oportunidades</code> (categorias {E(cats.get('versao'))}). Arquivos da fonte: {fontes_txt}.<br>
Contém dados da ANEEL (SIGET, Portal de Dados Abertos), disponibilizados sob a licença ODbL. Esta lista é uma base derivada sob a mesma licença.</p>
</div></body></html>"""
    (pasta / "relatorio.html").write_text(doc, encoding="utf-8")
    return {"html": pasta / "relatorio.html", "csv": pasta / "oportunidades.csv", "evidencias": pasta / "evidencias.csv"}
