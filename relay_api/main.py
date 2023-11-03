from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routes import images, activities
from helpers.RequestValidator import HttpErrorHandler
import os

app = FastAPI()

@app.exception_handler(HttpErrorHandler)
async def http_error_handler(request: Request, exc: HttpErrorHandler):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_text": exc.detail, "status_code": exc.status_code},
    )

app.include_router(images.router, tags=["Image Operations"], prefix="/images")
app.include_router(activities.router, tags=["Satellite Activities Operation"], prefix="/activities")
