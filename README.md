# Product Page Automation Platform

AI pipeline that extracts structured property data from PDF floor plans and generates publication-ready listing content for six real estate template types.

## What It Does

Agents extract room dimensions, floor areas, and layout features from architectural PDFs using a hybrid pymupdf4llm + image render pipeline with cross-validation. A content generation layer then produces template-specific copy (property descriptions, area guides, off-plan summaries) validated against extracted data before publication.

## Architecture

```
PDF Input
  --> Extraction Pipeline (pymupdf4llm text + page render fallback)
  --> Cross-validation (plausibility checks, unit inference, confidence scoring)
  --> Content Generation (Claude API, template-specific prompts)
  --> Output (ZIP with JSON sidecar, Drive sync, GCS upload)
```

Anti-hallucination pattern: Python extracts and validates all measurements deterministically. Claude narrates pre-validated data. Python re-validates generated content before delivery.

## Tech Stack

- Python 3.11 / FastAPI / PostgreSQL 16
- React 19 / TypeScript
- Claude API (claude-sonnet-4-6) for content generation
- Google Drive API + Google Cloud Storage for output delivery
- Docker / GitHub Actions CI

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 16
- Node.js 20+
- Google Cloud project with Drive API and GCS bucket
- Anthropic API key

### Installation

```bash
git clone https://github.com/shahe-dev/product-page-automation
cd product-page-automation
cp .env.example .env
# Edit .env with your credentials

# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd ../frontend
npm install
```

### Running

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

### Running tests

```bash
cd backend && pytest --tb=short
cd frontend && npm test
```

## Project Status

Active development. Core extraction and generation pipeline is production-tested across six template types (MPP resale, OPR, ADOP, ADRE, commercial, aggregator).

## License

[PolyForm Noncommercial 1.0.0](LICENSE) -- free for personal and research use, not for commercial use.
