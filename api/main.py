from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent.query import fetch_documents, synthesize_answer
from db.migrate import migrate

app = FastAPI()


class QuestionRequest(BaseModel):
    question: str


class SynthesizeRequest(BaseModel):
    question: str
    results: list


@app.on_event("startup")
def startup():
    migrate()
    from ingestion.scheduler import start
    start()


@app.post("/query/fetch")
def query_fetch(request: QuestionRequest):
    try:
        return fetch_documents(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/synthesize")
def query_synthesize(request: SynthesizeRequest):
    try:
        answer = synthesize_answer(request.question, request.results)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync")
def sync():
    from ingestion.scheduler import run_all
    try:
        run_all()
        return {"status": "sync complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
