# Technology Selection Rationale

## Kafka/Redpanda
**Selected**: Redpanda (Kafka-compatible)
**Rationale**: 
- Lightweight, single-binary deployment
- Kafka-compatible API
- Better performance for small-scale deployments
- Easier to run in Docker Compose

## FastAPI
**Selected**: FastAPI
**Rationale**:
- Modern async Python framework
- Built-in OpenAPI documentation
- Excellent performance
- Easy integration with Prometheus metrics

## MLflow
**Selected**: MLflow
**Rationale**:
- Industry standard for ML model management
- Supports model versioning and registry
- Easy integration with scikit-learn
- REST API for model serving

## Prometheus + Grafana
**Selected**: Prometheus + Grafana
**Rationale**:
- De facto standard for metrics collection
- Rich ecosystem and integrations
- Excellent visualization capabilities
- Time-series database optimized for metrics

## Evidently
**Selected**: Evidently
**Rationale**:
- Specialized for data drift detection
- Easy integration with ML pipelines
- Comprehensive drift reports
- Supports multiple drift detection methods

## Docker Compose
**Selected**: Docker Compose
**Rationale**:
- Simplifies multi-service deployment
- Consistent development and production environments
- Easy service orchestration
- Standard tool, widely supported

