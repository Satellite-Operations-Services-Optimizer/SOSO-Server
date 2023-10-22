from fastapi import FastAPI
from dotenv import dotenv_values
from Routes.queue_routes import router as queue_router

config = dotenv_values()
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    print("ServerRequestHandlerAPI Starting...")
    pass


@app.on_event("shutdown")
async def shutdown_event():
    print("ServerRequestHandlerAPI Closing...")
    pass

app.include_router(queue_router, tags=["Queue Operations"], prefix="/queues")
