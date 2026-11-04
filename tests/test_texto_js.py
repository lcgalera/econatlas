"""Frases de comparação de erro (web/texto.js): a direção da diferença nunca pode ser escondida (D26).

Roda o módulo no Node. Sem Node instalado (como no Mac do autor, D1), o teste é pulado;
no GitHub Actions o Node vem no runner.
"""
import json
import shutil
import subprocess

import pytest

from rotzx import config

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node não instalado")


def _js(expr: str):
    script = f"const T = require({json.dumps(str(config.WEB_DIR / 'texto.js'))}); console.log(JSON.stringify({expr}));"
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_razao_menor_que_um_e_reducao_do_erro():
    assert _js("T.comparaErro(0.88).direcao") == "menor"
    assert _js("T.errou(0.88)") == "errou 12% menos"
    assert _js("T.erroRelativo(0.88)") == "12% menor"


def test_razao_maior_que_um_e_aumento_do_erro():
    # o bug antigo: |0,95 − 1| e |1,05 − 1| davam a mesma frase "errou 5% menos"
    assert _js("T.comparaErro(1.05).direcao") == "maior"
    assert _js("T.errou(1.05)") == "errou 5% mais"
    assert _js("T.erroRelativo(1.05)") == "5% maior"
    assert _js("T.errou(1.05)") != _js("T.errou(0.95)")


def test_razao_praticamente_igual_a_um():
    for r in (1.0, 0.996, 1.004):
        assert _js(f"T.comparaErro({r}).direcao") == "igual"
        assert _js(f"T.errou({r})") == "errou praticamente o mesmo"
        assert _js(f"T.erroRelativo({r})") == "praticamente igual"
    # logo acima do limiar já conta a direção
    assert _js("T.comparaErro(0.994).direcao") == "menor"
    assert _js("T.comparaErro(1.006).direcao") == "maior"


def test_razao_invalida_nao_vira_frase():
    for r in ("null", "0", "-1", "NaN", "Infinity"):
        assert _js(f"T.comparaErro({r})") is None
        assert _js(f"T.errou({r})") == "–"
