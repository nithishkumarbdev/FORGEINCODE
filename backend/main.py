import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import mentor
from checker import check_step
from config import get_settings
from curriculum import TRACKS, find_step
from database import Progress, get_db, init_db
from schemas import MentorRequest, SubmitRequest

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("forge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Forge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/curriculum")
def get_curriculum():
    """Public step data only - never test_cases/harness/patterns, or the
    exercise turns into an answer key instead of an exercise."""
    return [
        {
            "id": track.id,
            "title": track.title,
            "summary": track.summary,
            "projects": [
                {
                    "id": project.id,
                    "title": project.title,
                    "summary": project.summary,
                    "steps": [
                        {
                            "id": step.id,
                            "title": step.title,
                            "language": step.language,
                            "instructions": step.instructions,
                            "starter_code": step.starter_code,
                        }
                        for step in project.steps
                    ],
                }
                for project in track.projects
            ],
        }
        for track in TRACKS
    ]


@app.get("/api/progress")
def get_progress(db: Session = Depends(get_db)):
    rows = db.query(Progress).all()
    return {
        r.step_id: {"passed": r.passed, "attempts": r.attempts, "submitted_code": r.submitted_code}
        for r in rows
    }


@app.post("/api/steps/{step_id}/submit")
def submit_step(step_id: str, req: SubmitRequest, db: Session = Depends(get_db)):
    step = find_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="No such exercise")

    result = check_step(step, req.code)

    progress = db.query(Progress).filter(Progress.step_id == step_id).first()
    if not progress:
        progress = Progress(step_id=step_id, attempts=0, passed=False)
        db.add(progress)

    progress.submitted_code = req.code
    progress.attempts += 1
    progress.passed = result["passed"]
    progress.updated_at = datetime.utcnow()
    db.commit()

    return {"passed": result["passed"], "message": result["message"], "attempts": progress.attempts}


@app.post("/api/steps/{step_id}/hint")
def hint_for_step(step_id: str, req: MentorRequest, db: Session = Depends(get_db)):
    step = find_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="No such exercise")

    progress = db.query(Progress).filter(Progress.step_id == step_id).first()
    last_result = None
    if progress and progress.attempts > 0:
        last_result = "passed" if progress.passed else "did not pass yet"

    try:
        hint = mentor.ask_mentor(step.title, step.instructions, req.code, req.question, last_result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=502, detail="The mentor is unavailable right now, please try again")

    return {"hint": hint}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
