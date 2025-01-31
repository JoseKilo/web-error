import logging
from typing import Dict

from pyramid.httpexceptions import HTTPException
from pyramid.request import Request  # noqa: TCH002
from pyramid.view import view_config

from web_error import constant
from web_error.error import HttpException

logger = logging.getLogger(__name__)


@view_config(context=HTTPException, renderer="json")
def pyramid_handler(exc: HTTPException, request: Request) -> Dict:
    status = exc.code
    response = {
        "message": exc.explanation,
        "debug_message": exc.detail,
        "code": None,
    }

    if "predicate mismatch" in exc.detail and "request_method" in exc.detail:
        status = 405
        response["message"] = "Request method not allowed."

    if status >= constant.SERVER_ERROR:
        logger.exception(exc.explanation)

    request.response.status = status
    return response


@view_config(context=Exception, renderer="json")
def exception_handler(exc: Exception, request: Request) -> Dict:
    # If the view has two formal arguments, the first is the context.
    # The context is always available as ``request.context`` too.
    status = constant.SERVER_ERROR
    message = "Unhandled exception occurred."
    response = {
        "message": message,
        "debug_message": str(exc),
        "code": None,
    }

    if isinstance(exc, HttpException):
        response = exc.marshal()
        status = exc.status

    if status >= constant.SERVER_ERROR:
        logger.exception(message)

    request.response.status = status
    return response
