# Exam 05 — Text-as-data under time pressure

**Time:** 90 minutes.

Generate `raw/generated_documents.csv` with 20,000 synthetic policy documents. Build a complete text pipeline.

## Required components

1. clean/normalize raw text;
2. create a dense embedding representation (pretrained embeddings **or** a local TF-IDF + dimensionality-reduction embedding);
3. train a topic classifier;
4. train a sentiment classifier;
5. report held-out metrics;
6. output document-level predictions and embeddings.

## Deliverables

- `predictions.parquet`: `doc_id,topic_true,topic_pred,sentiment_true,sentiment_pred`.
- `embeddings.parquet`: `doc_id,e000...` with >=32 dense dimensions.
- `metrics.json`: macro F1 + accuracy for topic and sentiment.
- `model_card.md`: split strategy, leakage controls, model choice, limitations.
- `run.py` one-command reproduction with fixed seed.

Critical trap: split by `template_family`, not random row, so near-duplicate templates do not leak across train/test.
