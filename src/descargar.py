"""Descarga el dataset público (CC BY 4.0): correos ya convertidos a texto, sin adjuntos."""
import urllib.request
from pathlib import Path

RAW = Path("data/raw")
BASE = "https://zenodo.org/api/records/8339691/files/{}/content"
ARCHIVOS = ["CEAS_08.csv", "Enron.csv", "Ling.csv", "SpamAssasin.csv", "Nazario.csv", "Nazario_5.csv"]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for nombre in ARCHIVOS:
        destino = RAW / nombre
        if destino.exists():
            print(f"ya existe: {nombre}")
            continue
        print(f"descargando: {nombre}")
        urllib.request.urlretrieve(BASE.format(nombre), destino)
    print("listo")


if __name__ == "__main__":
    main()
