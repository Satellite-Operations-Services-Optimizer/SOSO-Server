from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routes.image_routes import router as image_router
from routes.satellite_activities_routes import router as activity_router
from helpers.RequestValidator import HttpErrorHandler

app = FastAPI()

@app.exception_handler(HttpErrorHandler)
async def http_error_handler(request: Request, exc: HttpErrorHandler):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_text": exc.detail, "status_code": exc.status_code},
    )


@app.on_event("startup")
async def startup_event():
    print("ServerRequestHandlerAPI Starting...")
    pass


@app.on_event("shutdown")
async def shutdown_event():
    print("ServerRequestHandlerAPI Closing...")
    pass


app.include_router(image_router, tags=["Image Operations"], prefix="/images")
app.include_router(activity_router, tags=["Satellite Activities Operation"], prefix="/activities")
