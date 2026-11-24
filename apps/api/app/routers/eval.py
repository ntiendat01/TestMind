"""Stateless QA review imports. No filesystem access or model calls."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute
from starlette.types import Message

from app.core.errors import APIError
from app.schemas.eval import ReviewPacketRequest, ReviewScoresRequest
from app.services.eval.review import ReviewScore, parse_scores
from app.services.eval.review_packets import ReviewCase, parse_cases, validate_cases

MAX_REVIEW_BYTES = 8 * 1024 * 1024


class BoundedReviewRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def bounded(request: Request) -> Response:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_REVIEW_BYTES:
                    raise APIError(413, "review_too_large", "Review request exceeds 8 MiB.")
                body.extend(chunk)

            async def receive() -> Message:
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            return await handler(Request(request.scope, receive))

        return bounded


router = APIRouter(prefix="/v1/eval/review", tags=["eval"], route_class=BoundedReviewRoute)


@router.post("/packet", response_model=list[ReviewCase])
def validate_packet(payload: ReviewPacketRequest) -> list[ReviewCase]:
    try:
        cases = parse_cases(payload.content)
        if len(cases) > 500:
            raise ValueError("Review packets may contain at most 500 cases.")
        return cases
    except ValueError as exc:
        raise APIError(422, "invalid_review_packet", "Invalid review packet or digest.") from exc


@router.post("/scores/validate", response_model=list[ReviewScore])
def validate_scores(payload: ReviewScoresRequest) -> list[ReviewScore]:
    try:
        cases = validate_cases(payload.cases)
        return parse_scores([payload.content], cases, keep_pending=True)
    except ValueError as exc:
        raise APIError(422, "invalid_review_scores", "Invalid review scores or packet.") from exc
