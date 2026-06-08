# MLflow

MLflow is configured by `MLFLOW_TRACKING_URI`. Docker Compose starts a local MLflow server on `http://localhost:5000`; local scripts can also use `file:./mlruns`.

Churn training logs model parameters and metrics. Forecasting logs horizon/target parameters and MAE.
