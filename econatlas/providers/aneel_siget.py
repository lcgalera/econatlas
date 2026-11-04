"""ANEEL — SIGET (Sistema de Gestão da Transmissão): visão por empreendimento, a partir dos arquivos oficiais.

Lê os CSVs baixados por `econatlas fonte-explorar x --conjunto sistema-de-gestao-da-transmissao-siget`
(data/fontes/aneel/<conjunto>/brutos/, fora do git) e monta uma linha por empreendimento com o que a
fonte afirma: situação, datas do ato legal, concessionária (contrato), UF das subestações, obras e
módulos de equipamento e de manobra. Fase 1: serve para avaliação humana, ainda não é o coletor de produção.

Ligações usadas (sobreposição de 100% medida em 04/11/2026, ver docs/03-fonte-siget.md):
  empreendimento/obra/módulo --IdeMdl--> módulos de equipamento, manobra e linha
  empreendimento --IdeCcd--> contrato de concessão (razão social, CNPJ)
  empreendimento --IdeEpd--> atos autorizativos (REA/DSP), com link do documento

Licença da fonte: ODbL (Open Data Commons Open Database License). Bases derivadas publicadas precisam
citar a ANEEL e manter a mesma licença.
"""
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .. import config
from . import ckan

CONJUNTO = "sistema-de-gestao-da-transmissao-siget"
ATRIBUICAO = "Contém dados da ANEEL (SIGET, Portal de Dados Abertos), disponibilizados sob a licença ODbL."
ARQUIVOS = {
    "eom": "siget-contrato-empreendimento-obra-modulo.csv",
    "agente": "siget-contrato-agente.csv",
    "equipamento": "siget-contrato-moduloequipamento-subestacao.csv",
    "manobra": "siget-contrato-modulomanobra-subestacao-tipoarranjo.csv",
    "linha": "siget-contrato-modulolinhatransmissao-subestacaoorigem-subestacaodestino.csv",
    "geral": "siget-contrato-modulogeral-subestacao-tipoarranjo.csv",
    "resolucao": "siget-resolucao-contrato-agente.csv",
}
EM_ANDAMENTO = "Em andamento"


def pasta_padrao() -> Path:
    return config.DATA_DIR / "fontes" / "aneel" / CONJUNTO / "brutos"


def carregar(pasta: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """Tabelas do SIGET, cada uma do arquivo bruto mais recente. `attrs['arquivo']` guarda a proveniência."""
    pasta = Path(pasta or pasta_padrao())
    out = {}
    for chave, nome in ARQUIVOS.items():
        achados = sorted(pasta.glob(f"*_{nome}"), key=lambda p: p.stat().st_mtime)
        if not achados:
            raise FileNotFoundError(f"{nome} não está em {pasta}; rode `econatlas fonte-explorar x --conjunto {CONJUNTO}`")
        df = ckan.ler_csv(achados[-1].read_bytes())
        df.attrs["arquivo"] = achados[-1].name
        out[chave] = df
    return out


def numero(s: pd.Series) -> pd.Series:
    """Números da fonte vêm como '500,00', '150.00' ou '1.234,56'."""
    t = s.astype(str).str.strip()
    milhar = t.str.contains(",") & t.str.contains(r"\.")
    t = t.where(~milhar, t.str.replace(".", "", regex=False))
    return pd.to_numeric(t.str.replace(",", ".", regex=False), errors="coerce")


def data(s: pd.Series) -> pd.Series:
    """Datas da fonte vêm como dd/mm/aaaa (contrato) ou aaaa-mm-dd (resolução)."""
    br = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    iso = pd.to_datetime(s.astype(str).str[:10], format="%Y-%m-%d", errors="coerce")
    return br.fillna(iso)


def _fmt(v: float, unid: str) -> str:
    return "" if pd.isna(v) else f" {v:g} {unid}"


def _equipamentos(eom: pd.DataFrame, eq: pd.DataFrame) -> pd.DataFrame:
    """Equipamentos (módulos ME) ligados às obras em andamento, um texto por empreendimento."""
    ob = eom[eom.DscSitObr == EM_ANDAMENTO][["IdeEpd", "IdeMdl", "DscTipObr"]].drop_duplicates()
    e = ob.merge(eq, on="IdeMdl")
    if e.empty:
        return pd.DataFrame(columns=["IdeEpd", "equipamentos", "n_equipamentos"])
    tns, pot = numero(e.NumTnsMdl), numero(e.MdaPotAtvMdlEqp)
    e["txt"] = (e.DscTipEqp + _sep(tns, "kV") + _sep(pot, "MVA") + " [" + e.DscTipObr + "]")
    return e.groupby("IdeEpd").agg(equipamentos=("txt", lambda x: "; ".join(sorted(set(x)))),
                                   n_equipamentos=("IdeMdl", "nunique")).reset_index()


def _sep(v: pd.Series, unid: str) -> pd.Series:
    return v.map(lambda x: _fmt(x, unid))


def _manobra(eom: pd.DataFrame, mm: pd.DataFrame) -> pd.DataFrame:
    ob = eom[eom.DscSitObr == EM_ANDAMENTO][["IdeEpd", "IdeMdl"]].drop_duplicates()
    m = ob.merge(mm, on="IdeMdl")
    m["dj"], m["sc"] = numero(m.QtdDijMdlMno), numero(m.QtdChvSccMdlMno)
    return m.groupby("IdeEpd").agg(n_modulos_manobra=("IdeMdl", "nunique"),
                                   disjuntores_declarados=("dj", "sum"),
                                   seccionadoras_declaradas=("sc", "sum")).reset_index()


def _linhas(eom: pd.DataFrame, lt: pd.DataFrame) -> pd.DataFrame:
    ob = eom[eom.DscSitObr == EM_ANDAMENTO][["IdeEpd", "IdeObr"]].drop_duplicates()
    m = ob.merge(lt, on="IdeObr")
    m["txt"] = m.NomLinTms + " (" + m.NumTensaoBaseLinhaTransm.str.replace(",00", "", regex=False) + " kV)"
    return m.groupby("IdeEpd").agg(linhas=("txt", lambda x: "; ".join(sorted(set(x))))).reset_index()


def _ufs(eom: pd.DataFrame, t: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    partes = [t[k][["IdeMdl", "SigUFSubestacao"]] for k in ("equipamento", "manobra", "geral")]
    lt = t["linha"]
    partes += [lt[["IdeMdl", c]].rename(columns={c: "SigUFSubestacao"}) for c in ("SigUFSubestacaoOrigem", "SigUFSubestacaoDestino")]
    u = eom[["IdeEpd", "IdeMdl"]].merge(pd.concat(partes), on="IdeMdl")
    u = u[u.SigUFSubestacao.str.len() == 2]
    return u.groupby("IdeEpd").agg(ufs=("SigUFSubestacao", lambda x: ",".join(sorted(set(x))))).reset_index()


def _atos(res: pd.DataFrame) -> pd.DataFrame:
    """Ato autorizativo mais recente de cada empreendimento (REA/DSP), com link do documento."""
    r = res.assign(pub=data(res.DatPubDoc)).sort_values("pub")
    r = r.groupby("IdeEpd").tail(1)
    return r[["IdeEpd", "CodReg", "DatPubDoc", "DscLink"]].rename(
        columns={"CodReg": "ato", "DatPubDoc": "ato_publicado_em", "DscLink": "ato_link"})


def empreendimentos(t: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Uma linha por empreendimento, só com o que a fonte afirma (nenhuma inferência de compra)."""
    eom = t["eom"]
    base = eom.drop_duplicates("IdeEpd")[["IdeEpd", "IdeOnsEpd", "NomEpd", "DscEpd", "DscSituacaoEpd", "DatOprComEpd",
                                          "DatCaoCgmAtoLgl", "DatEfeOprComEpd", "IdeCcd"]].copy()
    ag = t["agente"][["IdeCcd", "DscRazaoSocial", "NumCNPJ", "NumCnaCcd"]]
    base = base.merge(ag, on="IdeCcd", how="left")
    obras = eom.drop_duplicates("IdeObr").groupby("IdeEpd").agg(
        n_obras=("IdeObr", "nunique"),
        n_obras_em_andamento=("DscSitObr", lambda x: int((x == EM_ANDAMENTO).sum())),
        tipos_obra=("DscTipObr", lambda x: ", ".join(sorted(set(x) - {""})))).reset_index()
    out = base.merge(obras, on="IdeEpd", how="left")
    for parte in (_ufs(eom, t), _equipamentos(eom, t["equipamento"]), _manobra(eom, t["manobra"]),
                  _linhas(eom, t["linha"]), _atos(t["resolucao"])):
        out = out.merge(parte, on="IdeEpd", how="left")
    out["origem"] = out.IdeEpd.isin(t["resolucao"].IdeEpd).map(
        {True: "autorização (resolução/despacho)", False: "contrato de concessão"})
    out["n_equipamentos"] = out.n_equipamentos.fillna(0).astype(int)
    out["n_modulos_manobra"] = out.n_modulos_manobra.fillna(0).astype(int)
    out = out.rename(columns={
        "IdeEpd": "id_aneel", "IdeOnsEpd": "id_ons", "NomEpd": "nome", "DscEpd": "descricao", "DscSituacaoEpd": "situacao",
        "DatOprComEpd": "operacao_ato_legal", "DatCaoCgmAtoLgl": "conclusao_ato_legal", "DatEfeOprComEpd": "operacao_efetiva",
        "IdeCcd": "id_contrato", "DscRazaoSocial": "concessionaria", "NumCNPJ": "cnpj", "NumCnaCcd": "contrato"})
    out.attrs["fontes"] = {k: v.attrs.get("arquivo") for k, v in t.items()}
    return out.fillna("").sort_values("id_aneel", key=lambda s: pd.to_numeric(s, errors="coerce")).reset_index(drop=True)


def amostra(emp: pd.DataFrame, n: int = 20, hoje: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Amostra reproduzível para avaliação manual (docs/03-fonte-siget.md §7).

    Regra: situação "Em andamento", data de operação do ato legal no futuro e pelo menos um módulo de
    equipamento ligado a obra em andamento. Metade de cada origem (autorização × contrato), as mais
    documentadas primeiro (mais equipamentos, depois mais módulos de manobra), desempate pelo id da ANEEL.
    """
    hoje = hoje or pd.Timestamp.today().normalize()
    e = emp[(emp.situacao == EM_ANDAMENTO) & (data(emp.operacao_ato_legal) > hoje) & (emp.n_equipamentos > 0)].copy()
    e["_id"] = pd.to_numeric(e.id_aneel, errors="coerce")
    e = e.sort_values(["n_equipamentos", "n_modulos_manobra", "_id"], ascending=[False, False, True])
    metade = n // 2
    partes = [e[e.origem == o].head(metade + (n % 2 if i == 0 else 0)) for i, o in enumerate(sorted(e.origem.unique()))]
    a = pd.concat(partes) if partes else e.head(0)
    if len(a) < n:  # uma das origens não tem casos suficientes: completa com a outra
        a = pd.concat([a, e[~e.index.isin(a.index)].head(n - len(a))])
    a = a.drop(columns="_id")
    a["avaliacao_relevante"] = ""  # preenchido à mão: s / n / ? (critério em docs/03 §7)
    a["avaliacao_nota"] = ""
    return a.reset_index(drop=True)


def elegiveis(emp: pd.DataFrame, hoje: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Universo das amostras: em andamento, operação do ato legal no futuro, ≥ 1 equipamento em obra em andamento."""
    hoje = hoje or pd.Timestamp.today().normalize()
    return emp[(emp.situacao == EM_ANDAMENTO) & (data(emp.operacao_ato_legal) > hoje) & (emp.n_equipamentos > 0)]


JANELA_MESES = 6  # condição 2 do critério (docs/03 §5)


def amostra_aleatoria(emp: pd.DataFrame, n: int = 20, semente: int = 20261104, hoje: Optional[pd.Timestamp] = None,
                      excluir: Optional[set] = None) -> pd.DataFrame:
    """Sorteio simples (semente fixa) entre os elegíveis, sem os já avaliados. Serve para estimar a precisão sem viés.

    As condições mecânicas do critério já vêm calculadas: c2 (operação a mais de JANELA_MESES meses de `hoje`)
    e c3 (concessionária identificada). A condição 1 (equipamento novo do perfil) é julgada por pessoa.
    """
    hoje = hoje or pd.Timestamp.today().normalize()
    u = elegiveis(emp, hoje)
    if excluir:
        u = u[~u.id_aneel.isin(excluir)]
    u = u.assign(_id=pd.to_numeric(u.id_aneel, errors="coerce")).sort_values("_id").drop(columns="_id")
    a = u.sample(n=min(n, len(u)), random_state=semente).copy()
    op = data(a.operacao_ato_legal)
    a["meses_ate_operacao"] = ((op - hoje).dt.days / 30.44).round(1)
    a["c2_janela"] = (op > hoje + pd.DateOffset(months=JANELA_MESES)).map({True: "s", False: "n"})
    a["c3_comprador"] = (a.concessionaria.astype(str).str.strip() != "").map({True: "s", False: "n"})
    a["c1_equipamento"] = ""  # s / n / ? — julgamento humano
    a["avaliacao_nota"] = ""
    a.attrs.update(semente=semente, data_referencia=str(hoje.date()), universo=len(u))
    return a.reset_index(drop=True)


def planilha_avaliacao(a: pd.DataFrame, caminho: Path) -> Path:
    """Planilha para a avaliação humana: a pessoa preenche só a condição 1; o resultado sai por fórmula."""
    from openpyxl.styles import Alignment, Font, PatternFill
    cols = [("c1_equipamento", "C1 equipamento novo do perfil? (s/n/?)", 16), ("resultado", "Resultado", 11),
            ("c2_janela", f"C2 > {JANELA_MESES} meses?", 10), ("c3_comprador", "C3 concessionária?", 10),
            ("meses_ate_operacao", "Meses até operação", 10), ("avaliacao_nota", "Nota", 30), ("id_ons", "Id ONS", 13),
            ("nome", "Empreendimento", 40), ("descricao", "Descrição (fonte)", 60), ("equipamentos", "Equipamentos (obras em andamento)", 55),
            ("concessionaria", "Concessionária", 20), ("ufs", "UF", 8), ("operacao_ato_legal", "Operação (ato legal)", 13),
            ("origem", "Origem", 20), ("n_modulos_manobra", "Módulos de manobra", 10), ("linhas", "Linhas", 35),
            ("tipos_obra", "Tipos de obra", 16), ("ato", "Ato", 15), ("ato_link", "Link do ato", 35)]
    x = a.assign(resultado="")[[c for c, _, _ in cols]].rename(columns={c: t for c, t, _ in cols})
    with pd.ExcelWriter(caminho, engine="openpyxl") as w:
        x.to_excel(w, index=False, sheet_name="Amostra")
        ws = w.sheets["Amostra"]
        for i, (_, _, larg) in enumerate(cols, start=1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = larg
        amarelo = PatternFill("solid", fgColor="FFF2CC")
        for r in range(2, len(x) + 2):
            # resultado: n se qualquer condição falha; ? se C1 é ?; s se as três valem; vazio enquanto C1 não for preenchida
            ws.cell(r, 2).value = (f'=IF(A{r}="","",IF(OR(A{r}="n",C{r}="n",D{r}="n"),"n",IF(A{r}="?","?","s")))')
            ws.cell(r, 1).fill = amarelo
            for c in ws[r]:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        for c in ws[1]:
            c.font = Font(bold=True)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "H2"
        n = len(x) + 1
        resumo = pd.DataFrame({"Item": ["Avaliados (C1 preenchida)", "s", "n", "?", "Precisão = s / (s + n)", "",
                                        "Semente do sorteio", "Data de referência", "Universo elegível"],
                               "Valor": [f'=COUNTIF(Amostra!A2:A{n},"?*")', f'=COUNTIF(Amostra!B2:B{n},"s")',
                                         f'=COUNTIF(Amostra!B2:B{n},"n")', f'=COUNTIF(Amostra!B2:B{n},"~?")',
                                         '=IF(B3+B4=0,"",B3/(B3+B4))', "", a.attrs.get("semente", ""),
                                         a.attrs.get("data_referencia", ""), a.attrs.get("universo", "")]})
        resumo.to_excel(w, index=False, sheet_name="Resumo")
        w.sheets["Resumo"].column_dimensions["A"].width = 30
        w.sheets["Resumo"]["B6"].number_format = "0%"
        crit = pd.DataFrame({"Como avaliar (docs/03-fonte-siget.md §5)": [
            "Preencha só a coluna amarela (C1). C2, C3 e o Resultado já vêm calculados.",
            "C1 = s se a descrição ou os equipamentos indicam fornecimento NOVO ou SUBSTITUIÇÃO de equipamento do perfil:",
            "   transformador de potência, reator, banco de capacitores, compensador, manobra (disjuntores/seccionadoras).",
            "   [Instalação] = módulo novo. [Adequação] sozinho não basta: leia a descrição.",
            "C1 = n se é só proteção, obra civil, linha sem equipamento de subestação ou revitalização sem equipamento citado.",
            "C1 = ? se a fonte não permite decidir. Julgue pelo que está escrito, não pelo que imagina.",
            "Use a Nota para dizer o motivo de n ou ?, e para discordar da regra (sem mudar a marca).",
            ATRIBUICAO]})
        crit.to_excel(w, index=False, sheet_name="Como avaliar")
        w.sheets["Como avaliar"].column_dimensions["A"].width = 115
    return caminho
