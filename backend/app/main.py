from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, blocos, condominios, hidrometros, unidades

app = FastAPI(title="HidroMeter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    # Formato de erro padronizado da API: {"erro": "mensagem"}.
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    primeiro = exc.errors()[0] if exc.errors() else None
    mensagem = f"{'.'.join(str(p) for p in primeiro['loc'][1:])}: {primeiro['msg']}" if primeiro else "Dados inválidos."
    return JSONResponse(status_code=422, content={"erro": mensagem})


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(condominios.router)
app.include_router(blocos.router)
app.include_router(unidades.router)
app.include_router(hidrometros.router)
