from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi_pagination import add_pagination
from routes.image_routes import router as image_router
from routes.satellite_activity_routes import router as satellite_activity_router
from routes.asset_routes import router as asset_router
from routes.schedule_routes import router as schedule_router
from routes.outage_routes import router as outage_router
from routes.maintenance_router import router as maintenance_router
from helpers.request_validation_helper import HttpErrorHandler
import uvicorn


async def lifespan(app: FastAPI):
    print("ServerRequestHandlerAPI Starting...")
    yield
    print("ServerRequestHandlerAPI Closing...")

app = FastAPI(lifespan=lifespan)

@app.exception_handler(HttpErrorHandler)
async def http_error_handler(request: Request, exc: HttpErrorHandler):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with the correct frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Or restrict to ["GET", "POST"], etc.
    allow_headers=["*"],
)

add_pagination(app)

app.include_router(satellite_activity_router, tags=["Satellite Operation"], prefix="/assets/satellites")
app.include_router(asset_router, tags=["Asset Creation"], prefix="/assets")
app.include_router(schedule_router, tags=["Schedule Interactions"], prefix="/schedules")
app.include_router(image_router, tags=["Image Order Operations"], prefix="/imaging")
app.include_router(maintenance_router, tags=["Maintenence Order Operations"], prefix="/maintenance")
app.include_router(outage_router, tags=["Outage Order Operations"], prefix="/outage")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)