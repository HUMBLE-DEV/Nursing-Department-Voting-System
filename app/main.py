from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import auth_router, admin_router, student_router
from app.config import settings

from app import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed.create_first_admin()
    yield


app = FastAPI(title="Departmental Voting System", lifespan=lifespan)

# TIGHTEN THIS before going live: replace "*" with your actual deployed frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(student_router.router)

# candidate photos
app.mount("/static", StaticFiles(directory="static"), name="static")
# the HTML/JS frontend itself — served at the root, index.html is the default page
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
