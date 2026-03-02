# External Documentation References

This document provides links to official documentation for third-party services, libraries, and frameworks used in the PDP Automation system.

## Why This Document Exists
- Integration docs can link to official documentation
- Developer guide can reference authoritative sources
- DevOps docs can link to deployment guides
- Ensures everyone references the same authoritative sources

---

## Google Cloud Platform

### [Cloud Run Docs](https://cloud.google.com/run/docs)
**Used for:** Backend API deployment (FastAPI services)
**Key sections:**
- Deploying containers
- Environment variables and secrets management
- Auto-scaling configuration
- Cold start optimization

### [Cloud Storage Docs](https://cloud.google.com/storage/docs)
**Used for:** Storing PDF files, processed images, and extraction results
**Key sections:**
- Bucket management and permissions
- Signed URLs for secure file access
- Lifecycle policies for old files
- Integration with Cloud Run

### [Google Sheets API](https://developers.google.com/sheets/api/guides/concepts)
**Used for:** Batch reading/writing form data, exporting results to Google Sheets
**Key sections:**
- Authentication and authorization
- Reading and writing data
- Batch operations
- Rate limits and quotas

### [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
**Used for:** User authentication, Google Sheets API authorization
**Key sections:**
- Service account authentication
- OAuth 2.0 flows
- Token management
- Scopes and permissions

---

## OpenAI / AI Services

### [OpenAI API Quickstart](https://platform.openai.com/docs/quickstart)
**Used for:** Getting started with GPT-4 Vision for PDF analysis
**Key sections:**
- API authentication
- Basic request structure
- Error handling

### [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
**Used for:** Detailed API specifications for GPT-4 Vision calls
**Key sections:**
- Chat completions endpoint
- Vision capabilities
- Parameters and options
- Response formats

### [GPT-4 Vision Guide](https://platform.openai.com/docs/guides/vision)
**Used for:** Core PDF analysis functionality (extracting form data from images)
**Key sections:**
- Image input formats (base64, URLs)
- Vision-specific parameters
- Best practices for document analysis
- Limitations and considerations

### [OpenAI Pricing](https://openai.com/pricing)
**Used for:** Cost estimation and budgeting
**Key sections:**
- GPT-4 Vision pricing per token
- Image pricing based on resolution
- Cost optimization strategies

---

## Database

### [Neon PostgreSQL Docs](https://neon.tech/docs/introduction)
**Used for:** Serverless PostgreSQL database for storing processing metadata
**Key sections:**
- Database creation and configuration
- Branching for development/testing
- Backup and recovery
- Performance tuning

### [Neon Connection Pooling](https://neon.tech/docs/connect/connection-pooling)
**Used for:** Managing database connections from Cloud Run instances
**Key sections:**
- Connection pooling setup
- Connection string formats
- Best practices for serverless environments
- Troubleshooting connection issues

---

## Backend Frameworks & Libraries

### [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
**Used for:** Backend API framework
**Key sections:**
- Path operations and routing
- Request/response models with Pydantic
- Async/await patterns
- Background tasks
- Dependency injection

### [PyMuPDF Docs](https://pymupdf.readthedocs.io/)
**Used for:** PDF processing, page extraction, image conversion
**Key sections:**
- Opening and reading PDFs
- Extracting pages
- Converting pages to images
- Text extraction (fallback method)
- Performance optimization

### [OpenCV Python Docs](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
**Used for:** Image preprocessing before AI analysis
**Key sections:**
- Image loading and saving
- Image transformations (resize, crop, rotate)
- Color space conversions
- Noise reduction and enhancement
- Contour detection

---

## Frontend Frameworks & Libraries

### [React Query Docs](https://tanstack.com/query/latest)
**Used for:** Data fetching, caching, and state management in frontend
**Key sections:**
- Query basics and mutations
- Caching strategies
- Optimistic updates
- Background refetching
- Error handling

### [Tailwind CSS Docs](https://tailwindcss.com/docs)
**Used for:** UI styling framework
**Key sections:**
- Utility classes
- Responsive design
- Dark mode
- Custom configuration
- Component patterns

---

## Additional Resources

### Community & Support
- Stack Overflow tags for each technology
- GitHub issues for bug reports
- Official Discord/Slack communities

### Version Compatibility
Always check documentation versions match your installed packages:
- Python dependencies: see `backend/requirements.txt`
- JavaScript dependencies: see `frontend/package.json`
- Cloud services: check deployment configurations

---

**Last Updated:** 2026-01-15
**Maintenance:** Review quarterly for deprecated APIs or major version updates
