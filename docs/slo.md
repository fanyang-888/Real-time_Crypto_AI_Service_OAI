# Service Level Objectives (SLO)

## Availability
- **Target**: 99.5% uptime
- **Measurement**: Service responds to /health endpoint
- **Window**: 30 days

## Latency
- **Target**: p95 latency ≤ 800ms for /predict endpoint
- **Measurement**: Prometheus histogram metric `http_request_duration_seconds`
- **Window**: 5-minute rolling window

## Error Rate
- **Target**: < 1% error rate for predictions
- **Measurement**: `prediction_errors_total / prediction_requests_total`
- **Window**: 5-minute rolling window

## Data Freshness
- **Target**: Kafka consumer lag < 1000 messages
- **Measurement**: `kafka_consumer_lag` metric
- **Window**: Real-time

## Model Performance
- **Target**: PR-AUC > baseline model
- **Measurement**: MLflow metrics comparison
- **Window**: Per model version

## Monitoring
- Prometheus alerts configured for SLO violations
- Grafana dashboards show SLO compliance
- Weekly SLO review in team meetings

