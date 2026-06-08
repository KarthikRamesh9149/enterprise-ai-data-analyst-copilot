# Model Governance

Churn modeling uses RandomForestClassifier with preprocessing for numeric/categorical features. It logs metrics and parameters to MLflow, stores feature importance, creates risk scores, and writes a model card.

Metrics include accuracy, F1, and ROC AUC when class diversity permits. Model cards document purpose, training data, features, intended use, limitations, risk notes, and monitoring recommendations.

Limitations: synthetic demo data, no fairness analysis, no automated drift monitoring, and no autonomous customer actioning.
