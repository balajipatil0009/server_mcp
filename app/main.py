from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine

# Import models so metadata registers all tables before create_all
from app.modules.students import model as _student_model  # noqa: F401
from app.modules.analytics import model as _analytics_model  # noqa: F401
from app.modules.students.controller import router as students_router
from app.modules.analytics.controller import router as analytics_router

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Dev convenience: auto-create tables. Use Alembic for prod migrations.
    # Wrapped so /ui + /docs still serve even if MySQL creds aren't set yet.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:  # noqa: BLE001
        print(f"[startup] WARNING: could not connect to MySQL ({e}). "
              "Update .env DB_PASSWORD then restart. API/DB routes will 500 until then.")


@app.get("/", tags=["Health"], include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


app.include_router(students_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)

# Sample frontend (no build step): served at /ui/
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")
