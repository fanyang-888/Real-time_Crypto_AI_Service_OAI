# System Architecture

## Overview
The Real-Time Crypto AI Volatility Service is a microservices-based system for real-time cryptocurrency volatility prediction.

## Architecture Diagram

```
┌─────────────────┐
│  Coinbase Data  │
│  (CSV Replay)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Ingestor     │
│   (Producer)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka/Redpanda │
│   (Streaming)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────────────┐
│ Feature │ │   FastAPI       │
│ Service │ │   (Inference)   │
│(Consumer)│ └────────┬────────┘
└─────────┘          │
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐ ┌──────────┐ ┌──────────┐
    │ MLflow │ │Prometheus│ │ Grafana  │
    │(Models)│ │(Metrics) │ │(Viz)     │
    └────────┘ └──────────┘ └──────────┘
```

## Components

### 1. Ingestor (Producer)
- Reads Coinbase data from CSV
- Replays data at configurable speed (1x, 10x, real-time)
- Publishes to Kafka topic
- Handles reconnection and graceful shutdown

### 2. Kafka/Redpanda
- Message streaming platform
- Topic: `coinbase-trades` (input)
- Topic: `predictions` (output)
- Provides durability and replay capability

### 3. Feature Service (Consumer)
- Consumes from Kafka
- Maintains sliding window (default: 50)
- Computes features: ret_mean, ret_std, n
- Publishes features to prediction topic

### 4. FastAPI Service
- REST API for predictions
- Endpoints: /predict, /health, /version, /metrics
- Loads models from MLflow
- Supports MODEL_VARIANT (baseline/ml)
- Exposes Prometheus metrics

### 5. MLflow
- Model registry and versioning
- Tracks experiments and runs
- Serves model artifacts
- Supports model rollback

### 6. Prometheus
- Metrics collection
- Scrapes from FastAPI /metrics endpoint
- Stores time-series data
- Provides query interface

### 7. Grafana
- Visualization dashboard
- Connects to Prometheus
- Displays latency, throughput, errors
- Real-time monitoring

## Data Flow

1. **Ingestion**: CSV → Ingestor → Kafka
2. **Feature Engineering**: Kafka → Feature Service → Features → Kafka
3. **Prediction**: Features → FastAPI → Model → Predictions
4. **Monitoring**: All services → Prometheus → Grafana

## Technology Stack

- **Streaming**: Redpanda (Kafka-compatible)
- **API**: FastAPI (Python)
- **ML**: scikit-learn, MLflow
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker, Docker Compose

## Scalability Considerations

- Horizontal scaling: Multiple consumer instances
- Model serving: Can scale API independently
- Kafka partitioning: Supports parallel processing
- Stateless services: Easy to scale horizontally

## Security

- Environment variables for configuration
- No authentication (development setup)
- Network isolation via Docker networks
- Secrets management via .env files

