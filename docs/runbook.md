# Runbook

## Starting the System

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

## Stopping the System

```bash
# Graceful shutdown
docker-compose down

# Force stop
docker-compose kill
```

## Common Issues

### Kafka Connection Errors
**Symptom**: Producer/consumer cannot connect to Kafka
**Solution**:
1. Check Redpanda is running: `docker-compose ps redpanda`
2. Check logs: `docker-compose logs redpanda`
3. Restart Redpanda: `docker-compose restart redpanda`

### Model Loading Failures
**Symptom**: API returns 503, model not loaded
**Solution**:
1. Check MLflow is accessible: `curl http://localhost:5000/health`
2. Verify model exists in MLflow UI
3. Check MODEL_VARIANT environment variable
4. Fallback to baseline: Set `MODEL_VARIANT=baseline`

### High Latency
**Symptom**: p95 latency > 800ms
**Solution**:
1. Check Grafana dashboard for bottlenecks
2. Review model complexity
3. Consider batch size optimization
4. Check system resources: `docker stats`

### Data Replay Issues
**Symptom**: Ingestor not sending data
**Solution**:
1. Verify data file exists: `ls -la data/replay_10min.csv`
2. Check Kafka topic: `docker exec -it redpanda rpk topic list`
3. Check ingestor logs: `docker-compose logs ingestor`

## Model Rollback

```bash
# Switch to baseline model
docker-compose stop api
export MODEL_VARIANT=baseline
docker-compose up -d api

# Switch to ML model
docker-compose stop api
export MODEL_VARIANT=ml
docker-compose up -d api
```

## Monitoring Access
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- MLflow: http://localhost:5000

## Health Checks
```bash
# API health
curl http://localhost:8000/health

# API version
curl http://localhost:8000/version

# Metrics
curl http://localhost:8000/metrics
```

## Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ingestor
docker-compose logs -f feature-service
```

