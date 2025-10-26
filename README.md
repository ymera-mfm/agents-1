# YMERA Multi-Agent AI System

A robust, production-ready enterprise platform designed to manage and execute tasks using multiple specialized AI agents.

## Features

- **Modular Architecture**: Component-based design with specialized agents
- **Production-Ready**: Enhanced security, observability, and scalability
- **Enterprise-Grade**: Suitable for Kubernetes deployment
- **Multi-Agent System**: Supports multiple specialized agents working together
- **Real-time Communication**: NATS-based message broker for inter-agent communication
- **Comprehensive Monitoring**: Built-in health checks and metrics collection

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 16+
- Redis 7+
- NATS Server

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ymera-mfm/agents-1.git
cd agents-1
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start services with Docker Compose:
```bash
docker-compose up -d
```

6. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Architecture

### Core Components

- **Base Agent**: Foundation for all specialized agents
- **Communication Agent**: Handles inter-agent messaging
- **Monitoring Agent**: System health and metrics tracking
- **Database Layer**: PostgreSQL with SQLAlchemy ORM
- **Message Broker**: NATS for event streaming
- **API Gateway**: FastAPI-based REST API

### Agent Types

1. **Communication Agent**: Manages message routing and delivery
2. **Monitoring Agent**: Tracks system health and performance
3. **Learning Agent**: Adaptive learning capabilities (extensible)
4. **Validation Agent**: Quality assurance and testing (extensible)

## API Documentation

Once running, access the interactive API docs:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_base_agent.py

# Run integration tests
pytest tests/test_integration.py
```

## Development

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

### Adding New Agents

1. Create a new file: `agent_{name}.py`
2. Inherit from `BaseAgent`
3. Implement required methods: `initialize()`, `process_message()`, `execute()`
4. Add tests in `tests/test_{name}.py`
5. Register agent in configuration

## Monitoring

Access monitoring dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Deployment

### Docker

Build and run with Docker:
```bash
docker build -t ymera-system .
docker run -p 8000:8000 ymera-system
```

### Kubernetes

Deploy to Kubernetes:
```bash
kubectl apply -f k8s/
```

## Configuration

Key configuration options in `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_HOST`: Redis server host
- `NATS_SERVERS`: NATS server URLs
- `SECRET_KEY`: JWT secret key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Security

- Zero-trust architecture
- JWT-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Encrypted data at rest and in transit

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

Copyright © 2025 YMERA. All rights reserved.

## Support

For issues and questions:
- GitHub Issues: https://github.com/ymera-mfm/agents-1/issues
- Documentation: See `/docs` directory
