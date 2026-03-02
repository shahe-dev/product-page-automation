# Agent Brief: DEV-CLOUDRUN-001

**Agent ID:** DEV-CLOUDRUN-001
**Agent Name:** Cloud Run Agent
**Type:** Development
**Phase:** 6 - DevOps
**Context Budget:** 50,000 tokens

---

## Mission

Create Cloud Run service configurations for backend and frontend deployment with auto-scaling and traffic management.

---

## Documentation to Read

### Primary
1. `docs/06-devops/DEPLOYMENT_GUIDE.md` - Deployment specs
2. `docs/01-architecture/INFRASTRUCTURE.md` - Infrastructure design

---

## Dependencies

**Upstream:** DEV-DOCKER-001, DEV-CICD-001
**Downstream:** DEV-MONITORING-001

---

## Outputs

### `infrastructure/cloudrun-backend.yaml`
### `infrastructure/cloudrun-frontend.yaml`
### `scripts/deploy.sh`

---

## Acceptance Criteria

1. **Backend Service:**
   - Cloud Run service definition
   - CPU: 2 vCPU
   - Memory: 2GB
   - Min instances: 1 (staging: 0)
   - Max instances: 10
   - Concurrency: 80
   - Timeout: 300s
   - VPC connector for DB access

2. **Frontend Service:**
   - Cloud Run service definition
   - CPU: 1 vCPU
   - Memory: 512MB
   - Min instances: 1
   - Max instances: 5
   - Concurrency: 200

3. **Environment Configuration:**
   - Secret Manager references
   - Environment variables
   - Service account binding

4. **Traffic Management:**
   - Gradual rollout (canary)
   - Rollback capability
   - Blue-green option

5. **Deploy Script:**
   - Environment parameter
   - Image tag parameter
   - Health verification
   - Rollback on failure

6. **Networking:**
   - Custom domain mapping
   - SSL/TLS certificates
   - CDN configuration (frontend)

---

## Service Configuration

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: pdp-backend
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
        - image: gcr.io/project/backend:latest
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
```

---

## QA Pair: QA-CLOUDRUN-001

---

**Begin execution.**
