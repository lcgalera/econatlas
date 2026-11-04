"""Linha de comando do rotzx.

Exemplos:
  python -m econatlas atualizar                  # baixa todas as séries públicas
  python -m econatlas atualizar ipca_mensal      # só uma série
  python -m econatlas importar export.csv --id md_icms --nome "ICMS – SP" --unidade "R$ mil" \
      --periodicidade mensal --instituicao "Sefaz-SP" --fonte "Macrodados (exportação)"
  python -m econatlas qualidade
  python -m econatlas servir                     # abre a interface em http://127.0.0.1:8000
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
    p = argparse.ArgumentParser(prog="econatlas")
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
    elif args.cmd == "servir":
        import uvicorn
        uvicorn.run("econatlas.api:app", host="127.0.0.1", port=args.porta)


if __name__ == "__main__":
    main()
