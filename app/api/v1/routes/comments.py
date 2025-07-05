import logging

from fastapi import APIRouter, Header, Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def verify(authorization: str = Header(None)) -> Response:
    return Response("{'success': True, 'route': 'comments'}")
