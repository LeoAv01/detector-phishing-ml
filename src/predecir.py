"""Analiza un archivo .eml, decide qué hacer con él y explica por qué con valores SHAP."""
import sys
from pathlib import Path

import joblib
import numpy as np
import xgboost as xgb
from scipy.sparse import csr_matrix, hstack

from features import extraer_indicadores
from parseo import leer_eml

ZONA_REVISION = 0.5  # entre esto y el umbral, decide una persona


def analizar(ruta: Path, top: int = 6) -> dict:
    d = joblib.load("modelos/detector.joblib")
    fila = leer_eml(ruta)
    indicadores = extraer_indicadores(fila)
    X = hstack([csr_matrix([list(indicadores.values())], dtype=float), d["tfidf"].transform([fila["texto"]])]).tocsr()
    prob = float(d["modelo"].predict_proba(X)[0, 1])
    # pred_contribs calcula valores SHAP: cuánto empujó cada variable hacia phishing
    shap = d["modelo"].get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]
    orden = np.argsort(-np.abs(shap))[:top]
    if prob >= d["umbral"]:
        decision = "BLOQUEAR"
    elif prob >= ZONA_REVISION:
        decision = "REVISAR"
    else:
        decision = "PERMITIR"
    return {
        "decision": decision,
        "probabilidad": round(prob, 4),
        "motivos": [(d["nombres"][i], round(float(shap[i]), 3)) for i in orden if shap[i] != 0],
    }


if __name__ == "__main__":
    r = analizar(Path(sys.argv[1]))
    print(f"{r['decision']}  (probabilidad de phishing: {r['probabilidad']})")
    for nombre, valor in r["motivos"]:
        print(f"  {'+' if valor > 0 else '-'} {nombre}: {valor}")
