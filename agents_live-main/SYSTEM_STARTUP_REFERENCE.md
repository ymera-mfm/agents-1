# YMERA Platform - System Startup Quick Reference

## 🚀 Quick Start Commands

### Automated Startup (Recommended)

**Linux/Mac:**
```bash
./start_system.sh
```

**Windows:**
```cmd
start_system.bat
```

### Docker Compose Quick Start

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Manual Start

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt

# 2. Configure .env
cp .env.example .env
# Edit .env with your settings

# 3. Start infrastructure (Docker)
docker compose up -d postgres redis

# 4. Initialize database
alembic upgrade head

# 5. Start application
python main.py
```

## 📍 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Health Check** | http://localhost:8000/health | - |
| **Metrics** | http://localhost:8000/metrics | - |
| **Grafana** | http://localhost:3000 | admin/ymera_admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger** | http://localhost:16686 | - |
| **MinIO** | http://localhost:9001 | ymera_admin/ymera_password |

## 🔧 Common Commands

### Docker Compose

```bash
docker compose up -d              # Start all services
docker compose stop               # Stop all services
docker compose down               # Stop and remove containers
docker compose ps                 # List services status
docker compose logs -f            # Follow all logs
docker compose restart <service>  # Restart a service
```

### Python/Application

```bash
python3 -m venv venv              # Create virtual environment
source venv/bin/activate          # Activate (Linux/Mac)
pip install -r requirements.txt   # Install dependencies
python main.py                    # Start application
pytest                            # Run tests
```

### Database

```bash
alembic upgrade head              # Apply migrations
alembic current                   # Check current version
docker compose exec postgres psql -U ymera_user -d ymera  # Connect to DB
```

## 🐛 Quick Troubleshooting

### Port Already in Use
```bash
# Linux/Mac
lsof -i :8000 && kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Connection Failed
```bash
docker compose restart postgres
docker compose logs postgres
```

### Module Not Found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Reset Everything
```bash
docker compose down -v
rm -rf venv
./start_system.sh
```

## 📊 Health Checks

```bash
curl http://localhost:8000/health         # Overall health
curl http://localhost:8000/health/live    # Liveness probe
curl http://localhost:8000/health/ready   # Readiness probe
```

## 🔐 Quick API Test

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!"}'
```

## 📦 Required Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
JWT_SECRET_KEY=minimum-32-character-secret-key-here
SECRET_KEY=another-minimum-32-character-secret-key
```

## 🆘 Documentation Links

- **Complete Guide**: [RUNNING_GUIDE.md](./RUNNING_GUIDE.md)
- **README**: [README.md](./README.md)
- **Deployment**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

---

**For detailed instructions, see [RUNNING_GUIDE.md](./RUNNING_GUIDE.md)**
