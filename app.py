"""
Entrypoint for the Resume Screener API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import extract

app = FastAPI(
    title = "Resume Screener API",
    description="This is a Resume Screener API.",
    summary="This API is used to interact with the Resume Screener.",
    version="1.0",
    contact={
        "name": "Suraj Potnuru",
        "url": "https://github.com/suraj-potnuru/resume-screener",
        "email": "surajpotnuru7@gmail.com",
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"]
)

app.include_router(extract.router)

@app.get("/api/heartbeat")
async def heartbeat():
    """
    Simple hearbeat endpoint. Returns 200.
    """
    return JSONResponse(status_code=200, content = {"message": "API is running !"})
