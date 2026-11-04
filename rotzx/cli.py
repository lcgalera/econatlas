"""Linha de comando do rotzx.

Exemplos:
  python -m rotzx atualizar                  # baixa todas as séries públicas
  python -m rotzx atualizar ipca_mensal      # só uma série
  python -m rotzx importar export.csv --id md_icms --nome "ICMS – SP" --unidade "R$ mil" \
      --periodicidade mensal --instituicao "Sefaz-SP" --fonte "Macrodados (exportação)"
  python -m rotzx qualidade
  python -m rotzx servir                     # abre a interface em http://127.0.0.1:8000
"""
import argparse
import shutil
import sys
from pathlib import Path

from . import catalog as cat
from . import config, quality, storage
from .providers import get_provider


def update(ids=None, conn=None):
    catalog = cat.load_catalog()
    conn = conn or storage.connect()
    targets = [catalog[i] for i in ids] if ids else [m for m in catalog.values() if m.provedor != "arquivo"]
    results = []
    for meta in targets:
        try:
            result = get_provider(meta.provedor).fetch(meta)
            summary = storage.save_fetch(conn, meta, result)
        except Exception as exc:  # uma série com problema não interrompe as demais
            summary = {"series_id": meta.id, "status": "erro", "erro": str(exc)}
        results.append(summary)
        print(f"  {summary['series_id']:<24} {summary['status']:<14} "
              f"{summary.get('n_obs', '')} obs  {summary.get('erro', '')}", file=sys.stderr)
    return results


def predict():
    """Rotina mensal do IPCA: atualiza IPCA e Focus e registra as previsões (imutáveis)."""
    from .forecast import focus, registry
    conn = storage.connect()
    update(["ipca_mensal"], conn)
    focus.update(conn)
    return registry.register_ipca(conn)


def predict_sectors(pessoal: bool = False):
    """Rotina mensal setorial: atualiza alvo e preditor, registra as previsões (imutáveis) e
    devolve a avaliação das que já têm o dado realizado. Por padrão só séries públicas;
    `pessoal=True` inclui CNI e ABIMAQ (Macrodados), que dependem de importação manual."""
    from .forecast import setorial
    conn = storage.connect()
    update(["selic_mensal", "pim_eletricos"], conn)
    # públicas: registro oficial feito pelo GitHub Actions; --pessoal: só CNI/ABIMAQ, no Mac do Lucas
    setores = setorial.SETORES_PESSOAIS if pessoal else setorial.SETORES_PUBLICOS
    registro = setorial.register(conn, setores)
    rows = [r for r in setorial.evaluated(conn) if r["setor"] in setores]
    return {"registro": registro, "avaliadas": sum(r["realizado"] is not None for r in rows),
            "pendentes": sum(r["realizado"] is None for r in rows), "placar": setorial.scoreboard(rows)}


def calibrate_sectors():
    import json
    from datetime import datetime, timezone
    from .forecast import setorial
    conn = storage.connect()
    out = {"executado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "metodo": "fração das origens desde 2016 em que o realizado caiu dentro da faixa empírica de 80%",
           "setores": {s: setorial.calibration(conn, s) for s in setorial.SETORES_PREVISAO}}
    config.ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
    (config.ANALYSES_DIR / "previsao_setorial_calibracao.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def save_backtest():
    import json
    from .forecast import backtest
    result = backtest.run_ipca(storage.connect())
    config.BACKTEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.BACKTEST_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def analyze_sector(setores=None):
    import json
    from datetime import datetime, timezone
    from .analysis import leading
    conn = storage.connect()
    config.ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for setor in setores or list(leading.SETORES):
        result = leading.run(conn, setor)
        result["executado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        (config.ANALYSES_DIR / f"{setor}_antecedentes.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        results.append(result)
    return results


def import_macrodados(paths, modulo="radar_setorial", tema="outros"):
    """Importa exportações da Macrodados: cada coluna vira uma série de uso pessoal.

    Colunas presentes no manifesto (catalog/macrodados_cesta.json) recebem o código
    md#### como id e os metadados de lá (instituição, tema, unidade, nome legível).
    As demais têm o id derivado do nome da coluna. Nos dois casos, reimportar uma
    exportação mais nova gera uma nova versão (vintage), não uma série duplicada.
    Tema, módulo e descrição editados no catálogo local são preservados.
    """
    import json
    from datetime import datetime
    from .providers import macrodados

    manifest = macrodados.load_manifest(config.MACRODADOS_MANIFEST)
    existing = {}
    if config.LOCAL_CATALOG_FILE.exists():
        existing = {i["id"]: i for i in json.loads(config.LOCAL_CATALOG_FILE.read_text(encoding="utf-8"))}
    ids = []
    for p in paths:
        src = Path(p).expanduser().resolve()
        raw = src.read_bytes()
        series = macrodados.parse_export(raw, src.name)
        dest = config.DATA_DIR / "imports" / "macrodados" / f"{datetime.now():%Y%m%dT%H%M%S}_{src.name}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        for s in series:
            known = manifest.get(macrodados.norm(s.coluna), {})
            sid = "md_" + (known["codigo_md"] if known else macrodados.slug(s.nome))
            prev = existing.get(sid, {})
            meta = cat.SeriesMeta(
                id=sid, nome=known.get("nome", s.nome), modulo=prev.get("modulo", modulo), inicio=known.get("inicio"),
                tema=prev.get("tema", known.get("tema", tema)),
                instituicao=known.get("instituicao", s.instituicao), provedor="arquivo", codigo=str(dest),
                unidade=known.get("unidade", s.unidade), periodicidade=s.periodicidade,
                geografia=prev.get("geografia", "Brasil"), licenca=macrodados.LICENCA, uso="pessoal",
                descricao=prev.get("descricao") or f"Nome na Macrodados: {macrodados.norm(s.coluna)}."
                          + (f" {known['nota']}" if known.get("nota") else ""),
                metadados_conferidos=bool(known),
                extra={**prev.get("extra", {}), "fonte_aquisicao": "Macrodados Web (exportação)",
                       "codigo_md": known.get("codigo_md"), "arquivo_original": src.name,
                       "coluna_data": None, "coluna_valor": s.coluna},
            )
            cat.save_local_series(meta)
            ids.append(sid)
            print(f"  {sid}: {s.periodicidade}, {len(s.data)} obs, unidade '{meta.unidade}', fonte '{meta.instituicao}'"
                  + ("" if known else "  [fora do manifesto: conferir metadados]"), file=sys.stderr)
    return update(ids)


def import_file(args):
    src = Path(args.arquivo).expanduser().resolve()
    dest_dir = config.DATA_DIR / "imports" / args.id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    meta = cat.SeriesMeta(
        id=args.id, nome=args.nome, modulo=args.modulo, tema=args.tema, instituicao=args.instituicao,
        provedor="arquivo", codigo=str(dest), unidade=args.unidade, periodicidade=args.periodicidade,
        geografia=args.geografia, licenca=f"Adquirido via {args.fonte}; termos de uso a confirmar",
        uso=args.uso, descricao=args.descricao, metadados_conferidos=False,
        extra={"fonte_aquisicao": args.fonte, "arquivo_original": src.name,
               "coluna_data": args.coluna_data, "coluna_valor": args.coluna_valor},
    )
    cat.save_local_series(meta)
    update([meta.id])


def main(argv=None):
    p = argparse.ArgumentParser(prog="rotzx")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("atualizar", help="baixa séries dos provedores públicos")
    a.add_argument("ids", nargs="*")

    i = sub.add_parser("importar", help="importa CSV/Excel exportado legalmente")
    i.add_argument("arquivo")
    i.add_argument("--id", required=True)
    i.add_argument("--nome", required=True)
    i.add_argument("--unidade", required=True)
    i.add_argument("--periodicidade", required=True, choices=cat.PERIODICIDADES)
    i.add_argument("--instituicao", required=True, help="quem produz a estatística (ex.: IBGE)")
    i.add_argument("--fonte", default="Macrodados (exportação)", help="como o dado foi adquirido")
    i.add_argument("--uso", default="pessoal", choices=cat.USOS)
    i.add_argument("--modulo", default="radar_brasil", choices=list(cat.MODULOS))
    i.add_argument("--tema", default="outros")
    i.add_argument("--geografia", default="Brasil")
    i.add_argument("--descricao", default="")
    i.add_argument("--coluna-data", default=None)
    i.add_argument("--coluna-valor", default=None)

    md = sub.add_parser("importar-macrodados", help="importa exportações da Macrodados (uma ou várias séries por arquivo)")
    md.add_argument("arquivos", nargs="+")
    md.add_argument("--modulo", default="radar_setorial", choices=list(cat.MODULOS))
    md.add_argument("--tema", default="outros")

    pb = sub.add_parser("publicar", help="gera o site público estático (só dados abertos) em ./site")
    pb.add_argument("--saida", default=None, help="pasta de saída (padrão: ./site)")

    an = sub.add_parser("analisar-setor", help="testa indicadores antecedentes por setor (fora da amostra)")
    an.add_argument("setores", nargs="*", help="eletrico, maquinas, maquinas_abimaq (padrão: todos)")
    sub.add_parser("registro-exportar", help="acrescenta as previsões novas aos CSVs de registro/ (nunca reescreve)")
    sub.add_parser("registro-importar", help="carrega registro/*.csv no banco (ex.: banco novo no GitHub Actions)")
    rv = sub.add_parser("registro-verificar", help="falha se alguma linha antiga do registro mudou (git) ou diverge do banco")
    rv.add_argument("--contra", default="HEAD", help="commit de referência (padrão: HEAD; vazio = só o banco)")

    sub.add_parser("qualidade", help="roda as verificações de qualidade")
    sub.add_parser("prever", help="atualiza IPCA e Focus e registra as previsões do mês (imutáveis)")
    ps = sub.add_parser("prever-setor", help="registra as previsões setoriais do mês (imutáveis) e avalia as vencidas")
    ps.add_argument("--pessoal", action="store_true", help="só CNI e ABIMAQ (Macrodados, uso pessoal, local)")
    sub.add_parser("backtest", help="refaz o backtest do IPCA e salva o resultado (~1–2 min)")
    sub.add_parser("calibrar-setorial", help="mede a cobertura das faixas das previsões setoriais (~5 min)")

    fe = sub.add_parser("fonte-explorar", help="Fase 1: busca um conjunto no portal CKAN (ANEEL) e gera o perfil dos campos")
    fe.add_argument("busca", help="termo de busca (ex.: siget) ou, com --conjunto, ignorado")
    fe.add_argument("--portal", default="aneel", help="aneel ou a URL de outro portal CKAN")
    fe.add_argument("--conjunto", default=None, help="nome do conjunto: baixa os recursos e gera data/fontes/.../relatorio.md")
    fe.add_argument("--max-mb", type=float, default=300, help="tamanho máximo por arquivo baixado")

    sa = sub.add_parser("siget-amostra", help="Fase 1: visão por empreendimento do SIGET e amostra para avaliação manual")
    sa.add_argument("--n", type=int, default=20, help="tamanho da amostra (padrão: 20)")
    sa.add_argument("--aleatoria", action="store_true", help="sorteio entre os elegíveis (sem os da amostra.csv) + planilha de avaliação")
    sa.add_argument("--semente", type=int, default=20261104, help="semente do sorteio (padrão: 20261104)")

    sub.add_parser("siget-atualizar", help="Fase 2: baixa os arquivos do SIGET que mudaram e registra versões e eventos no histórico")
    li = sub.add_parser("leiloes-importar", help="importa a planilha oficial de resultados de leilões de transmissão (baixada à mão) para historico/")
    li.add_argument("arquivo", help="Resultado_leiloes_transmissao.xlsx (gov.br/aneel › Centrais de Conteúdos › Relatórios e Indicadores › Leilões)")
    mu = sub.add_parser("mundo-atualizar", help="D38: coleta comércio (Comex Stat), economia (Banco Mundial) e manchetes (GDELT) para o globo")
    mu.add_argument("--ano", default=None, help="ano do comércio (padrão: o último ano completo)")
    mu.add_argument("--sem-noticias", action="store_true", help="não busca manchetes")
    mu.add_argument("--so-noticias", action="store_true", help="só manchetes (não refaz o comércio, que leva ~10 min)")
    mu.add_argument("--so-relacoes", action="store_true", help="só votos na ONU, disputas na OMC e conflitos armados (D42, D43)")
    sub.add_parser("contexto-atualizar", help="Fase 5: baixa só as séries públicas usadas no contexto do radar (catalog/contexto_radar.json)")
    sub.add_parser("siget-historico-exportar", help="acrescenta coletas e eventos novos a historico/*.csv (nunca reescreve)")
    sub.add_parser("siget-historico-importar", help="carrega historico/*.csv num banco novo (ex.: GitHub Actions)")

    op = sub.add_parser("oportunidades", help="Fase 3: oportunidades do SIGET para um perfil (relatório HTML + CSV)")
    op.add_argument("--perfil", default=None, help="JSON do perfil (padrão: catalog/perfil_demo.json)")
    op.add_argument("--top", type=int, default=30, help="quantas oportunidades detalhar no relatório")
    op.add_argument("--saida", default=None, help="pasta de saída (padrão: data/relatorios/<perfil>_<data>)")

    s = sub.add_parser("servir", help="inicia a interface web local")
    s.add_argument("--porta", type=int, default=8000)

    args = p.parse_args(argv)
    if args.cmd == "atualizar":
        update(args.ids or None)
    elif args.cmd == "importar":
        import_file(args)
    elif args.cmd == "importar-macrodados":
        import_macrodados(args.arquivos, args.modulo, args.tema)
    elif args.cmd == "publicar":
        from . import public_build
        m = public_build.build(Path(args.saida) if args.saida else None)
        print(f"site público gerado: {m['series']} séries, análises {m['setores_analise']}, "
              f"previsões setoriais {m['setores_previsao']}; verificação anti-vazamento ok")
    elif args.cmd == "analisar-setor":
        for r in analyze_sector(args.setores or None):
            print(f"{r['setor']}: {r['n_testes']} testes, {len(r['candidatos'])} candidatos")
    elif args.cmd == "registro-exportar":
        from . import registro
        print("linhas novas:", registro.exportar())
    elif args.cmd == "registro-importar":
        from . import registro
        print("linhas carregadas:", registro.importar())
    elif args.cmd == "registro-verificar":
        from . import registro
        problemas = registro.verificar(storage.connect(), contra=args.contra or None)
        if problemas:
            print("REGISTRO ALTERADO:\n  " + "\n  ".join(problemas), file=sys.stderr)
            sys.exit(1)
        print("registro íntegro: só acréscimos, e o banco confere com o CSV")
    elif args.cmd == "qualidade":
        for r in quality.run_all(storage.connect(), cat.load_catalog()):
            print(r)
    elif args.cmd == "prever":
        print(predict())
    elif args.cmd == "prever-setor":
        r = predict_sectors(args.pessoal)
        for s in r["registro"]:
            print(f"  {s['setor']:16} origem {s.get('origem', '–')}  registradas {s.get('registradas', 0)}  {s.get('erro', '')}")
        print(f"avaliação: {r['avaliadas']} previsões com dado realizado, {r['pendentes']} aguardando")
        for p in r["placar"]:
            extra = f", com juros/base {p['vs_base']:.3f}" if "vs_base" in p else ""
            print(f"  {p['setor']:16} {p['modelo']:5} n={p['n']} RMSE {p['rmse']:.2f}{extra}")
    elif args.cmd == "calibrar-setorial":
        r = calibrate_sectors()
        print("calibração salva para", ", ".join(r["setores"]))
    elif args.cmd == "backtest":
        r = save_backtest()
        print(f"backtest salvo: origens {r['origens'][0]} a {r['origens'][1]}")
    elif args.cmd == "fonte-explorar":
        from .providers import ckan
        if args.conjunto:
            print("relatório:", ckan.explorar(args.portal, args.conjunto, max_mb=args.max_mb))
        else:
            for c in ckan.buscar(args.portal, args.busca):
                print(f"{c['nome']}  |  {c['titulo']}  |  licença: {c['licenca'] or 'não declarada'}  |  {c['modificado']}")
                for r in c["recursos"]:
                    print(f"    [{r['formato'] or '?'}] {r['nome']}  {r['url']}")
    elif args.cmd == "siget-amostra":
        from .providers import aneel_siget as sg
        emp = sg.empreendimentos(sg.carregar())
        pasta = sg.pasta_padrao().parent
        if args.aleatoria:
            import pandas as pd
            anterior = pasta / "amostra.csv"
            ja = set(pd.read_csv(anterior, dtype=str).id_aneel) if anterior.exists() else set()
            al = sg.amostra_aleatoria(emp, n=args.n, semente=args.semente, excluir=ja)
            al.to_csv(pasta / "amostra-aleatoria.csv", index=False)
            xl = sg.planilha_avaliacao(al, pasta / "amostra-aleatoria-avaliacao.xlsx")
            print(f"sorteio de {len(al)} entre {al.attrs['universo']} elegíveis (semente {args.semente}, {len(ja)} já avaliados excluídos) -> {xl}")
            print(sg.ATRIBUICAO)
            return
        am = sg.amostra(emp, n=args.n)
        emp.to_csv(pasta / "empreendimentos.csv", index=False)
        am.to_csv(pasta / "amostra.csv", index=False)
        print(f"{len(emp)} empreendimentos ({(emp.situacao == sg.EM_ANDAMENTO).sum()} em andamento) -> {pasta / 'empreendimentos.csv'}")
        print(f"amostra de {len(am)} para avaliação manual -> {pasta / 'amostra.csv'}")
        print(sg.ATRIBUICAO)
    elif args.cmd == "siget-atualizar":
        from .intelligence import historico
        from .providers import aneel_siget as sg
        for k, v in sg.baixar().items():
            print(f"  {k:12} {v['status']:18} {v.get('arquivo', '')}")
        emp = sg.empreendimentos(sg.carregar())
        r = historico.registrar(storage.connect(), emp)
        print(f"histórico: {r['status']} (coleta {r['coleta_id']}), {r['eventos']} eventos")
        if r["eventos"]:
            ev = historico.eventos(storage.connect(), r["coleta_id"])
            print("  " + ", ".join(f"{k}: {v}" for k, v in ev.assign(k=ev.tipo + " " + ev.rotulo).k.str.strip().value_counts().items()))
        print(sg.ATRIBUICAO)
    elif args.cmd == "leiloes-importar":
        import hashlib
        from .providers import aneel_leiloes as al
        src = Path(args.arquivo).expanduser().resolve()
        df = al.ler_planilha(src)
        destino = config.DATA_DIR / "fontes" / "aneel" / "resultado-de-leiloes" / "planilhas"
        destino.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        shutil.copy2(src, destino / f"{sha[:12]}_{src.name}")
        al.ARQUIVO_TIDY.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(al.ARQUIVO_TIDY, index=False, lineterminator="\n")
        rec = df[df.data_leilao.notna()].data_leilao.max()
        print(f"{len(df)} lotes de {df.groupby(['leilao', 'data_leilao'], dropna=False).ngroups} leilões; o mais recente em {rec}")
        print(f"  {al.ARQUIVO_TIDY.relative_to(config.ROOT)} (SHA-256 da planilha: {sha[:16]})")
        print(al.ATRIBUICAO)
    elif args.cmd == "mundo-atualizar":
        from .mundo import build as mb
        if args.so_relacoes:
            m = mb.relacoes()
            print(f"relações: ONU {m.get('onu', {}).get('ano', '–')}, OMC; falhas: {m.get('falhas', {})}")
        elif args.so_noticias:
            n = mb.noticias()
            print(f"manchetes: {sum(map(len, n['paises'].values()))} em {len(n['paises'])} países; falhas: {len(n['falhas'])}")
        else:
            m = mb.montar(args.ano, com_noticias=not args.sem_noticias)
            print(f"globo: {len(m['paises'])} países, comércio de {m['ano_comercio']} -> {mb.SAIDA.relative_to(config.ROOT)}")
    elif args.cmd == "contexto-atualizar":
        from .intelligence import contexto as ctxm
        update(ctxm.series_usadas())
    elif args.cmd == "siget-historico-exportar":
        from .intelligence import historico
        print("historico/:", historico.exportar(storage.connect()))
    elif args.cmd == "siget-historico-importar":
        from .intelligence import historico
        print("historico/:", historico.importar(storage.connect()))
    elif args.cmd == "oportunidades":
        import pandas as pd
        from . import intelligence as it
        from .intelligence import evidencia, relatorio, scoring
        from .providers import aneel_siget as sg
        t = sg.carregar()
        cats = it.carregar_categorias()
        perfil = it.carregar_perfil(Path(args.perfil)) if args.perfil else it.carregar_perfil()
        hoje = pd.Timestamp.today().normalize()
        data_fonte = pd.to_datetime(t["eom"].DatGeracaoConjuntoDados.iloc[0], errors="coerce")
        emp = sg.empreendimentos(t)
        ev = evidencia.evidencias(t, cats)
        ops = scoring.oportunidades(emp, ev, cats, perfil, hoje=hoje, data_fonte=data_fonte)
        pasta = Path(args.saida) if args.saida else config.DATA_DIR / "relatorios" / f"{perfil['id']}_{hoje:%Y-%m-%d}"
        from .intelligence import historico
        mudancas = historico.eventos(storage.connect())
        from .intelligence import contexto as ctxm
        conn = storage.connect()
        ctx = {"pipeline": ctxm.pipeline(t, emp, hoje), "indicadores": ctxm.indicadores(conn, cat.load_catalog()),
               "previsao": ctxm.previsao_setorial()}
        faltam = [i["id"] for i in ctx["indicadores"] if "erro" in i]
        if faltam:
            print(f"  aviso: sem dados para {', '.join(faltam)} (rode `rotzx atualizar`)")
        from .intelligence import leiloes as lm
        from .providers import aneel_leiloes as al
        tab = al.carregar()
        lc = None
        if not tab.empty:
            mapa = lm.carregar_mapa()
            lc = {"pendentes": lm.pendentes(tab, mapa, hoje), "prazos": lm.prazos_observados(mapa, t["agente"]),
                  "atribuicao": al.ATRIBUICAO}
            print(f"  leilões: {len(lc['pendentes'])} lotes arrematados sem contrato identificado no SIGET")
        else:
            print("  aviso: resultados de leilões não importados (rode `rotzx leiloes-importar arquivo.xlsx`)")
        out = relatorio.gerar(ops, ev, cats, perfil, pasta, top=args.top, hoje=hoje, fontes=emp.attrs.get("fontes"),
                              eventos=mudancas, contexto=ctx, leiloes=lc)
        print(f"{len(ops)} oportunidades para {perfil['nome']}")
        for k, v in out.items():
            print(f"  {k}: {v}")
        print(sg.ATRIBUICAO)
    elif args.cmd == "servir":
        import uvicorn
        uvicorn.run("rotzx.api:app", host="127.0.0.1", port=args.porta)


if __name__ == "__main__":
    main()
