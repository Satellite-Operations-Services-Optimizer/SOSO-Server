from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi_pagination import add_pagination
from Routes.image_routes import router as image_router
from Routes.satellite_activities_routes import router as activity_router
from Routes.asset_routes import router as asset_router
from Routes.schedule_routes import router as schedule_router
from Routes.maintenance_router import router as maintenance_router
from Helpers.request_validation_helper import HttpErrorHandler
import uvicorn

def lifespan(app: FastAPI):
    print("ServerRequestHandlerAPI Starting...")
    yield
    print("ServerRequestHandlerAPI Closing...")

app = FastAPI(lifespan=lifespan)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:80/satellite/1/state");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)

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

app.include_router(image_router, tags=["Image Operations"], prefix="/images")
app.include_router(activity_router, tags=["Satellite Activities Operation"], prefix="/satellite")
app.include_router(asset_router, tags=["Asset Creation"], prefix="/assets")
app.include_router(schedule_router, tags=["Schedule Retrieval"], prefix="/schedules")
app.include_router(maintenance_router, tags=["Maintenence Activities"], prefix="/maintenance")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)