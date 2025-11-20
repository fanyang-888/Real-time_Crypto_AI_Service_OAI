# Real-Time Crypto AI Volatility Service

Real-time cryptocurrency volatility prediction system with Kafka streaming, MLflow model management, and comprehensive monitoring.

## Quick Start

```bash
docker-compose up -d
```

Access services:
- API: http://localhost:8000
- MLflow: http://localhost:5000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## API Endpoints

- `POST /predict` - Batch predictions
- `GET /health` - Health check
- `GET /version` - Model version
- `GET /metrics` - Prometheus metrics

## Configuration

Copy `.env.example` to `.env` and customize settings.

