from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from Routes.image_routes import router as image_router
from Routes.satellite_activities_routes import router as activity_router
from Routes.asset_routes import router as asset_router
from Routes.schedule_routes import router as schedule_router
from Routes.maintenance_router import router as maintenance_router
from Helpers.request_validator import HttpErrorHandler

def lifespan(app: FastAPI):
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
    allow_origins=["http://localhost:3000"],  # Replace with the correct frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Or restrict to ["GET", "POST"], etc.
    allow_headers=["*"],
)

add_pagination(app)

app.include_router(image_router, tags=["Image Operations"], prefix="/images")
app.include_router(activity_router, tags=["Satellite Activities Operation"], prefix="/activities")
app.include_router(asset_router, tags=["Asset Creation"], prefix="/assets")
app.include_router(schedule_router, tags=["Schedule Retrieval"], prefix="/schedules")
app.include_router(maintenance_router, tags=["Maintenence Activities"], prefix="/maintenance")