"""Tests for the API gateway module."""
import pytest
from acquisition_platform.api_gateway import (
    APIRoute,
    APIRequest,
    APIResponse,
    APIGateway,
)


class TestAPIRoute:
    """Tests for APIRoute dataclass."""

    def test_route_creation(self):
        """Route created with correct attributes."""
        route = APIRoute(path="/test", method="GET", handler="test_handler", auth_required=True)
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.handler == "test_handler"
        assert route.auth_required is True

    def test_route_defaults(self):
        """Route defaults auth_required to False."""
        route = APIRoute(path="/test", method="GET", handler="test_handler")
        assert route.auth_required is False


class TestAPIRequest:
    """Tests for APIRequest dataclass."""

    def test_request_creation(self):
        """Request created with correct attributes."""
        req = APIRequest(method="POST", path="/test", headers={"Auth": "token"}, body={"key": "value"})
        assert req.method == "POST"
        assert req.path == "/test"
        assert req.headers == {"Auth": "token"}
        assert req.body == {"key": "value"}

    def test_request_defaults(self):
        """Request defaults to empty dicts."""
        req = APIRequest(method="GET", path="/test")
        assert req.headers == {}
        assert req.body == {}


class TestAPIResponse:
    """Tests for APIResponse dataclass."""

    def test_response_creation(self):
        """Response created with correct attributes."""
        resp = APIResponse(status=200, body={"result": "ok"}, headers={"Content-Type": "application/json"})
        assert resp.status == 200
        assert resp.body == {"result": "ok"}
        assert resp.headers == {"Content-Type": "application/json"}

    def test_response_defaults(self):
        """Response defaults to empty dicts."""
        resp = APIResponse(status=200)
        assert resp.body == {}
        assert resp.headers == {}


class TestAPIGateway:
    """Tests for APIGateway class."""

    def test_route_registration(self):
        """Route registered."""
        gw = APIGateway()
        route = gw.register_route("/test", "GET", "test_handler", auth_required=True)
        assert isinstance(route, APIRoute)
        assert route.path == "/test"
        assert route.method == "GET"
        assert route.handler == "test_handler"
        assert route.auth_required is True
        assert len(gw.routes) == 1

    def test_request_handling(self):
        """Request handled."""
        gw = APIGateway()
        gw.register_route("/test", "GET", "test_handler")
        req = APIRequest(method="GET", path="/test")
        resp = gw.handle_request(req)
        assert isinstance(resp, APIResponse)
        assert resp.status == 200

    def test_empty_request(self):
        """Empty request returns defaults."""
        gw = APIGateway()
        req = APIRequest(method="GET", path="/nonexistent")
        resp = gw.handle_request(req)
        assert isinstance(resp, APIResponse)
        assert resp.status == 404
        assert resp.body == {}

    def test_rate_limiting(self):
        """Rate limiting applied."""
        gw = APIGateway()
        # First request should be allowed
        assert gw.rate_limit("client1", max_requests=5) is True
        # Exhaust the limit
        for _ in range(4):
            gw.rate_limit("client1", max_requests=5)
        # Next request should be denied
        assert gw.rate_limit("client1", max_requests=5) is False
        # Different client should be allowed
        assert gw.rate_limit("client2", max_requests=5) is True

    def test_authentication(self):
        """Authentication checked."""
        gw = APIGateway()
        # Request without auth token should fail
        req_no_auth = APIRequest(method="GET", path="/test", headers={})
        assert gw.authenticate(req_no_auth) is False
        # Request with auth token should pass
        req_with_auth = APIRequest(method="GET", path="/test", headers={"Authorization": "Bearer token"})
        assert gw.authenticate(req_with_auth) is True

    def test_api_report(self):
        """Report generated."""
        gw = APIGateway()
        gw.register_route("/test", "GET", "test_handler")
        req = APIRequest(method="GET", path="/test")
        gw.handle_request(req)
        report = gw.monitor_api()
        assert isinstance(report, dict)
        assert "total_requests" in report
        assert "total_errors" in report
        assert "routes" in report
        assert report["total_requests"] >= 1

    def test_api_versioning(self):
        """Versioning handled."""
        gw = APIGateway()
        version = gw.version_api("v1")
        assert isinstance(version, str)
        assert "v1" in version

    def test_api_documentation(self):
        """Docs generated."""
        gw = APIGateway()
        gw.register_route("/test", "GET", "test_handler")
        docs = gw.generate_api_docs()
        assert isinstance(docs, str)
        assert "/test" in docs
        assert "GET" in docs

    def test_api_monitoring(self):
        """API monitored."""
        gw = APIGateway()
        gw.register_route("/test", "GET", "test_handler")
        req = APIRequest(method="GET", path="/test")
        gw.handle_request(req)
        metrics = gw.monitor_api()
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
        assert "total_errors" in metrics
        assert "routes" in metrics
        assert metrics["total_requests"] >= 1

    def test_api_error_handling(self):
        """Errors handled."""
        gw = APIGateway()
        error = ValueError("test error")
        resp = gw.handle_api_error(error)
        assert isinstance(resp, APIResponse)
        assert resp.status == 500
        assert "error" in resp.body