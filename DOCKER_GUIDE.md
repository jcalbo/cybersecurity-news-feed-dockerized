# 🐳 Docker Deployment Guide

Complete guide to running the Cybersecurity News Feed with Docker.

## 📋 **Prerequisites**

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/engine/install/))
- Docker Compose 2.0+ (included with Docker Desktop)

**Verify installation:**
```bash
docker --version
docker-compose --version
```

---

## 🚀 **Quick Start**

### **Option 1: Docker Compose (Recommended)**

```bash
# From project root
docker-compose up -d
```

That's it! Services will be available at:
- **Frontend:** http://localhost:8501
- **Backend API:** http://localhost:8000

### **Option 2: Individual Containers**

#### Build Images
```bash
# Backend
docker build -t cybersecurity-news-backend ./backend

# Frontend
docker build -t cybersecurity-news-frontend ./frontend
```

#### Run Containers
```bash
# Backend
docker run -d \
  --name backend \
  -p 8000:8000 \
  cybersecurity-news-backend

# Frontend (connect to backend)
docker run -d \
  --name frontend \
  -p 8501:8501 \
  -e API_SERVER_URL=http://backend:8000 \
  --link backend \
  cybersecurity-news-frontend
```

---

## 📦 **Docker Compose Commands**

### **Start Services**
```bash
# Start in foreground (see logs)
docker-compose up

# Start in background (detached)
docker-compose up -d

# Build and start
docker-compose up --build
```

### **Stop Services**
```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

### **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### **Restart Services**
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### **Check Status**
```bash
docker-compose ps
```

---

## 🔧 **Configuration**

### **Environment Variables**

Create `.env` file in project root:

```env
# Backend Configuration
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8000

# Frontend Configuration
API_SERVER_URL=http://backend:8000
STREAMLIT_PORT=8501

# Optional: Resource Limits
BACKEND_MEMORY=512m
FRONTEND_MEMORY=512m
```

Then update `docker-compose.yml` to use it:
```yaml
services:
  backend:
    env_file: .env
```

### **Custom Ports**

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "9000:8000"  # Host:Container
  frontend:
    ports:
      - "9501:8501"
```

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────┐
│           Docker Host (Your Machine)         │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │  cybersecurity-network (Bridge)     │    │
│  │                                      │    │
│  │  ┌────────────┐    ┌─────────────┐ │    │
│  │  │  Frontend  │───▶│   Backend   │ │    │
│  │  │  :8501     │    │   :8000     │ │    │
│  │  └─────┬──────┘    └──────┬──────┘ │    │
│  │        │                   │         │    │
│  └────────┼───────────────────┼────────┘    │
│           │                   │              │
│      Port 8501            Port 8000          │
│           │                   │              │
└───────────┼───────────────────┼──────────────┘
            │                   │
            ↓                   ↓
        Browser             RSS Feeds
```

---

## 🧪 **Testing Docker Deployment**

### **Test 1: Check Containers Running**
```bash
docker-compose ps
```

Expected:
```
NAME                           STATUS    PORTS
cybersecurity-news-backend     Up        0.0.0.0:8000->8000/tcp
cybersecurity-news-frontend    Up        0.0.0.0:8501->8501/tcp
```

### **Test 2: Backend Health**
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"healthy","service":"cybersecurity_news_api"}
```

### **Test 3: Frontend Access**
```bash
# Open in browser
xdg-open http://localhost:8501
# or
open http://localhost:8501  # macOS
```

### **Test 4: Check Logs**
```bash
docker-compose logs backend | tail -20
docker-compose logs frontend | tail -20
```

---

## 📊 **Resource Management**

### **Limit Resources**

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### **Monitor Resources**
```bash
docker stats
```

---

## 🐛 **Troubleshooting**

### **Issue: Port Already in Use**

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
```

### **Issue: Cannot Connect to Backend**

**Check:**
```bash
# 1. Backend is running
docker-compose ps backend

# 2. Backend is healthy
docker-compose logs backend | grep -i error

# 3. Network connectivity
docker exec frontend ping backend -c 3
```

### **Issue: Build Fails**

**Solution:**
```bash
# Clean build with no cache
docker-compose build --no-cache

# Remove old images
docker system prune -a
```

### **Issue: Frontend Can't Reach Backend**

**Check environment variable:**
```bash
docker exec frontend printenv | grep API_SERVER_URL
```

Should show: `API_SERVER_URL=http://backend:8000`

---

## 🔄 **Updates & Rebuilds**

### **After Code Changes**

```bash
# Rebuild and restart
docker-compose up --build -d

# Or for specific service
docker-compose up --build -d backend
```

### **Pull Latest Images**
```bash
docker-compose pull
docker-compose up -d
```

---

## 🌐 **Production Deployment**

### **Use Production Compose**

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - API_SERVER_HOST=0.0.0.0
      - API_SERVER_PORT=8000
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    environment:
      - API_SERVER_URL=http://backend:8000
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Add reverse proxy (optional)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
```

Run with:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📝 **Useful Docker Commands**

```bash
# View container details
docker inspect cybersecurity-news-backend

# Execute command in container
docker exec -it cybersecurity-news-backend /bin/bash

# Copy files from container
docker cp cybersecurity-news-backend:/app/logs ./logs

# View container resource usage
docker stats cybersecurity-news-backend

# Export container as image
docker commit cybersecurity-news-backend my-backup:latest

# Clean up unused resources
docker system prune -a --volumes
```

---

## 🚀 **Deployment Checklist**

- [ ] Docker and Docker Compose installed
- [ ] Ports 8000 and 8501 available
- [ ] `.dockerignore` files in place
- [ ] Environment variables configured
- [ ] Build completes without errors
- [ ] Backend health check passes
- [ ] Frontend can connect to backend
- [ ] All RSS feeds are accessible
- [ ] Logs show no errors

---

## 📚 **Additional Resources**

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [UV in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [Streamlit Docker Guide](https://docs.streamlit.io/deploy/tutorials/docker)

---

## 💡 **Tips**

1. **Use Docker Compose** for local development
2. **Use docker-compose.prod.yml** for production
3. **Always use health checks** in production
4. **Monitor logs** regularly: `docker-compose logs -f`
5. **Backup volumes** if using persistent data
6. **Use tags** for versioning images: `v1.0.0`

---

**Happy Dockerizing! 🐳**

