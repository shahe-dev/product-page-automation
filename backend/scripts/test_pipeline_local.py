"""
Local Pipeline E2E Test Runner

Runs the full 14-step PDF processing pipeline locally with real APIs.
Bypasses Cloud Tasks by calling JobManager.execute_processing_pipeline() directly.

Usage:
    python scripts/test_pipeline_local.py <pdf_path> [--template opr] [--email test@your-domain.com]

Prerequisites:
    - backend/.env populated with real secrets
    - Local PostgreSQL running with alembic migrations applied
    - Google service account with Sheets/Drive access
    - Valid Anthropic API key
    - A real estate PDF brochure file
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Add backend/ to sys.path so app imports work
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

# Configure logging before any app imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

logger = logging.getLogger("pipeline_test")

VALID_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]

STEP_DESCRIPTIONS = {
    "upload": "PDF Upload & Validation",
    "extract_images": "Image Extraction (triple: embedded + renders + text)",
    "classify_images": "Image Classification (Claude Vision)",
    "detect_watermarks": "Watermark Detection",
    "remove_watermarks": "Watermark Removal (OpenCV inpainting)",
    "extract_floor_plans": "Floor Plan Extraction (Claude Vision OCR)",
    "optimize_images": "Image Optimization (WebP conversion)",
    "package_assets": "Asset Packaging (ZIP + manifest)",
    "extract_data": "Data Extraction (regex-based, free)",
    "structure_data": "Data Structuring (Claude API)",
    "generate_content": "Content Generation (Claude API, 10 fields)",
    "populate_sheet": "Sheet Population (Google Sheets API)",
    "upload_cloud": "Cloud Upload (Google Drive API)",
    "finalize": "Finalization",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the full PDP pipeline locally with real APIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_pipeline_local.py brochure.pdf
  python scripts/test_pipeline_local.py brochure.pdf --template aggregators
  python scripts/test_pipeline_local.py brochure.pdf --template opr --email user@your-domain.com
        """,
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF brochure file",
    )
    parser.add_argument(
        "--template",
        default="opr",
        choices=VALID_TEMPLATES,
        help="Template type (default: opr)",
    )
    parser.add_argument(
        "--email",
        default="test@your-domain.com",
        help="Test user email for job ownership (default: test@your-domain.com)",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip preflight validation checks",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


# ------------------------------------------------------------------
# Preflight validation
# ------------------------------------------------------------------

async def run_preflight_checks(pdf_path: str, template: str) -> bool:
    """Run all prerequisite checks before pipeline execution."""
    checks_passed = True

    print("\n" + "=" * 60)
    print("  PREFLIGHT CHECKS")
    print("=" * 60)

    # 1. PDF file exists and is valid
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"  [FAIL] PDF file not found: {pdf_path}")
        return False

    size_mb = pdf.stat().st_size / (1024 * 1024)
    with open(pdf, "rb") as f:
        header = f.read(5)
    if header != b"%PDF-":
        print(f"  [FAIL] File is not a valid PDF (missing %%PDF header)")
        return False
    print(f"  [OK] PDF file exists ({size_mb:.1f} MB)")

    # 2. Settings load successfully
    try:
        from app.config.settings import get_settings
        settings = get_settings()
        print(f"  [OK] Settings loaded (env={settings.ENVIRONMENT})")
    except Exception as e:
        print(f"  [FAIL] Settings validation failed: {e}")
        return False

    # 3. Database connection
    try:
        from app.config.database import check_database_connection
        db_ok = await check_database_connection()
        if db_ok:
            print(f"  [OK] Database connected")
        else:
            print(f"  [FAIL] Database connection failed")
            checks_passed = False
    except Exception as e:
        print(f"  [FAIL] Database error: {e}")
        checks_passed = False

    # 4. Check tables exist
    try:
        from sqlalchemy import text
        from app.config.database import async_session_factory
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
            table_count = result.scalar()
            if table_count and table_count > 0:
                print(f"  [OK] Database schema exists ({table_count} tables)")
            else:
                print(f"  [FAIL] No tables found. Run: alembic upgrade head")
                checks_passed = False
    except Exception as e:
        print(f"  [FAIL] Schema check failed: {e}")
        checks_passed = False

    # 5. Anthropic API key format
    if settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
        print(f"  [OK] Anthropic API key format valid")
    else:
        print(f"  [WARN] Anthropic API key has unexpected format")

    # 6. Google credentials
    creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS
    if creds_path:
        creds_file = Path(creds_path)
        if not creds_file.is_absolute():
            creds_file = BACKEND_DIR / creds_file
        if creds_file.exists():
            print(f"  [OK] Google credentials file found")
        else:
            print(f"  [FAIL] Google credentials not found: {creds_file}")
            checks_passed = False
    else:
        print(f"  [INFO] No GOOGLE_APPLICATION_CREDENTIALS set (using default credentials)")

    # 7. Template type
    print(f"  [OK] Template type '{template}' is valid")

    # 8. Template sheet ID
    try:
        sheet_id = settings.get_template_sheet_id(template)
        print(f"  [OK] Template sheet ID configured ({sheet_id[:12]}...)")
    except ValueError as e:
        print(f"  [FAIL] Template sheet ID: {e}")
        checks_passed = False

    print("=" * 60)
    if checks_passed:
        print("  All checks passed.")
    else:
        print("  Some checks FAILED. Fix issues above before running.")
    print("=" * 60 + "\n")

    return checks_passed


# ------------------------------------------------------------------
# Pipeline execution
# ------------------------------------------------------------------

async def run_pipeline(pdf_path: str, template: str, email: str):
    """Run the full pipeline with timing and progress output."""
    from app.config.database import get_db_context
    from app.models.database import User
    from app.models.enums import UserRole
    from app.repositories.job_repository import JobRepository
    from app.services.job_manager import JobManager
    from app.background.task_queue import TaskQueue
    from sqlalchemy import select

    pipeline_start = time.time()
    step_timings = {}

    print("\n" + "=" * 60)
    print("  PDP AUTOMATION - LOCAL PIPELINE TEST")
    print("=" * 60)
    print(f"  PDF:      {pdf_path}")
    print(f"  Template: {template}")
    print(f"  Email:    {email}")
    print(f"  Started:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    async with get_db_context() as db:
        # Find or create test user
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            now = datetime.now(timezone.utc)
            user = User(
                google_id=f"local-test-{uuid4().hex[:8]}",
                email=email,
                name="Pipeline Test User",
                picture_url=None,
                role=UserRole.USER,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)
            print(f"\n  Created test user: {email} (id={user.id})")
        else:
            print(f"\n  Using existing user: {email} (id={user.id})")

        # Create job
        task_queue = TaskQueue()
        repo = JobRepository(db)
        manager = JobManager(repo, task_queue)

        job = await manager.create_job(
            user_id=user.id,
            template_type=template,
        )
        await db.commit()

        print(f"  Created job: {job.id}")
        print(f"  Steps: {len(JobManager.JOB_STEPS)}")

        # Wrap _execute_step to add timing and output
        original_execute = manager._execute_step

        async def timed_execute_step(job_id, step_id, p_path):
            description = STEP_DESCRIPTIONS.get(step_id, step_id)
            step_num = next(
                (i + 1 for i, s in enumerate(JobManager.JOB_STEPS) if s["id"] == step_id),
                "?",
            )
            total = len(JobManager.JOB_STEPS)

            print(f"\n{'='*60}")
            print(f"  [{step_num}/{total}] {description}")
            print(f"{'='*60}")

            start = time.time()
            try:
                step_result = await original_execute(job_id, step_id, p_path)
                elapsed = time.time() - start
                step_timings[step_id] = elapsed

                print(f"  Completed in {elapsed:.1f}s")
                if step_result:
                    for k, v in step_result.items():
                        # Truncate long values
                        v_str = str(v)
                        if len(v_str) > 100:
                            v_str = v_str[:97] + "..."
                        print(f"    {k}: {v_str}")

                # Save ZIP to disk after asset packaging (in-memory only otherwise)
                if step_id == "package_assets":
                    ctx = manager._pipeline_ctx.get(job_id, {})
                    zip_bytes = ctx.get("zip_bytes")
                    if zip_bytes:
                        output_dir = BACKEND_DIR / "scripts" / "pipeline_output"
                        output_dir.mkdir(exist_ok=True)
                        zip_path = output_dir / f"assets_{job_id}.zip"
                        with open(zip_path, "wb") as zf:
                            zf.write(zip_bytes)
                        zip_mb = len(zip_bytes) / (1024 * 1024)
                        print(f"  >> ZIP saved to disk: {zip_path} ({zip_mb:.1f} MB)")

                return step_result

            except Exception as e:
                elapsed = time.time() - start
                step_timings[step_id] = elapsed
                print(f"  FAILED after {elapsed:.1f}s")
                print(f"  Error: {e}")
                raise

        manager._execute_step = timed_execute_step

        # Resolve PDF to absolute path
        abs_pdf_path = str(Path(pdf_path).resolve())

        # Run the pipeline
        print(f"\n{'#'*60}")
        print(f"  STARTING PIPELINE EXECUTION")
        print(f"{'#'*60}")

        try:
            pipeline_result = await manager.execute_processing_pipeline(
                job_id=job.id,
                pdf_path=abs_pdf_path,
            )
            await db.commit()

            pipeline_elapsed = time.time() - pipeline_start

            # Get Anthropic usage stats
            anthropic_stats = None
            try:
                from app.integrations.anthropic_client import anthropic_service
                anthropic_stats = anthropic_service.get_session_usage()
            except Exception:
                pass

            # Print final summary
            print(f"\n{'#'*60}")
            print(f"  PIPELINE COMPLETE")
            print(f"{'#'*60}")
            print(f"\n  Total time: {pipeline_elapsed:.1f}s ({pipeline_elapsed/60:.1f} min)")

            print(f"\n  Step Timings:")
            for step_id, elapsed in step_timings.items():
                bar = "#" * int(elapsed / pipeline_elapsed * 40)
                pct = elapsed / pipeline_elapsed * 100
                print(f"    {step_id:<22} {elapsed:>6.1f}s  {pct:>5.1f}%  {bar}")

            if anthropic_stats:
                print(f"\n  Anthropic API Usage:")
                print(f"    Requests:     {anthropic_stats['request_count']}")
                print(f"    Input tokens: {anthropic_stats['total_input_tokens']:,}")
                print(f"    Output tokens:{anthropic_stats['total_output_tokens']:,}")
                print(f"    Total cost:   ${anthropic_stats['total_cost']:.4f}")

            # Extract output URLs from result
            print(f"\n  Output:")
            if "populate_sheet" in pipeline_result:
                sheet_data = pipeline_result["populate_sheet"]
                if "sheet_url" in sheet_data:
                    print(f"    Sheet URL:  {sheet_data['sheet_url']}")
                if "sheet_id" in sheet_data:
                    print(f"    Sheet ID:   {sheet_data['sheet_id']}")
                if "fields_written" in sheet_data:
                    print(f"    Fields:     {sheet_data['fields_written']} written")

            if "upload_cloud" in pipeline_result:
                cloud_data = pipeline_result["upload_cloud"]
                if "zip_url" in cloud_data:
                    print(f"    ZIP URL:    {cloud_data['zip_url']}")
                if "sheet_url" in cloud_data:
                    print(f"    Sheet URL:  {cloud_data['sheet_url']}")
                if "project_folder_id" in cloud_data:
                    print(f"    Folder ID:  {cloud_data['project_folder_id']}")

            print(f"\n  Job ID: {job.id}")
            print(f"  Status: COMPLETED")

            # Dump full result to JSON for debugging
            import json
            result_file = BACKEND_DIR / "scripts" / f"pipeline_result_{job.id}.json"
            with open(result_file, "w") as f:
                json.dump(
                    pipeline_result,
                    f,
                    indent=2,
                    default=str,
                )
            print(f"  Full result saved to: {result_file}")

        except Exception as e:
            pipeline_elapsed = time.time() - pipeline_start
            await db.commit()  # Commit the failure status

            print(f"\n{'#'*60}")
            print(f"  PIPELINE FAILED")
            print(f"{'#'*60}")
            print(f"  Error: {e}")
            print(f"  Total time: {pipeline_elapsed:.1f}s")
            print(f"  Job ID: {job.id}")

            if step_timings:
                print(f"\n  Steps completed before failure:")
                for step_id, elapsed in step_timings.items():
                    print(f"    {step_id:<22} {elapsed:>6.1f}s")

            logger.exception("Pipeline execution failed")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Done.")
    print(f"{'='*60}\n")


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

async def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run preflight checks unless skipped
    if not args.skip_preflight:
        preflight_ok = await run_preflight_checks(args.pdf_path, args.template)
        if not preflight_ok:
            print("Aborting. Fix preflight issues or use --skip-preflight to bypass.")
            sys.exit(1)

    # Run the pipeline
    await run_pipeline(args.pdf_path, args.template, args.email)


if __name__ == "__main__":
    asyncio.run(main())
