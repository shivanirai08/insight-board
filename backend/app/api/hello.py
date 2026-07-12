"""
First real endpoint — teaching vehicle for request → validation → response.

Concepts covered here:
  - APIRouter: group related endpoints
  - Path / query parameters
  - Pydantic response models (OpenAPI + validation)
  - Status codes and HTTPException
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class Greeting(BaseModel):
    """Response schema — FastAPI serializes this to JSON and documents it in /docs."""

    message: str
    name: str
    excited: bool = False


class EchoBody(BaseModel):
    """Request body schema — invalid JSON/types → automatic 422 Unprocessable Entity."""

    text: str = Field(..., min_length=1, max_length=200, description="Text to echo back")
    shout: bool = False


@router.get("/hello", response_model=Greeting)
def say_hello(
    name: str = Query(default="world", min_length=1, max_length=50),
    excited: bool = False,
) -> Greeting:
    """
    GET /api/hello?name=Ada&excited=true

    Query params are parsed from the URL. Types and constraints are validated.
    """
    message = f"Hello, {name}!"
    if excited:
        message = message.upper().replace("!", "!!!")
    return Greeting(message=message, name=name, excited=excited)


@router.get("/hello/{name}", response_model=Greeting)
def say_hello_path(name: str) -> Greeting:
    """
    GET /api/hello/Ada

    Path parameters are required pieces of the URL path.
    """
    if name.lower() == "error":
        # Teaching example: raise HTTPException for expected client/server errors.
        raise HTTPException(status_code=400, detail="Name 'error' is reserved for demos.")
    return Greeting(message=f"Hello, {name}!", name=name)


@router.post("/echo", response_model=Greeting)
def echo(body: EchoBody) -> Greeting:
    """
    POST /api/echo  with JSON body {"text": "hi", "shout": true}

    Bodies are validated against Pydantic models. Try sending bad data in /docs.
    """
    text = body.text.upper() if body.shout else body.text
    return Greeting(message=text, name="echo", excited=body.shout)
