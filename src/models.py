from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Page:
    document_id: str
    filename: str
    number: int
    original_text: str
    text: str


@dataclass(frozen=True)
class Document:
    document_id: str
    filename: str
    size_bytes: int
    page_count: int
    pages: list[Page]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    filename: str
    page: int
    text: str
    start: int


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Evidence(BaseModel):
    source_id: str
    quote: str = Field(min_length=12, max_length=1500)


class Claim(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    evidence: list[Evidence] = Field(min_length=1, max_length=6)


class GeneratedAnswer(BaseModel):
    status: Literal["answered", "insufficient"]
    claims: list[Claim] = Field(default_factory=list, max_length=12)


class Rewrite(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    needs_clarification: bool = False


@dataclass(frozen=True)
class Citation:
    source_id: str
    chunk: Chunk
    quote: str
    score: float


@dataclass
class Answer:
    text: str
    status: str
    citations: list[Citation] = field(default_factory=list)
    resolved_question: str = ""
