"""Carga los datasets y lee correos .eml. Solo extrae texto: nunca abre enlaces ni renderiza HTML."""
import email
from email.message import Message
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

RAW = Path("data/raw")
ANIO_CORTE = 2020  # el phishing desde este año queda oculto para el examen final


def cargar_csv(nombre: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / f"{nombre}.csv")
    df = df.rename(columns={"sender": "remitente", "subject": "asunto", "body": "texto", "label": "etiqueta"})
    if "remitente" not in df:  # Enron y Ling no incluyen remitente
        df["remitente"] = ""
    df["anio"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.year if "date" in df else 0
    df["fuente"] = nombre
    df = df[["remitente", "asunto", "texto", "etiqueta", "anio", "fuente"]]
    df[["remitente", "asunto", "texto"]] = df[["remitente", "asunto", "texto"]].fillna("")
    df = df[df.texto.str.strip().str.len() > 0]
    df = df[~df.remitente.str.contains("MAILER-DAEMON", case=False)]  # avisos del servidor, no correos
    return df.drop_duplicates(subset=["asunto", "texto"]).reset_index(drop=True)


def cargar_datos() -> dict[str, pd.DataFrame]:
    """Separa por fuente y por tiempo para que el examen final sea realmente desconocido."""
    nazario = cargar_csv("Nazario")
    phishing_viejo = nazario[nazario.anio < ANIO_CORTE]
    phishing_nuevo = nazario[nazario.anio >= ANIO_CORTE]
    # Los legítimos de Nazario_5 vienen de listas de correo que no aparecen al entrenar
    extra = cargar_csv("Nazario_5")
    legitimos_nuevos = extra[extra.etiqueta == 0]
    ceas = cargar_csv("CEAS_08")
    otras = pd.concat([cargar_csv("Enron"), cargar_csv("Ling"), cargar_csv("SpamAssasin")], ignore_index=True)
    examen = pd.concat([phishing_nuevo, legitimos_nuevos], ignore_index=True)
    # Un correo repetido entre entrenamiento y examen inflaría el resultado
    vistos = pd.concat([ceas.texto, otras.texto, phishing_viejo.texto])
    examen = examen[~examen.texto.isin(vistos)].reset_index(drop=True)
    return {"ceas": ceas, "otras": otras, "phishing_viejo": phishing_viejo, "examen": examen}


def cuerpo_de(msg: Message) -> str:
    """Devuelve el texto de un correo. Del HTML conserva el destino real de cada enlace."""
    trozos = []
    for parte in msg.walk():
        tipo = parte.get_content_type()
        if tipo not in ("text/plain", "text/html"):
            continue
        crudo = parte.get_payload(decode=True) or b""
        contenido = crudo.decode(parte.get_content_charset() or "utf-8", errors="replace")
        if tipo == "text/html":
            sopa = BeautifulSoup(contenido, "html.parser")
            destinos = " ".join(a["href"] for a in sopa.find_all("a", href=True))
            contenido = f"{sopa.get_text(' ')} {destinos}"
        trozos.append(contenido)
    return "\n".join(trozos)


def leer_eml(ruta: Path) -> dict:
    msg = email.message_from_bytes(ruta.read_bytes())
    return {"remitente": str(msg.get("From", "")), "asunto": str(msg.get("Subject", "")), "texto": cuerpo_de(msg)}
