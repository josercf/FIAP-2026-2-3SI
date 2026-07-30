from fastapi import FastAPI, Header, HTTPException
import requests
import os

app = FastAPI()

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:3000")

@app.post("/ask-ai")
def ask_ai(prompt: str, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    
    token = authorization.replace("Bearer ", "")
    
    # 1. Validar token no Auth Service
    try:
        resp = requests.post(f"{AUTH_URL}/validate", json={"token": token})
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Token")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Auth Service Unavailable")

    # 2. Executar Lógica Fake de AI
    return {"reply": f"Analisando telemetria para o prompt: '{prompt}'. Tudo normal com a frota!"}
