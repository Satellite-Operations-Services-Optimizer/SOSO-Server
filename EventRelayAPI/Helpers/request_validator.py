from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from typing import Type, Callable
class HttpErrorHandler(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)



def validate_request_schema(request_data: dict, model_type: Type[BaseModel]) -> BaseModel:
    try:
        return model_type(**request_data)
    except ValidationError as e:
        error_details = e.errors()
        raise HttpErrorHandler(status_code=400, detail=f"Invalid Payload Schema: {error_details}")