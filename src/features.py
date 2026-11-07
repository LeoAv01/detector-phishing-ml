"""Indicadores que usaría un analista de seguridad, calculados para cada correo."""
import re
from email.utils import parseaddr
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.I)
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
ACORTADORES = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "rebrand.ly", "cutt.ly"}
TLD_RIESGO = {"zip", "top", "xyz", "click", "link", "work", "rest", "cam", "icu", "ru", "cn"}
MARCAS = {"paypal", "ebay", "amazon", "microsoft", "apple", "google", "netflix", "bank", "wellsfargo", "chase"}
URGENCIA = re.compile(
    r"\b(urgent|immediately|verify|suspended|locked|expire[sd]?|confirm your|password|"
    r"unusual activity|within \d+ hours|action required)\b",
    re.I,
)


def dominio_de(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def marca_suplantada(nombre_visible: str, correo: str) -> int:
    """1 si el nombre visible menciona una marca, pero el dominio real del remitente no."""
    visible = nombre_visible.lower()
    dominio = correo.split("@")[-1].lower()
    return int(any(m in visible and m not in dominio for m in MARCAS))


def extraer_indicadores(fila: dict) -> dict:
    texto, asunto = fila["texto"], fila["asunto"]
    urls = URL_RE.findall(texto)
    dominios = [d for d in map(dominio_de, urls) if d]
    nombre, correo = parseaddr(fila["remitente"])
    return {
        "n_urls": len(urls),
        "n_dominios": len(set(dominios)),
        "url_con_ip": sum(bool(IP_RE.match(d)) for d in dominios),
        "url_acortada": sum(d in ACORTADORES for d in dominios),
        "url_tld_riesgo": sum(d.rsplit(".", 1)[-1] in TLD_RIESGO for d in dominios),
        "url_punycode": sum("xn--" in d for d in dominios),
        "url_con_arroba": sum("@" in u for u in urls),
        "marca_suplantada": marca_suplantada(nombre, correo),
        "palabras_urgencia": len(URGENCIA.findall(f"{texto} {asunto}")),
        "asunto_mayusculas": int(asunto.isupper()),
    }
