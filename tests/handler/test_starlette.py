import json
from unittest import mock

from starlette.exceptions import HTTPException

from web_error import constant, error
from web_error.handler import starlette


class ATestError(error.ServerException):
    message = "This is an error."
    code = "E123"


class TestExceptionHandler:
    def test_unexpected_error(self, monkeypatch):
        monkeypatch.setattr(starlette.logger, "exception", mock.Mock())

        request = mock.Mock()
        exc = Exception("Something went bad")

        response = starlette.exception_handler(request, exc)

        assert response.status_code == constant.SERVER_ERROR
        assert json.loads(response.body) == {
            "message": "Unhandled exception occurred.",
            "debug_message": "Something went bad",
            "code": None,
        }
        assert starlette.logger.exception.call_args == mock.call(
            "Unhandled exception occurred.",
            exc_info=(type(exc), exc, None),
        )

    def test_starlette_error(self):
        request = mock.Mock()
        exc = HTTPException(constant.NOT_FOUND, "something bad")

        response = starlette.exception_handler(request, exc)

        assert response.status_code == constant.NOT_FOUND
        assert json.loads(response.body) == {
            "message": "something bad",
            "debug_message": "(404, 'something bad')",
            "code": None,
        }

    def test_known_error(self):
        request = mock.Mock()
        exc = ATestError("something bad")

        response = starlette.exception_handler(request, exc)

        assert response.status_code == constant.SERVER_ERROR
        assert json.loads(response.body) == {
            "message": "This is an error.",
            "debug_message": "something bad",
            "code": "E123",
        }

    def test_error_with_origin(self):
        request = mock.Mock(headers={"origin": "localhost"})
        exc = ATestError("something bad")

        eh = starlette.generate_handler_with_cors()
        response = eh(request, exc)

        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

    def test_error_with_origin_and_cookie(self):
        request = mock.Mock(headers={"origin": "localhost", "cookie": "something"})
        exc = ATestError("something bad")

        eh = starlette.generate_handler_with_cors()
        response = eh(request, exc)

        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "localhost"

    def test_missing_token_with_origin_limited_origins(self):
        request = mock.Mock(headers={"origin": "localhost", "cookie": "something"})
        exc = ATestError("something bad")

        eh = starlette.generate_handler_with_cors(allow_origins=["localhost"])
        response = eh(request, exc)

        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "localhost"

    def test_missing_token_with_origin_limited_origins_no_match(self):
        request = mock.Mock(headers={"origin": "localhost2", "cookie": "something"})
        exc = ATestError("something bad")

        eh = starlette.generate_handler_with_cors(allow_origins=["localhost"])
        response = eh(request, exc)

        assert "access-control-allow-origin" not in response.headers
