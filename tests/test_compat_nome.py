"""Compatibilidade com o nome antigo (econatlas → rotzx, D35)."""
import subprocess
import sys

import rotzx
from rotzx import config, public_build, storage


def test_comando_antigo_redireciona_com_aviso():
    r = subprocess.run([sys.executable, "-m", "econatlas", "--help"], capture_output=True, text=True, cwd=config.ROOT)
    assert r.returncode == 0 and "usage: rotzx" in r.stdout
    assert "python -m rotzx" in r.stderr


def test_import_antigo_aponta_para_rotzx():
    import econatlas
    assert econatlas is rotzx


def test_banco_antigo_e_renomeado_no_primeiro_uso(tmp_path, monkeypatch):
    novo, antigo = tmp_path / "rotzx.sqlite", tmp_path / "econatlas.sqlite"
    monkeypatch.setattr(config, "DB_FILE", novo)
    monkeypatch.setattr(config, "DB_FILE_ANTIGO", antigo)
    c = storage.connect(antigo)  # cria um banco "antigo" com uma tabela marcada
    c.execute("CREATE TABLE marca (x)")
    c.commit()
    c.close()
    conn = storage.connect()
    assert novo.exists() and not antigo.exists()
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'marca'").fetchone()


def test_pasta_site_com_marcador_antigo_pode_ser_regerada(tmp_path):
    out = tmp_path / "site"
    out.mkdir()
    (out / public_build.MARCA_ANTIGA).write_text("x")
    (out / "velho.html").write_text("x")
    public_build._prepare_dir(out)
    assert (out / public_build.MARCA).exists() and not (out / "velho.html").exists()
