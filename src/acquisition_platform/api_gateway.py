"""API Gateway module for the acquisition platform.

Provides routing, request handling, rate limiting, authentication,
versioning, documentation generation, monitoring, and error handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class APIRoute:
    """A registered API route.

    Attributes:
        path: URL path pattern (e.g., "/test").
        method: HTTP method (e.g., "GET", "POST").
        handler: Name of the handler function.
        auth_required: Whether authentication is required.
    """

    path: str
    method: str
    handler: str
    auth_required: bool = False


@dataclass
class APIRequest:
    """An incoming API request.

    Attributes:
        method: HTTP method.
        path: URL path.
        headers: Request headers.
        body: Request body.
    """

    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)


@dataclass
class APIResponse:
    """An API response.

    Attributes:
        status: HTTP status code.
        body: Response body.
        headers: Response headers.
    """

    status: int
    body: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


class APIGateway:
    """API Gateway for routing and managing API requests.

    Provides route registration, request handling, rate limiting,
    authentication, versioning, documentation, monitoring, and error handling.
    """

    def __init__(self) -> None:
        self.routes: list[APIRoute] = []
        self._request_counts: dict[str, int] = {}
        self._total_requests: int = 0
        self._total_errors: int = 0

    def register_route(
        self, path: str, method: str, handler: str, auth_required: bool = False
    ) -> APIRoute:
        """Register a new API route.

        Args:
            path: URL path pattern.
            method: HTTP method.
            handler: Handler function name.
            auth_required: Whether authentication is required.

        Returns:
            The registered APIRoute.
        """
        route = APIRoute(path=path, method=method, handler=handler, auth_required=auth_required)
        self.routes.append(route)
        return route

    def handle_request(self, request: APIRequest) -> APIResponse:
        """Handle an incoming API request.

        Args:
            request: The incoming API request.

        Returns:
            APIResponse with appropriate status and body.
        """
        self._total_requests += 1

        # Find matching route
        route = self._find_route(request.method, request.path)
        if route is None:
            self._total_errors += 1
            return APIResponse(status=404)

        # Check authentication
        if route.auth_required and not self.authenticate(request):
            self._total_errors += 1
            return APIResponse(status=401, body={"error": "Unauthorized"})

        return APIResponse(
            status=200,
            body={"message": "OK", "handler": route.handler},
            headers={"Content-Type": "application/json"},
        )

    def rate_limit(self, client_id: str, max_requests: int) -> bool:
        """Check if a client has exceeded their rate limit.

        Args:
            client_id: Unique client identifier.
            max_requests: Maximum allowed requests.

        Returns:
            True if request is allowed, False if rate limited.
        """
        current = self._request_counts.get(client_id, 0)
        if current >= max_requests:
            return False
        self._request_counts[client_id] = current + 1
        return True

    def authenticate(self, request: APIRequest) -> bool:
        """Check if a request is authenticated.

        Args:
            request: The API request to authenticate.

        Returns:
            True if authenticated, False otherwise.
        """
        auth_header = request.headers.get("Authorization", "")
        return auth_header.startswith("Bearer ") and len(auth_header) > 7

    def version_api(self, version: str) -> str:
        """Generate a versioned API prefix.

        Args:
            version: API version string (e.g., "v1").

        Returns:
            Versioned API prefix string.
        """
        return f"/api/{version}"

    def generate_api_docs(self) -> str:
        """Generate API documentation from registered routes.

        Returns:
            Markdown-formatted API documentation.
        """
        lines = ["# API Documentation", ""]
        for route in self.routes:
            auth_str = " (auth required)" if route.auth_required else ""
            lines.append(f"## {route.method} {route.path}{auth_str}")
            lines.append(f"- Handler: `{route.handler}`")
            lines.append("")
        return "\n".join(lines)

    def monitor_api(self) -> dict[str, Any]:
        """Get API monitoring metrics.

        Returns:
            Dict with monitoring metrics.
        """
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "routes": len(self.routes),
            "route_details": [
                {"path": r.path, "method": r.method, "handler": r.handler}
                for r in self.routes
            ],
        }

    def handle_api_error(self, error: Exception) -> APIResponse:
        """Handle an API error and return an appropriate response.

        Args:
            error: The exception that occurred.

        Returns:
            APIResponse with error details.
        """
        self._total_errors += 1
        return APIResponse(
            status=500,
            body={"error": str(error), "type": type(error).__name__},
            headers={"Content-Type": "application/json"},
        )

    def _find_route(self, method: str, path: str) -> APIRoute | None:
        """Find a matching route for the given method and path.

        Args:
            method: HTTP method.
            path: URL path.

        Returns:
            Matching APIRoute or None.
        """
        for route in self.routes:
            if route.method == method and route.path == path:
                return route
        return None
