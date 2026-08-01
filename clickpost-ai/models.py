from typing import List
from pydantic import BaseModel, Field

class Signal(BaseModel):
    signal_type: str
    description: str
    evidence: str
    source_url: str

class SignalExtractionResult(BaseModel):
    company: str
    signals: List[Signal]
    confidence: float
    reasoning: str
    sources: List[str]

class ScoredAccount(BaseModel):
    company: str
    website: str
    industry: str
    score: int = 0
    priority: str = "Low"
    confidence: float = 0.0
    reason: str = ""
    recommendation: str = ""
    signals: List[Signal] = Field(default_factory=list)

class RankedAccount(ScoredAccount):
    rank: int = 0

class Outreach(BaseModel):
    company: str
    linkedin_message: str
    email_message: str
