"""Poll latest job status every 10 seconds."""
import asyncio
from app.config.database import async_session_factory
from sqlalchemy import text


async def poll():
    skip_id = "508e330c-85f2-4f24-93be-eab80daddd9f"
    print("Waiting for new job...")
    found = False
    for i in range(180):
        async with async_session_factory() as db:
            r = await db.execute(
                text(
                    "SELECT id, status, progress, current_step, error_message "
                    "FROM jobs ORDER BY created_at DESC LIMIT 1"
                )
            )
            row = r.fetchone()
            d = dict(row._mapping)
            jid = str(d["id"])
            if jid == skip_id and not found:
                pass  # still waiting
            else:
                if not found:
                    print(f"New job: {jid}")
                    found = True
                status = d["status"]
                progress = d["progress"]
                step = d["current_step"]
                err = d["error_message"]
                print(f"  [{i*10}s] {status} | {progress}% | {step} | err={err}")
                if status in ("completed", "failed"):
                    break
        await asyncio.sleep(10)


asyncio.run(poll())
