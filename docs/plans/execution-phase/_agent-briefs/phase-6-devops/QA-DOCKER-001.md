# Agent Brief: QA-DOCKER-001

**Agent ID:** QA-DOCKER-001
**Agent Name:** Docker QA
**Type:** QA
**Phase:** 6 - DevOps
**Paired Dev Agent:** DEV-DOCKER-001

---

## Validation Checklist

- [ ] Backend Dockerfile builds successfully
- [ ] Frontend Dockerfile builds successfully
- [ ] Multi-stage builds optimize size
- [ ] Non-root users configured
- [ ] Health checks work
- [ ] docker-compose.yml starts all services
- [ ] docker-compose.dev.yml enables hot reload
- [ ] No secrets in images
- [ ] Base images are minimal
- [ ] Caching layers work

---

## Test Cases

1. Build backend image
2. Build frontend image
3. Run backend container
4. Run frontend container
5. Health check responds
6. docker-compose up (prod)
7. docker-compose up (dev)
8. Hot reload backend
9. Hot reload frontend
10. Connect to local DB
11. Check image sizes
12. Security scan images

---

## Image Size Targets

- Backend: <500MB
- Frontend: <100MB

---

## Security Tests

- No root processes
- No hardcoded secrets
- Minimal installed packages
- Vulnerability scan passes

---

## Development Tests

- Code changes reflect immediately
- Logs visible in terminal
- Debugger can attach
- Database accessible

---

**Begin review.**
