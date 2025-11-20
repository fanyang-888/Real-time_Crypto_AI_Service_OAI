# Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- ~4GB RAM available
- Ports available: 8000, 5000, 3000, 9090, 19092

## Quick Start

### 1. Clone and Setup

```bash
cd Real-Time_Crypto_AI_Service
```

### 2. Generate Sample Data

```bash
# Install Python dependencies
pip install pandas numpy

# Generate sample data
python scripts/generate_sample_data.py
```

This creates `data/replay_10min.csv` with 600 records (10 minutes of data).

### 3. Configure Environment

```bash
# Copy environment template (if .env.example exists)
cp .env.example .env

# Or create .env manually with:
# MODEL_VARIANT=ml
# KAFKA_TOPIC=coinbase-trades
# REPLAY_SPEED=1
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Verify Services

```bash
# API Health
curl http://localhost:8000/health

# API Version
curl http://localhost:8000/version

# Test Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rows": [
      {"ret_mean": 0.05, "ret_std": 0.01, "n": 50}
    ]
  }'
```

### 6. Access Dashboards

- **API Docs**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## MLflow Model Setup

### Option 1: Use Baseline Model (Default)

The system automatically falls back to a baseline Logistic Regression model if MLflow is unavailable.

### Option 2: Register Model in MLflow

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Set tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Train a model
X_train = np.array([[0.01, 0.005, 50], [0.05, 0.02, 50], [-0.01, 0.005, 50]])
y_train = np.array([0, 1, 0])

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Log to MLflow
with mlflow.start_run():
    mlflow.sklearn.log_model(model, "model")
    mlflow.register_model("runs:/<run_id>/model", "crypto_volatility_model")
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Services won't start
- Check Docker is running: `docker ps`
- Check ports are available: `lsof -i :8000`
- Check logs: `docker-compose logs <service-name>`

### Kafka connection errors
- Wait for Redpanda to be healthy: `docker-compose ps redpanda`
- Check Redpanda logs: `docker-compose logs redpanda`
- Restart services: `docker-compose restart`

### Model loading fails
- Check MLflow is accessible: `curl http://localhost:5000/health`
- Use baseline model: Set `MODEL_VARIANT=baseline` in .env
- Check model exists in MLflow UI

### High latency
- Check system resources: `docker stats`
- Review Grafana dashboard
- Consider reducing batch size
- Check Kafka consumer lag

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export KAFKA_BOOTSTRAP_SERVERS=localhost:19092
export MLFLOW_TRACKING_URI=http://localhost:5000
export MODEL_VARIANT=baseline

# Run API
uvicorn src.api.main:app --reload

# Run ingestor (in another terminal)
python -m src.ingestion.producer

# Run feature service (in another terminal)
python -m src.ingestion.consumer
```

## Production Considerations

- Use proper secrets management (not .env files)
- Enable authentication for API endpoints
- Set up proper logging aggregation
- Configure resource limits in docker-compose
- Set up backup for MLflow database
- Configure alerting in Prometheus
- Use managed Kafka for production scale

