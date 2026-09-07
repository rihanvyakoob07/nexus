from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.db import init_db
from app.routers import auth, engineers, jds, assessments, teams, dashboard, deployments, resumes, opportunities


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="NEXUS API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(engineers.router)
app.include_router(jds.router)
app.include_router(assessments.router)
app.include_router(teams.router)
app.include_router(dashboard.router)
app.include_router(deployments.router)
app.include_router(resumes.router)
app.include_router(opportunities.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}
