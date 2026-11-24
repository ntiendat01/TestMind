"""Bounded requests for stateless review validation."""

from app.services.eval.review_packets import ReviewCase
from pydantic import BaseModel, Field


class ReviewPacketRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5_000_000)


class ReviewScoresRequest(ReviewPacketRequest):
    cases: list[ReviewCase] = Field(min_length=1, max_length=500)
