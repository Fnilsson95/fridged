from fastapi import FastAPI

app = FastAPI(title="fridged")

@app.get("/api/health")
def health() -> dict[str, str]:
    """Used to check that the backend is running"""
    return {"status": "ok"}