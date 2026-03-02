"""
Isolated test for Google Drive upload operations.

Tests the three operations from pipeline step 13 (upload_cloud):
  1. Create project folder structure in Shared Drive
  2. Upload a file (bytes) to the Output folder
  3. Move a file between folders

Usage:
    python scripts/test_drive_upload.py
    python scripts/test_drive_upload.py --cleanup   # delete created folders after test
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.WARNING)

logger = logging.getLogger("drive_test")

TEST_PROJECT_NAME = "_DRIVE_TEST_deleteme"


async def run_test(cleanup: bool = False):
    from app.integrations.drive_client import drive_client

    created_ids = []  # track for cleanup

    print("\n" + "=" * 60)
    print("  GOOGLE DRIVE UPLOAD TEST")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Create project folder structure
    # ------------------------------------------------------------------
    print("\n[1/5] Creating project folder structure...")
    t0 = time.time()
    try:
        structure = await drive_client.create_project_structure(TEST_PROJECT_NAME)
        elapsed = time.time() - t0
        print(f"  OK ({elapsed:.1f}s)")
        for key, fid in structure.items():
            print(f"    {key}: {fid}")
        created_ids.append(structure["project"])  # deleting project deletes children
    except Exception as e:
        print(f"  FAILED: {e}")
        logger.exception("create_project_structure failed")
        return

    # ------------------------------------------------------------------
    # 2. Upload small test bytes to Output folder
    # ------------------------------------------------------------------
    print("\n[2/5] Uploading small test file (1 KB) to Output folder...")
    test_bytes = b"PDP Drive upload test -- safe to delete\n" * 25  # ~1 KB
    t0 = time.time()
    try:
        small_file_id = await drive_client.upload_file_bytes(
            file_bytes=test_bytes,
            file_name="test_small.txt",
            folder_id=structure["output"],
            mime_type="text/plain",
        )
        elapsed = time.time() - t0
        print(f"  OK ({elapsed:.1f}s) file_id={small_file_id}")
        created_ids.append(small_file_id)
    except Exception as e:
        print(f"  FAILED: {e}")
        logger.exception("upload small file failed")
        return

    # ------------------------------------------------------------------
    # 3. Upload larger test bytes (~5 MB) to Output folder
    # ------------------------------------------------------------------
    print("\n[3/5] Uploading larger test file (5 MB) to Output folder...")
    large_bytes = os.urandom(5 * 1024 * 1024)  # 5 MB random data
    t0 = time.time()
    try:
        large_file_id = await drive_client.upload_file_bytes(
            file_bytes=large_bytes,
            file_name="test_5mb.bin",
            folder_id=structure["output"],
            mime_type="application/octet-stream",
        )
        elapsed = time.time() - t0
        print(f"  OK ({elapsed:.1f}s) file_id={large_file_id}")
        created_ids.append(large_file_id)
    except Exception as e:
        print(f"  FAILED: {e}")
        logger.exception("upload large file failed")
        return

    # ------------------------------------------------------------------
    # 4. Move the small file from Output to Source folder
    # ------------------------------------------------------------------
    print("\n[4/5] Moving small file from Output to Source folder...")
    t0 = time.time()
    try:
        move_result = await drive_client.move_file(
            file_id=small_file_id,
            destination_folder_id=structure["source"],
        )
        elapsed = time.time() - t0
        print(f"  OK ({elapsed:.1f}s)")
        print(f"    new parents: {move_result.get('parents', [])}")
    except Exception as e:
        print(f"  FAILED: {e}")
        logger.exception("move_file failed")

    # ------------------------------------------------------------------
    # 5. Get file metadata (verify webViewLink)
    # ------------------------------------------------------------------
    print("\n[5/5] Getting file metadata...")
    t0 = time.time()
    try:
        metadata = await drive_client.get_file_metadata(large_file_id)
        elapsed = time.time() - t0
        print(f"  OK ({elapsed:.1f}s)")
        print(f"    name: {metadata.get('name')}")
        print(f"    size: {metadata.get('size')} bytes")
        print(f"    webViewLink: {metadata.get('webViewLink')}")
    except Exception as e:
        print(f"  FAILED: {e}")
        logger.exception("get_file_metadata failed")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    if cleanup:
        print("\n[CLEANUP] Deleting test project folder...")
        try:
            await drive_client.delete_file(structure["project"])
            print("  OK - project folder and contents deleted")
        except Exception as e:
            print(f"  FAILED: {e}")
            print(f"  Manual cleanup needed. Folder IDs: {created_ids}")
    else:
        print(f"\n[INFO] Test artifacts left in Shared Drive under Projects/{TEST_PROJECT_NAME}/")
        print(f"  Run with --cleanup to auto-delete, or delete manually.")

    print("\n" + "=" * 60)
    print("  DONE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    do_cleanup = "--cleanup" in sys.argv
    asyncio.run(run_test(cleanup=do_cleanup))
