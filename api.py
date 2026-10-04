"""Optional FastAPI exposure:  uvicorn api:app --reload"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import CodeAgent
from code_generator import CodeGenerator

app = FastAPI(title="Code Snippet Generator API")
_agent = None


class Req(BaseModel):
    requirement: str
    constraints: str = ""


@app.post("/generate")
def generate(body: Req):
    global _agent
    try:
        _agent = _agent or CodeAgent(CodeGenerator())
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    return _agent.run(body.requirement, constraints=body.constraints).model_dump()
