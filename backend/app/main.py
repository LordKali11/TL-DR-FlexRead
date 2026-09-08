import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import articles, users, personalization, system
from .services.article_ingestion import article_ingestion_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nzz-flexread")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ingest articles directly from remote MongoDB database
    logger.info("Initializing NZZ FlexRead Backend with remote MongoDB persistence...")
    found, indexed, errors = article_ingestion_service.ingest_from_mongodb()
    logger.info(f"Startup complete: {indexed}/{found} articles loaded directly from remote MongoDB collection.")
    yield
    logger.info("Shutting down NZZ FlexRead Backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# CORS configuration for frontend and browser extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(system.router)
app.include_router(articles.router)
app.include_router(users.router)
app.include_router(personalization.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
