"""Compara entrenar con una sola fuente contra varias, siempre con el mismo examen desconocido."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics import average_precision_score, roc_curve
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from features import extraer_indicadores
from parseo import cargar_datos

MAX_FALSOS_POSITIVOS = 0.01  # bloquear más del 1 % de correo legítimo es inaceptable
PESO_PHISHING = 10  # el phishing dirigido es escaso frente al spam masivo: cada caso vale más
# Fragmentos de URL y de listas de correo: delatan la fuente, no la intención del correo
RUIDO = {"com", "org", "net", "www", "http", "https", "html", "htm", "edu", "mail", "wrote", "list",
         "enron", "ect", "hou", "listinfo", "mailman", "spamassassin", "exmh", "razor"}


def umbral_para_fpr(y: np.ndarray, p: np.ndarray) -> float:
    """El umbral más bajo (más sensible) que respeta el límite de falsos positivos."""
    fpr, _, umbrales = roc_curve(y, p)
    return float(umbrales[np.where(fpr <= MAX_FALSOS_POSITIVOS)[0][-1]])


def medir(y: np.ndarray, p: np.ndarray, umbral: float) -> dict:
    pred = p >= umbral
    return {
        "recall": round(float(pred[y == 1].mean()), 4),
        "falsos_positivos": round(float(pred[y == 0].mean()), 4),
        "pr_auc": round(float(average_precision_score(y, p)), 4),
    }


def matriz(df: pd.DataFrame, tfidf: TfidfVectorizer):
    indicadores = pd.DataFrame([extraer_indicadores(f) for f in df.to_dict("records")]).values.astype(float)
    return hstack([csr_matrix(indicadores), tfidf.transform(df.texto)]).tocsr()


def experimento(nombre: str, datos: pd.DataFrame, examen: pd.DataFrame) -> tuple[dict, list[dict]]:
    resto, interno = train_test_split(datos, test_size=0.2, random_state=42, stratify=datos.etiqueta)
    train, val = train_test_split(resto, test_size=0.2, random_state=42, stratify=resto.etiqueta)
    # token_pattern solo con letras: evita aprender fechas o números propios de cada corpus
    tfidf = TfidfVectorizer(max_features=5000, sublinear_tf=True, min_df=3, token_pattern=r"[a-zA-Z]{3,}",
                            stop_words=list(ENGLISH_STOP_WORDS | RUIDO))
    tfidf.fit(train.texto)
    pesos = np.where(train.fuente == "Nazario", PESO_PHISHING, 1)
    modelo = XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, eval_metric="logloss")
    modelo.fit(matriz(train, tfidf), train.etiqueta.values, sample_weight=pesos)

    def prob(d):
        return modelo.predict_proba(matriz(d, tfidf))[:, 1]

    umbral = umbral_para_fpr(val.etiqueta.values, prob(val))
    filas = [
        {"entrenado_con": nombre, "examen": e, "umbral": round(umbral, 4), **medir(d.etiqueta.values, prob(d), umbral)}
        for e, d in [("interno", interno), ("desconocido", examen)]
    ]
    nombres = list(extraer_indicadores(train.iloc[0].to_dict())) + list(tfidf.get_feature_names_out())
    return {"modelo": modelo, "tfidf": tfidf, "umbral": umbral, "nombres": nombres}, filas


def main() -> None:
    d = cargar_datos()
    examen = d["examen"]
    print(f"examen desconocido: {(examen.etiqueta == 1).sum()} phishing, {(examen.etiqueta == 0).sum()} legítimos")
    diverso = pd.concat([d["ceas"], d["otras"], d["phishing_viejo"]], ignore_index=True)

    _, filas_una = experimento("una_fuente", d["ceas"], examen)
    final, filas_varias = experimento("varias_fuentes", diverso, examen)
    resultados = filas_una + filas_varias
    print(pd.DataFrame(resultados).to_string(index=False))

    Path("modelos").mkdir(exist_ok=True)
    Path("reportes").mkdir(exist_ok=True)
    joblib.dump(final, "modelos/detector.joblib")
    Path("reportes/metricas.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
