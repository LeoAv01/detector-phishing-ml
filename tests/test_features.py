"""Pruebas de los indicadores: si alguna falla, el modelo aprende de datos equivocados."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features import extraer_indicadores


def fila(**cambios) -> dict:
    return {"texto": "", "asunto": "", "remitente": "a@empresa.com", **cambios}


def test_detecta_url_con_ip():
    assert extraer_indicadores(fila(texto="entra a http://192.168.1.5/login"))["url_con_ip"] == 1


def test_detecta_url_acortada():
    assert extraer_indicadores(fila(texto="mira https://bit.ly/abc"))["url_acortada"] == 1


def test_detecta_marca_suplantada():
    s = extraer_indicadores(fila(remitente="PayPal Support <soporte@correo-raro.ru>"))
    assert s["marca_suplantada"] == 1


def test_marca_real_no_cuenta():
    s = extraer_indicadores(fila(remitente="PayPal <service@paypal.com>"))
    assert s["marca_suplantada"] == 0


def test_correo_vacio_no_rompe():
    assert extraer_indicadores(fila())["n_urls"] == 0
