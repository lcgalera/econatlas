/* rotzx — frases de comparação de erro entre modelos.
   Sem DOM: roda no navegador (window.Texto) e no Node (tests/test_texto_js.py).
   Regra (D26): razão = RMSE do modelo ÷ RMSE da referência.
     razão < 1 → o modelo errou menos; razão > 1 → errou mais;
     |razão − 1| < LIMIAR_EMPATE → "praticamente o mesmo erro".
   A direção nunca é escondida por valor absoluto: o módulo da diferença só é usado depois de decidida a direção. */
(function (root) {
  "use strict";
  const LIMIAR_EMPATE = 0.005; // diferença de erro abaixo de 0,5% conta como empate

  const num = (v, d) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);

  // { direcao: "menor" | "maior" | "igual", pct: |razão − 1| × 100 } ou null se a razão não for válida
  function comparaErro(razao) {
    if (razao == null || !Number.isFinite(razao) || razao <= 0) return null;
    const dif = razao - 1;
    const direcao = Math.abs(dif) < LIMIAR_EMPATE ? "igual" : dif < 0 ? "menor" : "maior";
    return { razao, direcao, pct: Math.abs(dif) * 100 };
  }

  // "errou 12% menos" | "errou 5% mais" | "errou praticamente o mesmo"
  function errou(razao, casas = 0) {
    const c = comparaErro(razao);
    if (!c) return "–";
    if (c.direcao === "igual") return "errou praticamente o mesmo";
    return `errou ${num(c.pct, casas)}% ${c.direcao === "menor" ? "menos" : "mais"}`;
  }

  // "12% menor" | "5% maior" | "praticamente igual"
  function erroRelativo(razao, casas = 0) {
    const c = comparaErro(razao);
    if (!c) return "–";
    if (c.direcao === "igual") return "praticamente igual";
    return `${num(c.pct, casas)}% ${c.direcao}`;
  }

  const Texto = { LIMIAR_EMPATE, comparaErro, errou, erroRelativo };
  if (typeof module !== "undefined" && module.exports) module.exports = Texto;
  else root.Texto = Texto;
})(typeof globalThis !== "undefined" ? globalThis : this);
