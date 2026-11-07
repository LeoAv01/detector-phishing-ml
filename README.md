# Detector de phishing explicable

Clasifica correos como **bloquear, revisar o permitir** y explica cada decisión con valores SHAP. Está evaluado con phishing de años y fuentes que el modelo no vio al entrenar.

## El problema
Un modelo puede parecer casi perfecto en su propio dataset y fallar en producción. Este proyecto mide esa brecha y la reduce.

## Resultados

Límite de falsos positivos fijado en 1 % sobre validación.

| Entrenado con | Examen | Recall | Falsos positivos | PR-AUC |
|---|---|---|---|---|
| Una fuente (CEAS 2008) | Mismo corpus | 98.3 % | 0.9 % | 0.999 |
| Una fuente (CEAS 2008) | Desconocido | 7.8 % | 6.7 % | 0.235 |
| Varias fuentes | Mismo corpus | 86.3 % | 0.8 % | 0.994 |
| Varias fuentes | Desconocido | 81.6 % | 3.1 % | 0.914 |

**Examen desconocido:** phishing de 2020 en adelante y correos legítimos de fuentes ausentes del entrenamiento, sin duplicados.

## Decisiones técnicas
- **XGBoost con TF-IDF e indicadores de seguridad:** URLs con IP, acortadores, TLD de riesgo, suplantación de marca y urgencia.
- **Umbral según el costo de negocio**, no el 0.5 por defecto.
- **Zona de revisión humana:** con el nivel actual de falsos positivos, no debe bloquear de forma autónoma.
- **Eliminación de duplicados y de palabras que delatan la fuente**, para evitar fuga de datos.

## Limitaciones
- Corpus principalmente en inglés.
- Solo 179 correos de phishing en el examen.
- No analiza SPF, DKIM ni el contenido de las páginas enlazadas.

## Cómo ejecutarlo
Requiere [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python src/descargar.py
uv run python src/entrenar.py
uv run python src/predecir.py ejemplos/sospechoso.eml
uv run pytest -q
```

## Datos
[Phishing Email Curated Datasets](https://zenodo.org/records/8339691) (CC BY 4.0). No se incluyen en el repositorio porque contienen correos maliciosos reales.
