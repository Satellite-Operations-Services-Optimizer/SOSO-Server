from fastapi import FastAPI

app = FastAPI()

@app.get("/home")
def index():
    return {"message": "Hello, I am the image management server!"}
