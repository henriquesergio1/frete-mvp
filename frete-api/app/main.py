
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import veiculos, cargas, fretes, parametros

app = FastAPI(title="Frete API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(veiculos.router)
app.include_router(cargas.router)
app.include_router(fretes.router)
app.include_router(parametros.router)
