/* EconAtlas — interface (sem build; ECharts via CDN). */
"use strict";

const $app = document.getElementById("app");
const state = { catalog: null, charts: [] };

/* ---------- utilidades ---------- */
const STATIC = window.ECONATLAS_STATIC === true;  // site público: arquivos JSON no lugar da API

// Mapeia cada rota da API para o arquivo gerado por `econatlas publicar`.
function staticPath(path) {
  const u = new URL(path, "http://x");
  const p = u.pathname;
  let m;
  if (p === "/api/catalogo") return { file: "data/catalogo.json" };
  if ((m = p.match(/^\/api\/series\/([\w-]+)\/versoes$/))) return { file: `data/series/${m[1]}/versoes.json` };
  if ((m = p.match(/^\/api\/series\/([\w-]+)$/)))
    return { file: `data/series/${m[1]}/${u.searchParams.get("transform") || "nivel"}.json`,
             inicio: u.searchParams.get("inicio"), fim: u.searchParams.get("fim") };
  const fixed = { "/api/qualidade": "qualidade", "/api/previsoes/ipca": "previsoes_ipca",
                  "/api/analises/setores": "analises_setores", "/api/previsoes/setoriais": "previsoes_setoriais" };
  if (fixed[p]) return { file: `data/${fixed[p]}.json` };
  throw new Error(`rota indisponível na versão pública: ${p}`);
}

const api = async (path, opts) => {
  if (STATIC) {
    const s = staticPath(path);
    const r = await fetch(s.file);
    if (!r.ok) throw new Error(r.status === 404 ? "dado não publicado nesta versão" : r.statusText);
    const d = await r.json();
    if (s.inicio || s.fim) d.dados = d.dados.filter(([x]) => (!s.inicio || x >= s.inicio) && (!s.fim || x <= s.fim));
    return d;
  }
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

function fmtNum(v, digits) {
  if (v == null || Number.isNaN(v)) return "–";
  const abs = Math.abs(v);
  const d = digits ?? (abs >= 100000 ? 0 : abs >= 100 ? 1 : 2);
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
}
function fmtDate(iso, per) {
  const [y, m, d] = iso.split("-").map(Number);
  if (per === "trimestral") return `${Math.floor((m - 1) / 3) + 1}º tri ${y}`;
  if (per === "anual") return String(y);
  if (per === "diaria") return `${d} ${MESES[m - 1]} ${y}`;
  return `${MESES[m - 1]} ${y}`;
}
const fmtTs = (iso) => {
  const d = new Date(iso);
  return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2, "0")}h${String(d.getMinutes()).padStart(2, "0")}`;
};
const sourceLabel = (s) =>
  s.provedor === "bcb_sgs" ? `BCB · SGS ${s.codigo}` :
  s.provedor === "ibge_sidra" ? `IBGE · SIDRA ${s.codigo.split("/")[1]}` :
  s.extra?.codigo_md ? `${s.instituicao} via Macrodados · ${s.extra.codigo_md}` :
  s.extra?.fonte_aquisicao || "Arquivo importado";

function flags(s) {
  const f = [];
  if (!s.metadados_conferidos) f.push(`<span class="flag warn" title="Nome, unidade e ajuste ainda não conferidos com a ficha oficial da série">a conferir</span>`);
  if (s.uso !== "publico") f.push(`<span class="flag crit" title="Não publicar nem compartilhar">uso ${esc(s.uso)}</span>`);
  return f.join(" ");
}

const PERIODOS = [
  { id: "5a", rotulo: "5 anos", anos: 5 },
  { id: "10a", rotulo: "10 anos", anos: 10 },
  { id: "2012", rotulo: "Desde 2012", inicio: "2012-01-01" },
  { id: "tudo", rotulo: "Tudo" },
];
function periodStart(pid) {
  const p = PERIODOS.find((x) => x.id === pid);
  if (!p || p.id === "tudo") return null;
  if (p.inicio) return p.inicio;
  const d = new Date(); d.setFullYear(d.getFullYear() - p.anos);
  return d.toISOString().slice(0, 10);
}
const tabsHtml = (name, items, on) =>
  `<div class="tabs" role="group" aria-label="Período" data-tabs="${name}">${items.map((i) =>
    `<button type="button" data-v="${i.id}" class="${i.id === on ? "on" : ""}">${esc(i.rotulo)}</button>`).join("")}</div>`;
function onTabs(name, cb) {
  document.querySelector(`[data-tabs="${name}"]`).onclick = (e) => {
    const v = e.target.dataset.v; if (!v) return;
    e.currentTarget.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
    cb(v);
  };
}
const field = (label, inner) => `<label class="field"><span>${label}</span>${inner}</label>`;

async function loadSeries(id, transform = "nivel", inicio = null) {
  const q = new URLSearchParams({ transform });
  if (inicio) q.set("inicio", inicio);
  return api(`/api/series/${id}?${q}`);
}

function sparkline(points, w = 112, h = 26) {
  const vals = points.map((p) => p[1]).filter((v) => v != null);
  if (vals.length < 2) return "";
  const min = Math.min(...vals), max = Math.max(...vals), span = max - min || 1;
  const xy = vals.map((v, i) => [(i / (vals.length - 1)) * (w - 4) + 2, h - 3 - ((v - min) / span) * (h - 6)]);
  const last = xy[xy.length - 1];
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">
    <polyline points="${xy.map((p) => p.map((n) => n.toFixed(1)).join(",")).join(" ")}" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/>
    <circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="2.5" fill="var(--ink)"/></svg>`;
}

/* ---------- gráficos ---------- */
function disposeCharts() { state.charts.forEach((c) => c.dispose()); state.charts = []; }
window.addEventListener("resize", () => state.charts.forEach((c) => c.resize()));

/**
 * Gráfico de linhas com um único eixo Y.
 * series: [{name, data:[[x,y]], color:'--var', dashed?, width?}]
 * band:   {lo:[[x,y]], hi:[[x,y]], name}  (intervalo sombreado)
 */
function drawChart(el, { series, band = null, unit = "", per = "mensal", xType = "time", group = null, xLabel = null }) {
  const chart = echarts.init(el, null, { renderer: "svg" });
  const ink = css("--ink"), ink2 = css("--ink-2"), ink3 = css("--ink-3"), grid = css("--grid"), rule = css("--rule");
  const allY = series.flatMap((s) => s.data.map((p) => p[1])).filter((v) => v != null);
  const hasNeg = allY.some((v) => v < 0);
  const eSeries = [];
  if (band) {
    const hiMap = Object.fromEntries(band.hi.map((p) => [p[0], p[1]]));
    eSeries.push({ type: "line", data: band.lo, stack: "band", stackStrategy: "all", symbol: "none", lineStyle: { opacity: 0 }, silent: true, z: 1, tooltip: { show: false } });
    eSeries.push({ type: "line", data: band.lo.map((p) => [p[0], hiMap[p[0]] - p[1]]), stack: "band", stackStrategy: "all", symbol: "none",
      lineStyle: { opacity: 0 }, areaStyle: { color: css("--band") }, silent: true, z: 1, tooltip: { show: false } });
  }
  series.forEach((s) => eSeries.push({
    name: s.name, type: "line", data: s.data, showSymbol: xType === "category", symbolSize: 7, symbol: "circle",
    lineStyle: { width: s.width || 2, color: css(s.color), type: s.dashed ? [5, 4] : "solid" },
    itemStyle: { color: css(s.color), borderColor: css("--bg"), borderWidth: 2 }, z: 3,
  }));
  if (hasNeg && xType === "time") {
    eSeries.push({ type: "line", data: [], markLine: { silent: true, symbol: "none", label: { show: false }, lineStyle: { color: ink3, type: "solid", width: 1 }, data: [{ yAxis: 0 }] } });
  }
  const bandIdx = band ? Object.fromEntries(band.lo.map((p, i) => [p[0], [p[1], band.hi[i][1]]])) : {};
  chart.setOption({
    animation: false,
    grid: { left: 4, right: 12, top: 12, bottom: xLabel ? 34 : 24, containLabel: true },
    tooltip: {
      trigger: "axis", confine: true,
      axisPointer: { type: "line", lineStyle: { color: ink3, width: 1 } },
      backgroundColor: css("--bg"), borderColor: rule, borderWidth: 1, padding: [8, 10],
      textStyle: { color: ink, fontSize: 13, fontFamily: "IBM Plex Sans" }, extraCssText: "box-shadow:none;border-radius:0",
      formatter: (ps) => {
        const ps2 = ps.filter((p) => p.seriesName && p.value[1] != null);
        if (!ps2.length) return "";
        const x = ps2[0].value[0];
        const head = xType === "time" ? fmtDate(x, per) : `${xLabel ? xLabel + " " : ""}${x}`;
        const lines = ps2.map((p) => `<div style="display:flex;gap:14px;justify-content:space-between"><span><i style="display:inline-block;width:10px;height:2px;background:${p.color};vertical-align:middle;margin-right:6px"></i>${esc(p.seriesName)}</span><b>${fmtNum(p.value[1])}</b></div>`).join("");
        const b = bandIdx[x] ? `<div style="color:${ink2};font-size:12px;margin-top:4px">${esc(band.name)}: ${fmtNum(bandIdx[x][0])} a ${fmtNum(bandIdx[x][1])}</div>` : "";
        return `<div style="font-size:12px;color:${ink2};margin-bottom:4px">${head}${unit ? " · " + esc(unit) : ""}</div>${lines}${b}`;
      },
    },
    xAxis: {
      type: xType, name: xLabel || "", nameLocation: "middle", nameGap: 26, nameTextStyle: { color: ink3, fontSize: 11 },
      axisLine: { lineStyle: { color: ink3 } }, axisTick: { show: false },
      axisLabel: { color: ink3, fontSize: 11, hideOverlap: true, fontFamily: "IBM Plex Sans" }, splitLine: { show: false },
    },
    yAxis: {
      type: "value", scale: !hasNeg && xType === "time", position: "right",
      axisLabel: { color: ink3, fontSize: 11, formatter: (v) => fmtNum(v), fontFamily: "IBM Plex Sans" },
      splitLine: { lineStyle: { color: grid } },
    },
    dataZoom: xType === "time" ? [{ type: "inside", throttle: 50 }] : [],
    series: eSeries,
  });
  if (group) { chart.group = group; echarts.connect(group); }
  state.charts.push(chart);
  return chart;
}

function seriesChart(el, resp, opts = {}) {
  const per = resp.transformacao.id === "media_mensal" ? "mensal" : resp.serie.periodicidade;
  return drawChart(el, { series: [{ name: resp.serie.nome, data: resp.dados, color: opts.color || "--series-1" }],
    unit: resp.transformacao.unidade, per, group: opts.group });
}

function sourceLine(resp) {
  const v = resp.versao, t = resp.transformacao;
  const parts = [`Fonte: ${esc(resp.serie.instituicao)}, via ${esc(sourceLabel(resp.serie))}`];
  if (t.id !== "nivel") parts.push(`${esc(t.rotulo)}: <code>${esc(t.formula)}</code>${t.base ? `, base ${t.base}` : ""}`);
  if (t.series_auxiliares.length) parts.push(`usa também ${t.series_auxiliares.join(", ")}`);
  parts.push(`coletado em ${fmtTs(v.fetched_at)} (versão ${v.id})`);
  return parts.join(". ") + ".";
}

/* ---------- módulos ---------- */
const MODULOS = [
  { id: "radar", num: "I", nome: "Radar Brasil", ativo: true, desc: "Observatório da economia brasileira: inflação, juros, câmbio, atividade, renda e crédito, com fonte e data em cada número." },
  { id: "forecast", num: "II", nome: "MacroForecast", ativo: true, desc: "Previsões do IPCA registradas antes da divulgação, comparadas ao Focus. Os erros ficam no registro." },
  { id: "setorial", num: "III", nome: "Radar Setorial", ativo: false, desc: "Indústria, materiais elétricos, construção e energia: atividade, emprego, custos e indicadores antecedentes.",
    itens: ["Produção, emprego e custos por setor", "Indicadores antecedentes, sem presumir causalidade", "Alertas com regras documentadas", "Vendas da empresa × indicadores econômicos"] },
  { id: "mundo", num: "IV", nome: "Brasil x Mundo", ativo: false, desc: "Estudos comparativos com indicadores comparáveis: PPC, preços constantes, produtividade e investimento.",
    itens: ["PIB per capita PPC (Banco Mundial)", "Investimento e produtividade", "Convergência de renda", "Estudos históricos pontuais"] },
];

function lede(kicker, title, standfirst, dateline = "") {
  return `<header class="lede"><p class="kicker">${kicker}</p><h1>${title}</h1><p class="standfirst">${standfirst}</p>${dateline ? `<div class="dateline">${dateline}</div>` : ""}</header>`;
}

function pageHome() {
  const by = Object.fromEntries(state.catalog.map((s) => [s.id, s]));
  const snap = [["ipca_12m", "IPCA em 12 meses"], ["selic_meta", "Meta Selic"], ["desocupacao", "Desocupação"], ["cambio_usd", "Dólar, média mensal"]]
    .filter(([id]) => by[id]?.ultimo)
    .map(([id, label]) => {
      const s = by[id];
      return `<a href="#/serie/${id}"><div class="label">${label}</div><div class="big">${fmtNum(s.ultimo.valor)}<small>${esc(s.unidade)}</small></div><div class="when">${fmtDate(s.ultimo.data, s.periodicidade)}</div></a>`;
    }).join("");
  $app.innerHTML = `
    ${lede("Inteligência econômica", "Dados econômicos com origem, data e método à vista",
      "Cada número mostra de onde veio, quando foi coletado e que cálculo foi aplicado. Módulos ainda sem dados aparecem como em preparação; nada aqui é simulado.")}
    <div class="snapshot">${snap}</div>
    <section class="sec">
      <div class="sec-head"><h2>Módulos</h2></div>
      <ol class="modules">
        ${MODULOS.map((m) => `
          <li>
            <div class="num">${m.num}</div>
            <div><h3><a href="#/${m.id}">${m.nome}</a></h3><p>${m.desc}</p></div>
            <div class="st"><span class="flag ${m.ativo ? "ok" : "muted"}">${m.ativo ? "Em operação"
              : state.catalog.some((s) => s.modulo === MOD_KEY[m.id]) ? "Dados importados" : "Em preparação"}</span></div>
          </li>`).join("")}
      </ol>
    </section>`;
}

const MOD_KEY = { radar: "radar_brasil", forecast: "macroforecast", setorial: "radar_setorial", mundo: "brasil_mundo" };
const MOD_ROUTE = Object.fromEntries(Object.entries(MOD_KEY).map(([k, v]) => [v, k]));

function importedSection(series) {
  if (!series.length) return "";
  const groups = TEMAS.filter(([t]) => series.some((s) => s.tema === t));
  return `
    <section class="sec">
      <div class="sec-head"><h2>Séries do setor</h2><span class="sub">${series.length} série${series.length > 1 ? "s" : ""} · ${[...new Set(series.map((s) => s.extra?.codigo_md ? "Macrodados Web (exportação)" : s.instituicao))].map(esc).join(", ")}</span></div>
      <table class="ind">
        <thead><tr><th>Indicador</th><th class="r">Último</th><th class="r ref-col">Referência</th><th class="r">Variação</th><th class="spark">Histórico</th></tr></thead>
        <tbody>${groups.map(([t, nome]) => `<tr class="group"><td colspan="5">${esc(nome)}</td></tr>${series.filter((s) => s.tema === t).map(indicatorRow).join("")}`).join("")}</tbody>
      </table>
      ${series.some((s) => s.uso !== "publico") ? `<p class="aside">Séries de <b>uso pessoal</b>. Os Termos de uso da Macrodados proíbem copiar, redistribuir ou republicar o conteúdo,
      por isso estas séries não podem ser baixadas pela interface nem aparecer em material publicado.
      Para atualizar, exporte de novo na Macrodados e rode <code>python -m econatlas importar-macrodados arquivo.csv</code>.</p>` : ""}
    </section>`;
}

function pagePlanned(id) {
  const m = MODULOS.find((x) => x.id === id);
  const imported = state.catalog.filter((s) => s.modulo === MOD_KEY[id]);
  $app.innerHTML = `
    ${lede(`Módulo ${m.num}`, m.nome, m.desc)}
    ${id === "setorial" ? `<div id="prev-setorial"></div><div id="analise"></div>` : ""}
    ${importedSection(imported)}
    <section class="sec prose">
      <p><span class="flag muted">Em preparação</span>. ${imported.length
        ? "As análises do módulo (comparações, indicadores antecedentes, alertas) ainda não foram construídas; acima estão apenas os dados importados."
        : "Este módulo não exibe números até existirem dados reais e métodos validados."}</p>
      <h3>Escopo previsto</h3>
      <ul>${m.itens.map((i) => `<li>${i}</li>`).join("")}</ul>
      <p>O cronograma e a metodologia estão em <code>docs/01-avaliacao-inicial.md</code>.</p>
    </section>`;
}

async function sectorForecasts() {
  const box = document.getElementById("prev-setorial");
  if (!box) return;
  let d;
  try { d = await api("/api/previsoes/setoriais"); } catch (e) { box.innerHTML = ""; return; }
  if (!d.registro.length) { box.innerHTML = ""; return; }
  const sgn = (v) => (v == null ? "–" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${fmtNum(Math.abs(v), 1)}`);
  const setores = Object.keys(d.setores);
  const latest = (s) => {
    const rs = d.registro.filter((r) => r.setor === s);
    const origem = rs.map((r) => r.origem).sort().pop();
    return rs.filter((r) => r.origem === origem);
  };
  const get = (rs, h, m) => rs.find((r) => r.horizonte === h && r.modelo === m);
  const cov = (s) => {
    const c = d.calibracao?.setores?.[s];
    if (!c) return "";
    const v = Object.entries(c).filter(([k]) => k.startsWith("juros")).map(([, x]) => x.cobertura80).filter((x) => x != null);
    return v.length ? `No backtest, a faixa conteve o realizado em ${fmtNum(Math.min(...v) * 100, 0)}% a ${fmtNum(Math.max(...v) * 100, 0)}% das vezes (meta: 80%).` : "";
  };
  const avaliadas = d.registro.filter((r) => r.realizado != null);
  box.innerHTML = `
    <section class="sec">
      <div class="sec-head"><h2>Previsões setoriais registradas</h2>
        <span class="sub">${d.registro.length} previsões · registro imutável · ${avaliadas.length} já avaliadas</span></div>
      <p class="prose" style="margin-top:0">Variação em 12 meses prevista para cada série, pelo modelo com juros (a variação da Selic em 12 meses, a hipótese original da análise),
      com a faixa empírica de 80%. A linha tracejada é o modelo só com o histórico do setor.</p>
      <div class="multiples">${setores.map((s) => `
        <figure class="fig">
          <p class="fig-title">${esc(d.setores[s].rotulo)}</p>
          <p class="fig-sub">var. 12m, log × 100 · origem ${fmtDate(latest(s)[0].origem, "mensal")}</p>
          <div class="chart sm" id="pf-${s}" style="height:220px"></div>
          <p class="source">${esc(d.setores[s].fonte)}. ${cov(s)}</p>
        </figure>`).join("")}</div>
      <div style="overflow-x:auto;margin-top:12px"><table class="tbl">
        <tr><th>Série</th><th>Mês-alvo</th><th class="r">Base</th><th class="r">Com juros</th><th class="r">Faixa 80% (com juros)</th><th class="r">Realizado</th></tr>
        ${setores.map((s) => { const rs = latest(s); return [0, 3, 6].map((h) => { const b = get(rs, h, "base"), j = get(rs, h, "juros"); if (!j) return "";
          return `<tr><td>${h === 0 ? esc(d.setores[s].rotulo) : ""}</td><td>${fmtDate(j.alvo, "mensal")}${h === 0 ? ' <span class="sub">(mês da origem)</span>' : ""}</td>
            <td class="r">${sgn(b?.valor)}</td><td class="r"><b>${sgn(j.valor)}</b></td>
            <td class="r">${j.lo80 != null ? `${sgn(j.lo80)} a ${sgn(j.hi80)}` : "–"}</td><td class="r">${j.realizado != null ? sgn(j.realizado) : "–"}</td></tr>`; }).join(""); }).join("")}
      </table></div>
      <h3 style="margin-top:24px">Placar ao vivo</h3>
      ${d.placar && d.placar.length ? `<div style="overflow-x:auto"><table class="tbl">
        <tr><th>Série</th><th>Modelo</th><th class="r">Previsões avaliadas</th><th class="r">RMSE (p.p.)</th><th class="r">Com juros ÷ base</th><th class="r">Faixa 80%: realizado dentro</th></tr>
        ${d.placar.map((p) => `<tr><td>${esc(d.setores[p.setor]?.rotulo || p.setor)}</td><td>${p.modelo === "juros" ? "Com juros" : "Base"}</td><td class="r">${p.n}</td>
          <td class="r">${fmtNum(p.rmse, 2)}</td><td class="r">${p.vs_base != null ? `${p.vs_base < 1 ? "−" : "+"}${fmtNum(Math.abs(p.vs_base - 1) * 100, 1)}%` : "–"}</td>
          <td class="r">${p.cobertura80 != null ? `${fmtNum(p.cobertura80 * 100, 0)}% de ${p.n_faixa}` : "–"}</td></tr>`).join("")}
      </table></div>`
      : `<p class="prose">Nenhuma previsão setorial chegou ao mês-alvo ainda. A avaliação é automática: quando o dado do mês-alvo for publicado,
        a próxima execução de <code>prever-setor</code> já mostra aqui o erro de cada modelo, a comparação do modelo com juros contra o base e a cobertura da faixa.</p>`}
      <p class="sub">Especificação <code>${esc(d.especificacao?.id || "")}</code>, fixada antes da primeira previsão: ${esc(d.modelos.juros)}.
      Qualquer mudança vira uma especificação nova, com outro nome, sem apagar as anteriores.</p>
      <p class="aside">A diferença entre os dois modelos é pequena (cerca de 1 ponto), e as faixas são largas (±12 a ±20 pontos), porque esses setores oscilam muito.
      O sinal dos juros ajusta a direção esperada; não dá precisão. Cada previsão fica registrada com a versão dos dados e não pode ser alterada:
      a avaliação aparece aqui quando o dado do mês-alvo for publicado.</p>
    </section>`;
  setores.forEach((s) => {
    const rs = latest(s), hist = d.setores[s].historico;
    const last = hist[hist.length - 1];
    const fj = [0, 3, 6].map((h) => get(rs, h, "juros")).filter(Boolean);
    const fb = [0, 3, 6].map((h) => get(rs, h, "base")).filter(Boolean);
    drawChart(document.getElementById(`pf-${s}`), {
      unit: "%",
      series: [
        { name: "Observado", data: hist, color: "--ink" },
        { name: "Com juros", data: [last, ...fj.map((r) => [r.alvo, r.valor])], color: "--series-1", dashed: false },
        { name: "Base", data: [last, ...fb.map((r) => [r.alvo, r.valor])], color: "--ink-3", dashed: true, width: 1.5 },
      ],
      band: fj.every((r) => r.lo80 != null) ? { name: "Faixa 80%", lo: fj.map((r) => [r.alvo, r.lo80]), hi: fj.map((r) => [r.alvo, r.hi80]) } : null,
    });
  });
}

async function sectorAnalysis() {
  const box = document.getElementById("analise");
  if (!box) return;
  let list;
  try { list = await api("/api/analises/setores"); } catch (e) { box.innerHTML = ""; return; }
  const H = list[0].horizontes.map(String);
  const hLabel = (h) => (h === "0" ? "Mês corrente" : `${h} meses à frente`);
  // "ganho" exige: teste significativo (Holm dentro da rodada) E erro menor no total E sem a pandemia
  const sigTest = (o) => o && o.p_holm != null && o.p_holm < 0.05;
  const sig = (o) => sigTest(o) && o.razao_rmse < 1 && o.razao_rmse_sem_pandemia < 1;
  const pct = (r) => `${r < 1 ? "−" : "+"}${fmtNum(Math.abs(r - 1) * 100, 1)}%`;
  const pTxt = (p) => (p < 0.01 ? "< 0,01" : "= " + fmtNum(p, 2));
  const JUROS = ["selic_mensal", "juro_real_exante", "juros_pj"];
  const robustCells = (a, filter) => a.candidatos.filter((c) => c.fora_da_amostra && filter(c))
    .flatMap((c) => H.filter((h) => sig(c.fora_da_amostra[h])).map((h) => ({ c, h, o: c.fora_da_amostra[h] })));
  const bestOf = (cells) => [...cells].sort((p, q) => p.o.razao_rmse - q.o.razao_rmse)[0];

  const summaryRows = list.map((a) => {
    const juros = robustCells(a, (c) => JUROS.includes(c.id));
    const outros = robustCells(a, (c) => !JUROS.includes(c.id));
    const b = bestOf(juros);
    return `<tr><td>${esc(a.alvo.rotulo)}<div class="sub" style="margin:0">${a.replicacao ? "replicação: hipóteses fixadas antes de ver este alvo" : "análise original"}</div></td>
      <td>${juros.length ? `<b>Sim</b>, ${new Set(juros.map((x) => x.c.rotulo)).size} de 6 medidas de juros` : "Não"}</td>
      <td>${b ? `${esc(b.c.rotulo)}: erro ${pct(b.o.razao_rmse)} em ${hLabel(b.h).toLowerCase()} (sem a pandemia, ${pct(b.o.razao_rmse_sem_pandemia)})` : "–"}</td>
      <td>${outros.length ? [...new Set(outros.map((x) => esc(x.c.rotulo)))].join("; ") : "Nenhum"}</td></tr>`;
  }).join("");

  box.innerHTML = `
    <section class="sec">
      <div class="sec-head"><h2>Indicadores antecedentes por setor</h2>
        <span class="sub">${list.length} séries-alvo · ${list[0].n_testes} testes cada · avaliação a partir de ${list[0].inicio_avaliacao.slice(0, 7)}</span></div>
      <div style="overflow-x:auto"><table class="tbl">
        <tr><th>Série-alvo</th><th>Os juros antecipam?</th><th>Melhor resultado dos juros</th><th>Outros indicadores robustos</th></tr>
        ${summaryRows}
      </table></div>
      <p class="aside">${(() => {
        // força do sinal = quantas das 6 medidas de juros têm ganho robusto em algum horizonte
        const n = (a) => new Set(robustCells(a, (c) => JUROS.includes(c.id)).map((x) => x.c.rotulo)).size;
        const nomes = (f) => list.filter(f).map((a) => esc(a.alvo.rotulo)).join("; ");
        const forte = list.filter((a) => n(a) >= 4), fraco = list.filter((a) => n(a) >= 1 && n(a) < 4), nada = list.filter((a) => n(a) === 0);
        return [
          forte.length ? `Sinal dos juros <b>forte</b> (4 ou mais das 6 medidas) em ${forte.length} de ${list.length} séries: ${nomes((a) => n(a) >= 4)}.` : "",
          fraco.length ? `<b>Fraco</b> (1 a 3 medidas) em ${nomes((a) => n(a) >= 1 && n(a) < 4)}.` : "",
          nada.length ? `<b>Ausente</b> em ${nomes((a) => n(a) === 0)}.` : "",
          "Um sinal que depende da série escolhida não é regra geral do setor.",
        ].filter(Boolean).join(" ");
      })()}</p>
      <div class="toolbar" style="margin-top:20px">${tabsHtml("alvo", list.map((a) => ({ id: a.setor, rotulo: a.alvo.rotulo.split(" – ")[0] + " · " + a.alvo.rotulo.split(": ").pop().split(" – ").pop() })), list[0].setor)}</div>
      <div id="analise-detalhe"></div>
    </section>`;

  let chart = null;
  const renderOne = (a) => {
    if (chart) { chart.dispose(); state.charts = state.charts.filter((x) => x !== chart); }
    const round = (r) => a.candidatos.filter((c) => c.rodada === r && c.fora_da_amostra);
    const gains = (r) => round(r).filter((c) => H.some((h) => sig(c.fora_da_amostra[h])));
    const fragile = (r) => round(r).filter((c) => H.some((h) => sigTest(c.fora_da_amostra[h])) && !H.some((h) => sig(c.fora_da_amostra[h])));
    const coincident = round(1).filter((c) => Math.max(...c.correlacoes.map((x) => Math.abs(x.corr))) >= 0.25
      && [...c.correlacoes].sort((p, q) => Math.abs(q.corr) - Math.abs(p.corr))[0].defasagem === 0 && !H.some((h) => sig(c.fora_da_amostra[h])));
    const gainLine = (c) => {
      const b = bestOf(H.filter((h) => sig(c.fora_da_amostra[h])).map((h) => ({ c, h, o: c.fora_da_amostra[h] })));
      return `<li><b>${esc(c.rotulo)}</b>: erro ${pct(b.o.razao_rmse)} em ${hLabel(b.h).toLowerCase()} (p ${pTxt(b.o.p_holm)}); sem a pandemia, ${pct(b.o.razao_rmse_sem_pandemia)}.</li>`;
    };
    const r2Label = a.replicacao ? "também fixada antes de ver este alvo" : "formulada <em>depois</em> da rodada 1; leia com mais cautela";
    const findings = `
      <p><b>Rodada 1</b> (hipóteses gerais):</p>
      ${gains(1).length ? `<ul>${gains(1).map(gainLine).join("")}</ul>` : "<p>Nenhum indicador reduziu o erro de forma robusta.</p>"}
      ${coincident.length ? `<p>${coincident.map((c) => esc(c.rotulo.split(" (")[0])).join(", ")} andam <b>junto</b> com o setor (correlação máxima no mesmo mês), mas não antecipam.</p>` : ""}
      <p><b>Rodada 2</b> (canal de juros, ${r2Label}):</p>
      ${gains(2).length ? `<ul>${gains(2).map(gainLine).join("")}</ul>` : "<p>Nenhuma medida reduziu o erro de forma robusta.</p>"}
      ${[...fragile(1), ...fragile(2)].map((c) => `<p>${esc(c.rotulo)}: teste significativo, mas o erro <b>não cai de forma robusta</b>. Não conta como melhora.</p>`).join("")}`;
    document.getElementById("analise-detalhe").innerHTML = `
      <div class="cols">
        <figure class="fig">
          <p class="fig-title">${esc(a.alvo.rotulo)}</p>
          <p class="fig-sub">variação em 12 meses, log × 100</p>
          <div id="alvoChart" class="chart" style="height:260px"></div>
          <p class="source">${esc(a.alvo.fonte || "")}. Uso pessoal. Análise executada em ${fmtTs(a.executado_em)}.</p>
        </figure>
        <div class="prose">${findings}</div>
      </div>
      <div style="overflow-x:auto;margin-top:12px">
      <table class="tbl">
        <tr><th>Indicador</th><th class="r">Correlação máxima</th>${H.map((h) => `<th class="r">Variação do erro, ${hLabel(h).toLowerCase()}</th>`).join("")}</tr>
        ${a.candidatos.map((c) => {
          if (!c.correlacoes) return `<tr><td>${esc(c.rotulo)}</td><td colspan="${H.length + 1}">${esc(c.erro || "")}</td></tr>`;
          const best = [...c.correlacoes].sort((p, q) => Math.abs(q.corr) - Math.abs(p.corr))[0];
          return `<tr><td>${esc(c.rotulo)}<div class="sub" style="margin:0">rodada ${c.rodada} · ${esc(c.transformacao)} · ${c.defasagem_divulgacao ? `${c.defasagem_divulgacao} ${c.defasagem_divulgacao === 1 ? "mês" : "meses"} de defasagem` : "sem defasagem"}</div></td>
            <td class="r">${fmtNum(best.corr, 2)} ${best.defasagem ? `(${best.defasagem}m antes)` : "(mesmo mês)"}</td>
            ${H.map((h) => { const o = c.fora_da_amostra[h];
              return `<td class="r">${o?.razao_rmse != null ? `${sig(o) ? "<b>" : ""}${pct(o.razao_rmse)}${sig(o) ? "</b>" : ""}<div class="sub" style="margin:0">p ${pTxt(o.p_holm)} · sem pand. ${pct(o.razao_rmse_sem_pandemia)}</div>` : "–"}</td>`; }).join("")}
          </tr>`; }).join("")}
      </table></div>
      <p class="sub" style="margin-top:8px">Variação do erro = RMSE do modelo com o indicador ÷ RMSE do modelo só com o histórico do setor − 1. Negativo = o indicador ajuda.
      Em negrito: significativo a 5% (Clark-West, Holm dentro da rodada) e com erro menor no total e sem a pandemia.</p>
      <div class="aside"><b>Como ler.</b> Cada previsão usa só o que estaria publicado na data (alvo com ${a.alvo.defasagem_divulgacao} meses de atraso; sondagens, Selic e câmbio no próprio mês).
      Os modelos são reestimados a cada mês. Associação preditiva não é causalidade, e as defasagens de divulgação são premissas a conferir.</div>`;
    chart = drawChart(document.getElementById("alvoChart"), { series: [{ name: "Variação em 12 meses", data: a.alvo.serie, color: "--series-1" }], unit: "%" });
  };
  renderOne(list[0]);
  onTabs("alvo", (v) => renderOne(list.find((a) => a.setor === v)));
}

/* ---------- Radar Brasil ---------- */
const TEMAS = [
  ["inflacao", "Inflação"], ["juros", "Juros"], ["cambio", "Câmbio"], ["atividade", "Atividade"],
  ["trabalho", "Trabalho"], ["renda", "Renda"], ["credito", "Crédito e endividamento"],
  ["industria", "Indústria de transformação"], ["eletrico", "Setor elétrico e eletroeletrônico"],
  ["maquinas", "Máquinas e equipamentos"], ["construcao", "Construção"], ["outros", "Outras séries importadas"],
];

function indicatorRow(s) {
  if (!s.ultimo) return `<tr><td colspan="5"><div class="name">${esc(s.nome)}</div><div class="meta">sem dados</div></td></tr>`;
  // taxas variam em p.p. e índices de difusão em pontos; níveis variam em %
  const pct = s.unidade.startsWith("%"), pts = s.unidade === "pontos";
  let chg = "–";
  if (s.anterior) {
    const d = pct || pts ? s.ultimo.valor - s.anterior.valor : (s.ultimo.valor / s.anterior.valor - 1) * 100;
    const arrow = d > 0 ? "▲" : d < 0 ? "▼" : "";
    chg = `<span title="contra ${fmtDate(s.anterior.data, s.periodicidade)}">${arrow} ${fmtNum(Math.abs(d))} ${pct ? "p.p." : pts ? "pts" : "%"}</span>`;
  }
  return `
    <tr class="row" data-href="#/serie/${s.id}">
      <td><a class="name" href="#/serie/${s.id}" style="text-decoration:none">${esc(s.nome)}</a>
        <div class="meta"><span>${esc(sourceLabel(s))}</span>${flags(s)}</div></td>
      <td class="val">${fmtNum(s.ultimo.valor)}<span class="unit">${esc(s.unidade)}</span></td>
      <td class="ref ref-col">${fmtDate(s.ultimo.data, s.periodicidade)}</td>
      <td class="chg">${chg}</td>
      <td class="spark">${sparkline(s.spark || [])}</td>
    </tr>`;
}

async function pageRadar() {
  const cat = state.catalog.filter((s) => s.modulo === "radar_brasil");
  const lastFetch = cat.map((s) => s.versao?.fetched_at).filter(Boolean).sort().pop();
  const opts = cat.filter((s) => s.ultimo).map((s) => `<option value="${s.id}">${esc(s.nome)}</option>`).join("");
  $app.innerHTML = `
    ${lede("Módulo I", "Radar Brasil",
      "Os principais indicadores da economia brasileira, direto das fontes oficiais. Selecione uma linha para ver a definição, o histórico de coletas e a série completa.",
      `${cat.length} séries · última coleta em ${lastFetch ? fmtTs(lastFetch) : "–"}`)}

    <section class="sec">
      <table class="ind">
        <thead><tr><th>Indicador</th><th class="r">Último</th><th class="r ref-col">Referência</th><th class="r">Variação</th><th class="spark">3 anos</th></tr></thead>
        <tbody>
          ${TEMAS.map(([t, nome]) => {
            const items = cat.filter((s) => s.tema === t);
            return items.length ? `<tr class="group"><td colspan="5">${nome}</td></tr>${items.map(indicatorRow).join("")}` : "";
          }).join("")}
        </tbody>
      </table>
      <p class="sub" style="margin-top:10px">Variação contra a observação anterior: em pontos percentuais para taxas, em % para níveis.${cat.some((s) => !s.metadados_conferidos) ? ' <span class="flag warn">A conferir</span> indica nome ou unidade ainda não checados contra a ficha oficial da série.' : " Nomes e unidades conferidos com as fontes oficiais."}</p>
    </section>

    <section class="sec" id="explorar">
      <div class="sec-head"><h2>Explorar e comparar</h2></div>
      <div class="toolbar">
        ${field("Indicador", `<select id="exA">${opts}</select>`)}
        ${field("Cálculo", `<select id="exTA"></select>`)}
        ${field("Comparar com", `<select id="exB"><option value="">Nenhum</option>${opts}</select>`)}
        <span id="exTBwrap" hidden>${field("Cálculo", `<select id="exTB"></select>`)}</span>
        ${tabsHtml("per", PERIODOS, "10a")}
      </div>
      <figure class="fig"><p class="fig-title" id="tA"></p><p class="fig-sub" id="uA"></p><div id="cA" class="chart"></div><p class="source" id="mA"></p></figure>
      <figure class="fig" id="wrapB" hidden><p class="fig-title" id="tB"></p><p class="fig-sub" id="uB"></p><div id="cB" class="chart"></div><p class="source" id="mB"></p>
        <p class="aside">Cada série tem o próprio gráfico e a própria escala; o eixo do tempo é sincronizado. Movimentos parecidos não demonstram relação causal. Os testes estatísticos entram na próxima fase.</p>
      </figure>
    </section>

    <section class="sec">
      <div class="sec-head"><h2>Poder de compra</h2></div>
      <div class="multiples">
        <figure class="fig"><p class="fig-title">Rendimento médio real habitual</p><p class="fig-sub">R$ a preços do último trimestre</p><div class="chart sm" id="pc1"></div><p class="source" id="pc1m"></p></figure>
        <figure class="fig"><p class="fig-title">Rendimento real, variação anual</p><p class="fig-sub">% contra o mesmo trimestre do ano anterior</p><div class="chart sm" id="pc2"></div><p class="source" id="pc2m"></p></figure>
      </div>
      <p class="aside">O rendimento da PNAD já vem deflacionado pelo IBGE. Ele mede o rendimento habitual do trabalho principal de quem está ocupado; não inclui transferências nem quem está desocupado.</p>
    </section>

    <section class="sec">
      <div class="sec-head"><h2>Pressão financeira das famílias</h2></div>
      <div class="multiples">
        ${[["juros_pf", "Juros médios, pessoa física", "% ao ano"], ["comprometimento_renda", "Comprometimento de renda", "% da renda com o serviço da dívida"],
           ["endividamento_familias", "Endividamento", "% da renda acumulada em 12 meses"], ["inadimplencia_pf", "Inadimplência, pessoa física", "% da carteira com atraso acima de 90 dias"]]
          .map(([id, t, u], i) => `<figure class="fig"><p class="fig-title"><a href="#/serie/${id}">${t}</a></p><p class="fig-sub">${u}</p><div class="chart sm" id="pf${i}"></div><p class="source" id="pf${i}m"></p></figure>`).join("")}
      </div>
      <p class="aside">Estes são os insumos do Índice de Pressão Financeira das Famílias (IPFF), um indicador experimental em desenvolvimento. A inadimplência vai servir para validar o índice, não para compô-lo.</p>
    </section>`;

  document.querySelectorAll("tr.row").forEach((tr) => tr.onclick = (e) => { if (e.target.tagName !== "A") location.hash = tr.dataset.href; });

  const byId = Object.fromEntries(cat.map((s) => [s.id, s]));
  const fillT = (sel, id) => { sel.innerHTML = (byId[id]?.transformacoes || []).map((t) => `<option value="${t.id}">${esc(t.rotulo)}</option>`).join(""); };
  const exA = document.getElementById("exA"), exTA = document.getElementById("exTA");
  const exB = document.getElementById("exB"), exTB = document.getElementById("exTB");
  let per = "10a";
  if (byId.ipca_mensal) exA.value = "ipca_mensal";
  fillT(exTA, exA.value);
  if (byId.ipca_mensal) exTA.value = "acum_12m";

  let explorerCharts = [];
  async function drawExplorer() {
    explorerCharts.forEach((c) => { c.dispose(); state.charts = state.charts.filter((x) => x !== c); });
    explorerCharts = [];
    const inicio = periodStart(per);
    const a = await loadSeries(exA.value, exTA.value, inicio);
    document.getElementById("tA").textContent = a.serie.nome;
    document.getElementById("uA").textContent = `${a.transformacao.rotulo}, ${a.transformacao.unidade}`;
    explorerCharts.push(seriesChart(document.getElementById("cA"), a, { group: "explorar" }));
    document.getElementById("mA").innerHTML = sourceLine(a);
    const wrapB = document.getElementById("wrapB");
    if (exB.value) {
      wrapB.hidden = false; document.getElementById("exTBwrap").hidden = false;
      const b = await loadSeries(exB.value, exTB.value, inicio);
      document.getElementById("tB").textContent = b.serie.nome;
      document.getElementById("uB").textContent = `${b.transformacao.rotulo}, ${b.transformacao.unidade}`;
      explorerCharts.push(seriesChart(document.getElementById("cB"), b, { color: "--series-2", group: "explorar" }));
      document.getElementById("mB").innerHTML = sourceLine(b);
    } else { wrapB.hidden = true; document.getElementById("exTBwrap").hidden = true; }
  }
  exA.onchange = () => { fillT(exTA, exA.value); drawExplorer(); };
  exTA.onchange = drawExplorer;
  exB.onchange = () => { fillT(exTB, exB.value); drawExplorer(); };
  exTB.onchange = drawExplorer;
  onTabs("per", (v) => { per = v; drawExplorer(); });

  const small = async (el, id, tr) => {
    if (!byId[id]?.ultimo) { document.getElementById(el).innerHTML = `<div class="empty">Sem dados.</div>`; return; }
    const r = await loadSeries(id, tr, "2012-01-01");
    seriesChart(document.getElementById(el), r);
    document.getElementById(el + "m").innerHTML = sourceLine(r);
  };
  await Promise.all([
    drawExplorer(),
    small("pc1", "rendimento_real", "nivel"), small("pc2", "rendimento_real", "var_anual"),
    small("pf0", "juros_pf", "nivel"), small("pf1", "comprometimento_renda", "nivel"),
    small("pf2", "endividamento_familias", "nivel"), small("pf3", "inadimplencia_pf", "nivel"),
  ]);
}

/* ---------- página de série ---------- */
async function pageSerie(id) {
  const s = state.catalog.find((x) => x.id === id);
  if (!s) { $app.innerHTML = `<div class="empty">Série não encontrada.</div>`; return; }
  const versoes = await api(`/api/series/${id}/versoes`);
  const meta = [
    ["Identificador", `<span class="mono">${esc(s.id)}</span>`],
    ["Definição", esc(s.descricao)],
    ["Instituição produtora", esc(s.instituicao)],
    ["Fonte de aquisição", esc(sourceLabel(s)) + (s.versao ? `, <a href="${esc(s.versao.source_url)}" target="_blank" rel="noopener">endpoint</a>` : "")],
    ["Unidade", esc(s.unidade)],
    ["Periodicidade", esc(s.periodicidade)],
    ["Cobertura", esc(s.geografia)],
    ["Período", s.versao ? `${fmtDate(s.versao.first_date, s.periodicidade)} a ${fmtDate(s.versao.last_date, s.periodicidade)}, ${s.versao.n_obs} observações` : "–"],
    ["Licença", esc(s.licenca)],
    ["Uso permitido", esc(s.uso)],
    ...(s.extra?.nome_oficial ? [["Nome oficial", `${esc(s.extra.nome_oficial)}<div class="sub" style="margin:0">unidade oficial: ${esc(s.extra.unidade_oficial || "–")} · periodicidade: ${esc(s.extra.periodicidade_oficial || "–")}</div>`]] : []),
    ["Metadados conferidos", s.metadados_conferidos
      ? `Sim${s.extra?.metadados_conferidos_em ? `, em ${esc(s.extra.metadados_conferidos_em)}` : ""}${s.extra?.fonte_metadados ? `<div class="sub" style="margin:0">${esc(s.extra.fonte_metadados)}</div>` : ""}`
      : `<span class="flag warn">Não</span> Conferir nome, unidade e ajuste sazonal na ficha oficial.`],
  ];
  const tema = (TEMAS.find(([t]) => t === s.tema) || [, s.tema])[1];
  const route = MOD_ROUTE[s.modulo] || "radar";
  const modNome = MODULOS.find((m) => m.id === route).nome;
  $app.innerHTML = `
    ${lede(`<a href="#/${route}">${modNome}</a> · ${esc(s.instituicao)}`, esc(s.nome), esc(s.descricao || tema), `${esc(sourceLabel(s))} ${flags(s)}`)}
    <section class="sec">
      <div class="toolbar">
        ${field("Cálculo", `<select id="tr">${s.transformacoes.map((t) => `<option value="${t.id}">${esc(t.rotulo)}</option>`).join("")}</select>`)}
        ${tabsHtml("per", PERIODOS, "tudo")}
        <div class="push">
          <button class="linkbtn" id="tbl" type="button">Ver tabela</button>
          ${s.uso === "publico" ? `<button class="linkbtn" id="csv" type="button">Baixar CSV</button>` : ""}
        </div>
      </div>
      <figure class="fig"><p class="fig-title" id="ttl"></p><p class="fig-sub" id="unit"></p><div id="ch" class="chart"></div><p class="source" id="meta"></p></figure>
      <div class="scroll" id="tblwrap" hidden></div>
    </section>
    <section class="sec cols">
      <div><div class="sec-head"><h2>Metadados</h2></div><dl class="meta-list">${meta.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl></div>
      <div><div class="sec-head"><h2>Histórico de coletas</h2></div>
        <p class="sub">Uma versão nova só é criada quando os dados mudam. "Revisados" conta valores passados que a fonte alterou.</p>
        <div class="scroll"><table class="tbl">
          <tr><th>Versão</th><th>Coletada em</th><th class="r">Obs.</th><th class="r">Novas</th><th class="r">Revisadas</th></tr>
          ${versoes.map((v) => `<tr><td>${v.id}</td><td>${fmtTs(v.fetched_at)}</td><td class="r">${v.n_obs}</td><td class="r">${v.n_new}</td><td class="r">${v.n_revised}</td></tr>`).join("")}
        </table></div>
        ${versoes[0] ? `<p class="source" style="border:0">Arquivo bruto <span class="mono">${esc(versoes[0].raw_path)}</span><br>SHA-256 <span class="mono" style="word-break:break-all">${esc(versoes[0].raw_sha256)}</span></p>` : ""}
      </div>
    </section>`;

  let per = "tudo", last = null;
  const tr = document.getElementById("tr");
  async function draw() {
    disposeCharts();
    last = await loadSeries(id, tr.value, periodStart(per));
    document.getElementById("ttl").textContent = last.transformacao.rotulo;
    document.getElementById("unit").textContent = last.transformacao.unidade;
    seriesChart(document.getElementById("ch"), last);
    document.getElementById("meta").innerHTML = sourceLine(last);
    if (!document.getElementById("tblwrap").hidden) renderTable();
  }
  function renderTable() {
    document.getElementById("tblwrap").innerHTML = `<table class="tbl"><tr><th>Período</th><th class="r">${esc(last.transformacao.unidade)}</th></tr>${
      last.dados.slice().reverse().map(([d, v]) => `<tr><td>${fmtDate(d, last.serie.periodicidade)}</td><td class="r">${fmtNum(v)}</td></tr>`).join("")}</table>`;
  }
  tr.onchange = draw;
  onTabs("per", (v) => { per = v; draw(); });
  document.getElementById("tbl").onclick = (e) => {
    const tw = document.getElementById("tblwrap"); tw.hidden = !tw.hidden;
    e.target.textContent = tw.hidden ? "Ver tabela" : "Ocultar tabela";
    if (!tw.hidden) renderTable();
  };
  const csvBtn = document.getElementById("csv");
  if (csvBtn) csvBtn.onclick = () => {
    const head = `# ${last.serie.nome} | ${last.transformacao.rotulo} | fonte: ${last.serie.instituicao} via ${sourceLabel(last.serie)} | coletado ${last.versao.fetched_at}\n`;
    const body = "data;valor\n" + last.dados.map(([d, v]) => `${d};${v == null ? "" : String(v).replace(".", ",")}`).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([head + body], { type: "text/csv;charset=utf-8" }));
    a.download = `${id}_${tr.value}.csv`; a.click(); URL.revokeObjectURL(a.href);
  };
  await draw();
}

/* ---------- MacroForecast ---------- */
const MODEL_COLOR = { sarima: "--series-1", focus_mediana: "--series-2", sazonal_ingenuo: "--series-3", ingenuo: "--series-4" };
const MODEL_ORDER = ["sarima", "focus_mediana", "sazonal_ingenuo", "ingenuo"];

function legendHtml(items) {
  return `<div class="legend">${items.map((i) => `<span><i class="${i.dashed ? "dash" : ""}" style="${i.dashed ? `border-color:var(${i.color})` : `background:var(${i.color})`}"></i>${esc(i.name)}</span>`).join("")}</div>`;
}

const FAIXA_TXT = { parametrica: "paramétrica (fórmula do SARIMA)", empirica_v1: "empírica, todos os erros", empirica_v2_60m: "empírica, erros dos últimos 60 meses" };
const faixaTxt = (m) => FAIXA_TXT[m] || m || "–";

async function pageForecast() {
  const [fc, ipca] = await Promise.all([api("/api/previsoes/ipca"), loadSeries("ipca_mensal", "nivel")]);
  const M = fc.modelos;
  const nome = (k) => M[k]?.rotulo || k;
  const origem = fc.ultima_origem;
  const atuais = fc.atuais;
  const models = MODEL_ORDER.filter((k) => atuais.some((r) => r.modelo === k));
  const alvos = [...new Set(atuais.map((r) => r.alvo))].sort();
  const get = (m, a) => atuais.find((r) => r.modelo === m && r.alvo === a);
  const acum = (m) => {
    const vals = alvos.map((a) => get(m, a)?.valor);
    return vals.length === 12 && vals.every((v) => v != null) ? (vals.reduce((p, v) => p * (1 + v / 100), 1) - 1) * 100 : null;
  };
  const bt = fc.backtest;
  const btRows = bt ? bt.resumo : [];
  const btGet = (m, h) => btRows.find((r) => r.modelo === m && r.h === h);
  const registered = atuais[0]?.registrado_em;

  // interpretação calculada a partir dos números do backtest
  let insight = "";
  // cobertura da faixa do SARIMA: paramétrica (antes) × empírica (depois), e o holdout 2021–26
  const covE = btRows.filter((r) => r.modelo === "sarima" && r.cobertura80_emp != null);
  const covEAvg = covE.reduce((s, r) => s + r.cobertura80_emp, 0) / (covE.length || 1);
  const ho = bt?.faixa_selecao?.v2_ultimos60m?.holdout_2021_2026;
  const hoAvg = ho ? Object.values(ho).reduce((s, v) => s + v[0], 0) / Object.values(ho).length : null;
  if (bt) {
    const best = (h) => MODEL_ORDER.map((m) => btGet(m, h)).filter(Boolean).sort((a, b) => a.rmse - b.rmse)[0];
    const b1 = best(1), b12 = best(12);
    const cov = btRows.filter((r) => r.modelo === "sarima" && r.cobertura80 != null);
    const covAvg = cov.reduce((s, r) => s + r.cobertura80, 0) / (cov.length || 1);

    const s1 = btGet("sarima", 1), f1 = btGet("focus_mediana", 1), s12 = btGet("sarima", 12), f12 = btGet("focus_mediana", 12);
    insight = `
      <p>Um mês à frente, o menor erro é de <b>${esc(nome(b1.modelo))}</b> (RMSE ${fmtNum(b1.rmse, 2)} p.p.).
      ${f1 && s1 ? `O Focus erra ${fmtNum((1 - f1.rmse / s1.rmse) * 100, 0)}% menos que o SARIMA nesse horizonte, o que é esperado: os analistas já conhecem o IPCA-15 e preços de alta frequência.` : ""}</p>
      <p>${f12 && s12 && Math.abs(s12.rmse - f12.rmse) < 0.01
        ? `Doze meses à frente, SARIMA e Focus ficam <b>praticamente empatados</b> (RMSE de ${fmtNum(s12.rmse, 2)} e ${fmtNum(f12.rmse, 2)} p.p.): a vantagem informacional dos analistas some com o horizonte.`
        : `Doze meses à frente, o menor erro é de <b>${esc(nome(b12.modelo))}</b> (RMSE ${fmtNum(b12.rmse, 2)} p.p.).`}</p>
      <p>A faixa de 80% da fórmula do SARIMA conteve o valor realizado em só <b>${fmtNum(covAvg * 100, 0)}%</b> dos casos: estreita demais.
      ${covE.length ? `A faixa empírica (erros do próprio SARIMA nos últimos 60 meses, por horizonte) cobre ${fmtNum(covEAvg * 100, 0)}% em 2016–2026${hoAvg != null ? ` e <b>${fmtNum(hoAvg * 100, 0)}%</b> em 2021–2026, período que não entrou na escolha do método` : ""}. Ela vale para as previsões novas; as já registradas mantêm a faixa original.` : ""}</p>`;
  }

  $app.innerHTML = `
    ${lede("Módulo II", "MacroForecast",
      "Previsões da variação mensal do IPCA, registradas antes da divulgação e comparadas à mediana do Focus. Nenhuma previsão é apagada ou corrigida depois.",
      origem ? `Previsões vigentes feitas com dados até ${fmtDate(origem, "mensal")} · registradas em ${fmtTs(registered)}` : "")}

    <section class="sec">
      <div class="sec-head"><h2>Previsões vigentes</h2></div>
      ${origem ? `
      <figure class="fig">
        <p class="fig-title">IPCA, variação mensal: observado e previsto</p>
        <p class="fig-sub">% ao mês · faixa sombreada: 80% do SARIMA, ${esc(faixaTxt(get("sarima", alvos[0])?.metodo_faixa))}</p>
        ${legendHtml([{ name: "Observado", color: "--ink" }, ...models.map((m) => ({ name: nome(m), color: MODEL_COLOR[m], dashed: true }))])}
        <div id="fcChart" class="chart"></div>
        <p class="source">Observado: IBGE, via BCB · SGS 433. Focus: mediana da pesquisa vigente no dia do registro (BCB, Expectativas de Mercado). Modelos: ver método abaixo.</p>
      </figure>
      <div class="scroll" style="max-height:none;overflow-x:auto">
        <table class="tbl">
          <tr><th>Mês-alvo</th>${models.map((m) => `<th class="r">${esc(nome(m))}</th>`).join("")}<th class="r">SARIMA, faixa 80%<div class="sub" style="margin:0;text-transform:none;letter-spacing:0;font-weight:400">${esc(faixaTxt(get("sarima", alvos[0])?.metodo_faixa))}</div></th></tr>
          ${alvos.map((a) => `<tr><td>${fmtDate(a, "mensal")}</td>${models.map((m) => `<td class="r">${fmtNum(get(m, a)?.valor)}</td>`).join("")}
            <td class="r">${get("sarima", a)?.lo80 != null ? `${fmtNum(get("sarima", a).lo80)} a ${fmtNum(get("sarima", a).hi80)}` : "–"}</td></tr>`).join("")}
          <tr><td><b>Acumulado em 12 meses</b></td>${models.map((m) => `<td class="r"><b>${fmtNum(acum(m))}</b></td>`).join("")}<td></td></tr>
        </table>
      </div>
      <p class="sub" style="margin-top:8px">O acumulado em 12 meses compõe as previsões pontuais mensais. É uma aproximação, sem intervalo de confiança.</p>`
      : `<p class="empty">Nenhuma previsão registrada. Rode <code>python -m econatlas prever</code>.</p>`}
    </section>

    <section class="sec">
      <div class="sec-head"><h2>Placar ao vivo</h2><span class="sub">${fc.registro.length} previsões registradas</span></div>
      ${fc.placar.length ? `
        <table class="tbl"><tr><th>Modelo</th><th class="r">Previsões avaliadas</th><th class="r">Erro médio absoluto (p.p.)</th><th class="r">RMSE (p.p.)</th><th class="r">Faixa 80%: realizado dentro</th></tr>
        ${fc.placar.sort((a, b) => a.rmse - b.rmse).map((r) => `<tr><td>${esc(nome(r.modelo))}</td><td class="r">${r.n}</td><td class="r">${fmtNum(r.mae, 3)}</td><td class="r">${fmtNum(r.rmse, 3)}</td>
          <td class="r">${(r.cobertura80 || []).length ? r.cobertura80.map((c) => `${fmtNum(c.cobertura * 100, 0)}% de ${c.n}<div class="sub" style="margin:0">${esc(faixaTxt(c.metodo))}</div>`).join("") : "–"}</td></tr>`).join("")}</table>
        <p class="sub">A cobertura ao vivo é separada por método de faixa: as previsões registradas com a faixa antiga continuam avaliadas pela faixa que tinham.</p>`
      : `<div class="prose"><p>Nenhuma previsão chegou à data de avaliação ainda. A primeira comparação acontece quando o IBGE divulgar o IPCA de ${alvos[0] ? fmtDate(alvos[0], "mensal") : "–"}.
         A partir daí, este placar se acumula todo mês, com o erro de cada modelo e a fração de vezes em que o realizado caiu dentro da faixa de 80% (meta: 80%).
         É o único teste que não pode ser refeito com o resultado conhecido.</p></div>`}
      <p style="margin-top:12px"><button class="linkbtn" id="showReg" type="button">Ver registro completo</button></p>
      <div class="scroll" id="reg" hidden></div>
    </section>

    <section class="sec">
      <div class="sec-head"><h2>Backtest</h2>${bt ? `<span class="sub">Origens de ${bt.origens[0]} a ${bt.origens[1]} · executado em ${fmtTs(bt.executado_em)}</span>` : ""}</div>
      ${bt ? `
      <div class="cols">
        <figure class="fig">
          <p class="fig-title">Erro de previsão por horizonte</p>
          <p class="fig-sub">RMSE em p.p., só nos casos em que todos os modelos têm previsão</p>
          ${legendHtml(MODEL_ORDER.map((m) => ({ name: nome(m), color: MODEL_COLOR[m] })))}
          <div id="btChart" class="chart" style="height:300px"></div>
        </figure>
        <div class="prose">${insight}</div>
      </div>
      <table class="tbl" style="margin-top:16px">
        <tr><th>Modelo</th>${[1, 3, 6, 12].map((h) => `<th class="r">RMSE ${h}m</th>`).join("")}<th class="r">Viés 1m</th><th class="r">Casos (1m)</th></tr>
        ${MODEL_ORDER.map((m) => `<tr><td>${esc(nome(m))}</td>${[1, 3, 6, 12].map((h) => `<td class="r">${fmtNum(btGet(m, h)?.rmse, 3)}</td>`).join("")}
          <td class="r">${fmtNum(btGet(m, 1)?.vies, 3)}</td><td class="r">${btGet(m, 1)?.n ?? "–"}</td></tr>`).join("")}
      </table>
      ${covE.length ? `
      <h3 style="margin-top:24px">Faixa de 80% do SARIMA: cobertura por horizonte, antes e depois</h3>
      <p class="sub">Fração das previsões em que o realizado caiu dentro da faixa. Meta: 80%.</p>
      <div style="overflow-x:auto"><table class="tbl">
        <tr><th>Horizonte</th><th class="r">Antes: paramétrica, 2016–26</th><th class="r">Depois: empírica 60 meses, 2016–26</th><th class="r">Depois, só 2021–26 (fora da escolha)</th><th class="r">Casos</th></tr>
        ${btRows.filter((r) => r.modelo === "sarima").sort((a, b) => a.h - b.h).map((r) => `<tr><td>${r.h} ${r.h === 1 ? "mês" : "meses"}</td>
          <td class="r">${fmtNum(r.cobertura80 * 100, 0)}%</td><td class="r">${r.cobertura80_emp != null ? fmtNum(r.cobertura80_emp * 100, 0) + "%" : "–"}</td>
          <td class="r"><b>${ho?.[String(r.h)] ? fmtNum(ho[String(r.h)][0] * 100, 0) + "%" : "–"}</b></td><td class="r">${r.n}</td></tr>`).join("")}
      </table></div>
      <p class="aside">A faixa da fórmula do SARIMA supõe que o erro tem sempre o mesmo tamanho, mas o erro do modelo dobrou de patamar depois de 2016.
      A faixa empírica usa os próprios erros recentes do SARIMA, por horizonte e só os já conhecidos na data. A janela de 60 meses foi escolhida entre três variantes declaradas antes,
      olhando só 2016–2020; o resultado de 2021–2026 não participou da escolha. Em 2016–2020 todas as variantes ficaram perto de 60%: os erros cresceram mais rápido do que qualquer janela acompanha.</p>` : ""}` : `<p class="empty">Backtest ainda não executado. Rode <code>python -m econatlas backtest</code>.</p>`}
    </section>

    <section class="sec prose">
      <div class="sec-head"><h2>Método e limitações</h2></div>
      <ul>
        ${MODEL_ORDER.filter((m) => M[m]).map((m) => `<li><b>${esc(nome(m))}</b>: <code>${esc(M[m].spec)}</code></li>`).join("")}
        <li>As especificações foram fixadas antes do backtest, para não escolher o modelo olhando o resultado.</li>
        <li>No backtest, cada origem usa só dados até aquele mês. O Focus é tomado da última pesquisa até o dia 15 do mês seguinte, quando o IPCA da origem já é conhecido.</li>
        <li>O backtest usa a versão atual da série, não as versões da época. Para o IPCA isso quase não pesa, porque a série não é revisada.</li>
        <li>O registro é imutável: o banco recusa alterações e exclusões. Para a mesma origem, vale a primeira previsão.</li>
        <li>Estas são projeções estatísticas, não recomendações. Choques de preços administrados, câmbio e clima não estão nos modelos.</li>
      </ul>
    </section>`;

  if (origem) {
    const obs = ipca.dados.filter((p) => p[0] >= alvos[0].replace(/^(\d{4})/, (y) => String(+y - 3)));
    const lastObs = obs[obs.length - 1];
    const sar = alvos.map((a) => get("sarima", a)).filter((r) => r && r.lo80 != null);
    drawChart(document.getElementById("fcChart"), {
      unit: "% a.m.",
      series: [
        { name: "Observado", data: obs, color: "--ink" },
        ...models.map((m) => ({ name: nome(m), color: MODEL_COLOR[m], dashed: true,
          data: [lastObs, ...alvos.map((a) => [a, get(m, a)?.valor ?? null])] })),
      ],
      band: sar.length ? { name: "SARIMA, faixa 80%", lo: sar.map((r) => [r.alvo, r.lo80]), hi: sar.map((r) => [r.alvo, r.hi80]) } : null,
    });
  }
  if (bt) {
    drawChart(document.getElementById("btChart"), {
      xType: "category", xLabel: "meses à frente", unit: "RMSE, p.p.",
      series: MODEL_ORDER.map((m) => ({ name: nome(m), color: MODEL_COLOR[m],
        data: Array.from({ length: 12 }, (_, i) => [String(i + 1), btGet(m, i + 1)?.rmse ?? null]) })),
    });
  }
  document.getElementById("showReg").onclick = (e) => {
    const box = document.getElementById("reg"); box.hidden = !box.hidden;
    e.target.textContent = box.hidden ? "Ver registro completo" : "Ocultar registro";
    if (!box.hidden && !box.innerHTML) {
      box.innerHTML = `<table class="tbl"><tr><th>Registrada em</th><th>Modelo</th><th>Origem</th><th>Alvo</th><th class="r">Previsto</th><th class="r">Realizado</th><th class="r">Erro</th></tr>
        ${fc.registro.map((r) => `<tr><td>${fmtTs(r.registrado_em)}</td><td>${esc(nome(r.modelo))}</td><td>${fmtDate(r.origem, "mensal")}</td><td>${fmtDate(r.alvo, "mensal")}</td>
          <td class="r">${fmtNum(r.valor)}</td><td class="r">${fmtNum(r.realizado)}</td><td class="r">${fmtNum(r.erro)}</td></tr>`).join("")}</table>`;
    }
  };
}

/* ---------- qualidade ---------- */
async function pageQualidade() {
  const checks = await api("/api/qualidade");
  const label = { ok: '<span class="flag ok">OK</span>', alerta: '<span class="flag warn">Alerta</span>', sem_dados: '<span class="flag muted">Sem dados</span>', erro: '<span class="flag crit">Erro</span>' };
  $app.innerHTML = `
    ${lede("Transparência", "Qualidade dos dados", "Verificações automáticas sobre a versão mais recente de cada série.")}
    <section class="sec"><table class="tbl">
      <tr><th>Verificação</th><th>Resultado</th><th>Detalhes</th></tr>
      ${checks.map((c) => {
        const det = Object.entries(c).filter(([k]) => !["verificacao", "resultado"].includes(k)).map(([k, v]) => `${esc(k.replace(/_/g, " "))}: ${esc(v)}`).join("<br>");
        return `<tr><td>${esc(c.verificacao)}</td><td>${label[c.resultado] || esc(c.resultado)}</td><td style="color:var(--ink-2)">${det}</td></tr>`;
      }).join("")}
    </table></section>`;
}

/* ---------- roteador ---------- */
let routeSeq = 0;  // cada navegação ganha um número; uma navegação antiga que termina depois não mexe na tela

async function route() {
  const my = ++routeSeq;
  disposeCharts();
  const [, page, arg] = (location.hash || "#/").split("/");
  const serieMod = page === "serie" && state.catalog ? state.catalog.find((s) => s.id === decodeURIComponent(arg))?.modulo : null;
  const active = page === "serie" ? (MOD_ROUTE[serieMod] || "radar") : page;
  document.querySelectorAll("[data-mod]").forEach((a) => a.classList.toggle("active", a.dataset.mod === active));
  try {
    if (!state.catalog) {
      state.catalog = await api("/api/catalogo");
      const last = state.catalog.map((s) => s.versao?.fetched_at).filter(Boolean).sort().pop();
      if (last) document.getElementById("stamp").textContent = `Dados de ${fmtTs(last)}`;
    }
    if (page === "radar") await pageRadar();
    else if (page === "serie") await pageSerie(decodeURIComponent(arg));
    else if (page === "forecast") await pageForecast();
    else if (page === "qualidade") await pageQualidade();
    else if (page === "setorial") { pagePlanned(page); await Promise.all([sectorForecasts(), sectorAnalysis()]); }
    else if (page === "mundo") pagePlanned(page);
    else pageHome();
  } catch (err) {
    if (my !== routeSeq) return;  // a página mudou no meio do carregamento: o erro é da tela antiga
    $app.innerHTML = `<div class="empty">Erro ao carregar: ${esc(err.message)}</div>`;
  }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);

document.getElementById("theme-toggle").onclick = () => {
  const dark = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = dark ? "light" : "dark";
  try { localStorage.setItem("econatlas-theme", document.documentElement.dataset.theme); } catch (e) {}
  route();
};

route();
