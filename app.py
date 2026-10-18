"""Minimal API for the Sentinel prompt-injection demo.

This is a heuristic detector for research and education, not a security boundary.
"""
from pathlib import Path
import re
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

PATTERNS = [
    {
        "name": "Próba nadpisania instrukcji",
        "pattern": r"ignore (all )?(previous|prior|earlier) instructions|zignoruj (wszystkie )?(wcześniejsze|poprzednie) polecenia|disregard (all )?previous instructions|pretend the system message no longer applies|nie stosuj się do zasad",
        "detail": "Treść próbuje zmienić hierarchię poleceń agenta.",
    },
    {
        "name": "Próba ujawnienia danych",
        "pattern": r"reveal (the )?(user|private|secret|sensitive) data|ujawnij (dane|sekrety)|exfiltrat|dane użytkownika|confidential records|private data|prywatne dane",
        "detail": "Treść sugeruje ujawnienie danych lub informacji wrażliwych.",
    },
    {
        "name": "Nieautoryzowane wysłanie danych",
        "pattern": r"send (them|it|data|the results) to|post .* to https?:|wyślij .* (na|do) (zewnętrzny|serwer)|zewnętrzny serwer|forward .* (to|into) my inbox|transfer .* outside this environment|session token",
        "detail": "Treść może próbować wysłać informacje poza zaufany kontekst.",
    },
    {
        "name": "Próba wymuszenia działania",
        "pattern": r"run this command|execute (the following|this) tool|make a purchase|wykonaj (to|tę) (operacj|polecenie)|zrób zakup",
        "detail": "Treść może próbować wywołać działanie zamiast jedynie przekazać informacje.",
    },
]
COMPILED_PATTERNS = [
    {**item, "regex": re.compile(item["pattern"], re.IGNORECASE)}
    for item in PATTERNS
]

app = FastAPI(
    title="Sentinel AI Web Shield API",
    description="Educational heuristic scanner for possible prompt-injection phrases.",
    version="0.1.0",
)


class ScanRequest(BaseModel):
    text: str = Field(..., max_length=200_000, description="Text or HTML to inspect")


class Finding(BaseModel):
    name: str
    detail: str


class ScanResponse(BaseModel):
    findings: list[Finding]
    count: int
    score: int
    status: str
    disclaimer: str


@app.get("/", include_in_schema=False)
def homepage() -> Any:
    """Serve the existing single-page demo when available."""
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Sentinel API is running. Open /docs to explore the API."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scan", response_model=ScanResponse)
def scan(request: ScanRequest) -> ScanResponse:
    findings = [
        Finding(name=item["name"], detail=item["detail"])
        for item in COMPILED_PATTERNS
        if item["regex"].search(request.text)
    ]
    count = len(findings)
    score = min(99, 45 + count * 15) if count else 0
    return ScanResponse(
        findings=findings,
        count=count,
        score=score,
        status="requires_attention" if count else "no_known_patterns_found",
        disclaimer=(
            "Heurystyka wykrywa wybrane frazy. Brak trafień nie oznacza, że treść jest bezpieczna."
        ),
    )
