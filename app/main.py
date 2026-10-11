from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.schema import init_db
from app.mcp.server import mcp_app
from app.modules.students.controller import router as students_router
from app.modules.analytics.controller import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: create tables if missing. Never drops data.
    # Wrapped so /ui + /docs still serve even if MySQL creds aren't set yet.
    try:
        init_db()
    except Exception as e:  # noqa: BLE001
        print(f"[startup] WARNING: could not connect to MySQL ({e}). "
              "Update .env DB_PASSWORD then restart. API/DB routes will 500 until then.")
    yield


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    """Run our startup steps and FastMCP's lifespan together, yielding no
    lifespan *state*.

    Yielding None (instead of FastMCP's `combine_lifespans` merged dict) keeps
    the mount portable: Starlette only accepts a non-None lifespan result when
    the ASGI server puts a "state" dict in the lifespan scope (uvicorn does;
    other servers and in-process test harnesses don't). Nothing here consumes
    lifespan state.
    """
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(lifespan(app))
        await stack.enter_async_context(mcp_app.lifespan(app))
        yield


# The MCP server's lifespan must run too, otherwise its session manager never
# initialises. Ours (init_db) and FastMCP's are combined in order.
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=combined_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

# LLM interface: same data + rules as the REST API above, served as MCP tools
# at settings.MCP_PATH (default /mcp).
app.mount(settings.MCP_PATH, mcp_app)
