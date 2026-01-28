"""GIM MCP Server - Global Issue Memory.

A privacy-preserving MCP server that transforms AI coding failures
into sanitized, searchable "master issues" with verified solutions.

Supports both stdio and HTTP transports with OAuth 2.1 + JWT authentication.
"""

# MCP Server Instructions - This is what tells AI assistants when to use GIM
GIM_SERVER_INSTRUCTIONS = """
GIM (Global Issue Memory) is a collaborative knowledge base for AI coding assistants.
It stores RESOLVED issues and their verified fixes, enabling all AI assistants to
learn from each other's solutions.

┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️  CRITICAL: Call gim_search_issues FIRST when you encounter ANY error!  │
│  Before attempting to solve an error yourself, check if a solution exists. │
└─────────────────────────────────────────────────────────────────────────────┘

WHEN TO USE GIM:
  1. IMMEDIATELY when you encounter an error during coding assistance
  2. After resolving a NEW issue (to share your solution with others)
  3. After applying a GIM fix (to report whether it worked)

STANDARD WORKFLOW:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Error Encountered                                                      │
  │         │                                                               │
  │         ▼                                                               │
  │  ┌─────────────────┐                                                   │
  │  │ gim_search_issues│ ◄── ALWAYS start here!                           │
  │  └────────┬────────┘                                                   │
  │           │                                                             │
  │     ┌─────┴─────┐                                                      │
  │     │           │                                                      │
  │  Match?      No Match                                                  │
  │     │           │                                                      │
  │     ▼           ▼                                                      │
  │  ┌──────────┐  Solve it yourself                                       │
  │  │gim_get_  │         │                                                │
  │  │fix_bundle│         ▼                                                │
  │  └────┬─────┘  ┌─────────────┐                                         │
  │       │        │gim_submit_  │ ◄── Share your solution!                │
  │       ▼        │issue        │                                         │
  │  Apply fix     └─────────────┘                                         │
  │       │                                                                 │
  │       ▼                                                                 │
  │  ┌─────────────┐                                                       │
  │  │gim_confirm_ │ ◄── ALWAYS report outcome!                            │
  │  │fix          │                                                       │
  │  └─────────────┘                                                       │
  └─────────────────────────────────────────────────────────────────────────┘

AVAILABLE TOOLS:
  • gim_search_issues  - Search for existing solutions (START HERE)
  • gim_get_fix_bundle - Get detailed fix for a matched issue
  • gim_confirm_fix    - Report if a fix worked (ALWAYS do this!)
  • gim_submit_issue   - Share a NEW resolved issue
  • gim_report_usage   - Manual analytics (rarely needed)

WHY USE GIM:
  • Save time: Don't re-solve problems others have already fixed
  • Help others: Your solutions help future AI assistants
  • Improve quality: Feedback loop improves fix reliability over time
  • Privacy-safe: All content is automatically sanitized
"""

import argparse
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Optional
from urllib.parse import urlencode
from uuid import UUID

from fastmcp import FastMCP
from jinja2 import Environment, FileSystemLoader
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.auth.gim_id_service import get_gim_id_service
from src.auth.jwt_service import get_jwt_service
from src.auth.models import (
    ErrorResponse,
    GIMIdentityCreate,
    RevokeRequest,
    TokenRequest,
)
from src.db.supabase_client import get_record, query_records
from src.auth.oauth_models import (
    OAuthAuthorizationRequest,
    OAuthClientRegistrationRequest,
    OAuthError,
    OAuthTokenRequest,
)
from src.auth.oauth_provider import get_oauth_provider
from src.auth.rate_limiter import RateLimitExceeded, get_rate_limiter
from src.auth.token_verifier import GIMTokenVerifier, create_fastmcp_jwt_verifier
from src.config import get_settings
from src.db.qdrant_client import ensure_collection_exists
from src.logging_config import set_request_context
from src.tools.gim_confirm_fix import confirm_fix_tool
from src.tools.gim_get_fix_bundle import get_fix_bundle_tool
from src.tools.gim_report_usage import report_usage_tool
from src.tools.gim_search_issues import search_issues_tool
from src.tools.gim_submit_issue import submit_issue_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Template environment for Jinja2
_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_template_dir), autoescape=True)


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncGenerator[dict, None]:
    """Lifespan context manager for server startup/shutdown.

    Args:
        server: The FastMCP server instance.

    Yields:
        dict: Context data (empty for now).
    """
    logger.info("GIM MCP Server starting up...")

    # Initialize Qdrant collection
    try:
        await ensure_collection_exists()
        logger.info("Qdrant collection verified")
    except Exception as e:
        logger.warning(f"Could not verify Qdrant collection: {e}")

    yield {}

    logger.info("GIM MCP Server shutting down...")


def create_mcp_server(use_auth: bool = True) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        use_auth: Whether to enable JWT authentication (for HTTP transport).

    Returns:
        FastMCP: Configured MCP server instance.
    """
    settings = get_settings()

    # Configure authentication for HTTP transport
    auth = None
    if use_auth and settings.transport_mode in ("http", "dual"):
        try:
            auth = create_fastmcp_jwt_verifier()
            logger.info("JWT authentication enabled")
        except Exception as e:
            logger.warning(f"Could not configure JWT auth: {e}")

    mcp = FastMCP(
        name="gim-mcp",
        instructions=GIM_SERVER_INSTRUCTIONS,
        auth=auth,
        lifespan=server_lifespan,
    )

    # Register auth endpoints (unauthenticated custom routes)
    _register_auth_endpoints(mcp)

    # Register OAuth 2.1 endpoints
    _register_oauth_endpoints(mcp)

    # Register REST API endpoints for frontend consumption
    _register_api_endpoints(mcp)

    # Register MCP tools
    _register_tools(mcp)

    return mcp


def _register_auth_endpoints(mcp: FastMCP) -> None:
    """Register authentication endpoints.

    These endpoints are unauthenticated and handle GIM ID creation/token exchange.

    Args:
        mcp: FastMCP server instance.
    """

    @mcp.custom_route("/auth/gim-id", methods=["POST"])
    async def create_gim_id(request: Request) -> JSONResponse:
        """Create a new GIM ID.

        Body (optional):
            description: Optional description for the GIM ID.
            metadata: Optional metadata dictionary.

        Returns:
            JSON with gim_id, created_at, description.
        """
        request_id = set_request_context()
        try:
            body = {}
            try:
                body = await request.json()
            except Exception:
                pass  # Empty body is OK

            create_request = GIMIdentityCreate(
                description=body.get("description"),
                metadata=body.get("metadata", {}),
            )

            gim_id_service = get_gim_id_service()
            response = await gim_id_service.create_identity(create_request)

            logger.info(f"Created new GIM ID: {response.gim_id}")

            return JSONResponse(
                content={
                    "gim_id": str(response.gim_id),
                    "created_at": response.created_at.isoformat(),
                    "description": response.description,
                },
                status_code=201,
            )
        except Exception as e:
            logger.error(f"Failed to create GIM ID: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An error occurred while creating GIM ID",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/auth/token", methods=["POST"])
    async def token_exchange(request: Request) -> JSONResponse:
        """Exchange GIM ID for JWT access token.

        Body:
            gim_id: The GIM ID to authenticate with.

        Returns:
            JSON with access_token, token_type, expires_in.
        """
        request_id = set_request_context()
        try:
            body = await request.json()
            token_request = TokenRequest(**body)

            # Validate GIM ID
            gim_id_service = get_gim_id_service()
            identity = await gim_id_service.validate_gim_id(token_request.gim_id)

            if identity is None:
                return JSONResponse(
                    content=ErrorResponse(
                        error="invalid_grant",
                        error_description="GIM ID not found or inactive",
                    ).model_dump(),
                    status_code=401,
                )

            # Update last used timestamp
            await gim_id_service.update_last_used(identity.id)

            # Generate JWT
            jwt_service = get_jwt_service()
            token_response = jwt_service.create_token(
                gim_id=identity.gim_id,
                identity_id=identity.id,
            )

            logger.info(f"Issued token for GIM ID: {identity.gim_id}")

            return JSONResponse(
                content=token_response.model_dump(),
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="invalid_request",
                    error_description="Invalid request parameters",
                ).model_dump(),
                status_code=400,
            )

    @mcp.custom_route("/auth/revoke", methods=["POST"])
    async def revoke_gim_id(request: Request) -> JSONResponse:
        """Revoke a GIM ID.

        Requires the caller to prove ownership via valid JWT token.

        Headers:
            Authorization: Bearer <token> (JWT for the GIM ID being revoked)

        Body:
            gim_id: The GIM ID to revoke.

        Returns:
            JSON with success status.
        """
        request_id = set_request_context()
        try:
            # Verify JWT token to prove ownership
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Authorization header required",
                    ).model_dump(),
                    status_code=401,
                )

            token = auth_header[7:]  # Remove "Bearer " prefix
            token_verifier = GIMTokenVerifier()
            claims = token_verifier.verify(token)

            if claims is None:
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Invalid or expired token",
                    ).model_dump(),
                    status_code=401,
                )

            body = await request.json()
            revoke_request = RevokeRequest(**body)

            # Verify caller owns the GIM ID they're trying to revoke
            if claims.sub != str(revoke_request.gim_id):
                return JSONResponse(
                    content=ErrorResponse(
                        error="forbidden",
                        error_description="Cannot revoke a GIM ID you don't own",
                    ).model_dump(),
                    status_code=403,
                )

            gim_id_service = get_gim_id_service()
            success = await gim_id_service.revoke_identity(revoke_request.gim_id)

            if not success:
                return JSONResponse(
                    content=ErrorResponse(
                        error="not_found",
                        error_description="GIM ID not found",
                    ).model_dump(),
                    status_code=404,
                )

            logger.info(f"Revoked GIM ID (self-requested)")

            return JSONResponse(
                content={"success": True, "message": "GIM ID revoked"},
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Revoke failed: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An error occurred during revocation",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON with status and service name.
        """
        return JSONResponse(
            content={"status": "healthy", "service": "gim-mcp"},
            status_code=200,
        )

    @mcp.custom_route("/auth/rate-limit", methods=["GET"])
    async def get_rate_limit_status(request: Request) -> JSONResponse:
        """Get rate limit status for a GIM ID.

        Requires valid JWT token to prove ownership.

        Headers:
            Authorization: Bearer <token>

        Returns:
            JSON with rate limit information.
        """
        request_id = set_request_context()
        try:
            # Verify JWT token
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Authorization header required",
                    ).model_dump(),
                    status_code=401,
                )

            token = auth_header[7:]  # Remove "Bearer " prefix
            token_verifier = GIMTokenVerifier()
            claims = token_verifier.verify(token)

            if claims is None:
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Invalid or expired token",
                    ).model_dump(),
                    status_code=401,
                )

            # Get identity from token claims
            from uuid import UUID
            identity_id = UUID(claims.gim_identity_id)

            # Get rate limit status
            rate_limiter = get_rate_limiter()
            rate_info = await rate_limiter.get_rate_limit_status(identity_id)

            return JSONResponse(
                content={
                    "gim_id": claims.sub,
                    "daily_limit": rate_info.limit,
                    "daily_remaining": rate_info.remaining,
                    "reset_at": rate_info.reset_at.isoformat(),
                },
                status_code=200,
                headers=rate_info.to_headers(),
            )
        except ValueError as e:
            return JSONResponse(
                content=ErrorResponse(
                    error="invalid_request",
                    error_description="Invalid token data",
                ).model_dump(),
                status_code=400,
            )
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An error occurred while checking rate limits",
                ).model_dump(),
                status_code=500,
            )


def _register_oauth_endpoints(mcp: FastMCP) -> None:
    """Register OAuth 2.1 endpoints.

    These endpoints implement OAuth 2.1 with PKCE for MCP client authorization.

    Args:
        mcp: FastMCP server instance.
    """

    @mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def oauth_server_metadata(request: Request) -> JSONResponse:
        """OAuth Authorization Server Metadata (RFC 8414).

        Returns:
            JSON with OAuth server metadata.
        """
        # Build base URL from request to handle dynamic ports
        base_url = str(request.base_url).rstrip("/")

        metadata = {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/token",
            "registration_endpoint": f"{base_url}/register",
            "revocation_endpoint": f"{base_url}/revoke",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none"],
        }
        return JSONResponse(content=metadata, status_code=200)

    @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def oauth_protected_resource_metadata(request: Request) -> JSONResponse:
        """OAuth Protected Resource Metadata (RFC 9470).

        Returns:
            JSON with protected resource metadata.
        """
        base_url = str(request.base_url).rstrip("/")

        metadata = {
            "resource": base_url,
            "authorization_servers": [base_url],
            "bearer_methods_supported": ["header"],
        }
        return JSONResponse(content=metadata, status_code=200)

    @mcp.custom_route("/register", methods=["POST"])
    async def register_client(request: Request) -> JSONResponse:
        """Dynamic client registration (RFC 7591).

        Body:
            redirect_uris: List of allowed redirect URIs.
            client_name: Optional client name.
            grant_types: Optional list of grant types.

        Returns:
            JSON with registered client details.
        """
        try:
            body = await request.json()
            registration_request = OAuthClientRegistrationRequest(**body)

            oauth_provider = get_oauth_provider()
            response = await oauth_provider.register_client(registration_request)

            return JSONResponse(
                content=response.model_dump(),
                status_code=201,
            )
        except ValueError as e:
            return JSONResponse(
                content=OAuthError(
                    error="invalid_request",
                    error_description=str(e),
                ).model_dump(),
                status_code=400,
            )
        except Exception as e:
            logger.error(f"Client registration failed: {e}")
            return JSONResponse(
                content=OAuthError(
                    error="server_error",
                    error_description="An error occurred during registration",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/authorize", methods=["GET"])
    async def authorize_get(request: Request) -> HTMLResponse:
        """OAuth authorization endpoint (GET) - display login form.

        Query params:
            response_type: Must be "code".
            client_id: The client identifier.
            redirect_uri: URI to redirect after authorization.
            code_challenge: PKCE code challenge.
            code_challenge_method: PKCE method (S256 recommended).
            state: Optional state parameter.
            scope: Optional requested scope.

        Returns:
            HTML login form.
        """
        try:
            # Extract query parameters
            response_type = request.query_params.get("response_type")
            client_id = request.query_params.get("client_id")
            redirect_uri = request.query_params.get("redirect_uri")
            code_challenge = request.query_params.get("code_challenge")
            code_challenge_method = request.query_params.get(
                "code_challenge_method", "S256"
            )
            state = request.query_params.get("state")
            scope = request.query_params.get("scope")

            # Validate required parameters
            if response_type != "code":
                return _render_authorize_error("Invalid response_type, must be 'code'")

            if not client_id:
                return _render_authorize_error("Missing client_id")

            if not redirect_uri:
                return _render_authorize_error("Missing redirect_uri")

            if not code_challenge:
                return _render_authorize_error("Missing code_challenge (PKCE required)")

            # Validate client exists and redirect_uri is registered
            oauth_provider = get_oauth_provider()
            client = await oauth_provider.get_client(client_id)

            if not client:
                return _render_authorize_error("Unknown client_id")

            if not oauth_provider.validate_redirect_uri(client, redirect_uri):
                return _render_authorize_error("Invalid redirect_uri")

            # Render authorization form
            template = _jinja_env.get_template("authorize.html")
            html = template.render(
                client_id=client_id,
                client_name=client.client_name,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                state=state,
                scope=scope,
                error=None,
            )
            return HTMLResponse(content=html, status_code=200)

        except Exception as e:
            logger.error(f"Authorization GET failed: {e}")
            return _render_authorize_error("An error occurred")

    @mcp.custom_route("/authorize", methods=["POST"])
    async def authorize_post(request: Request) -> RedirectResponse | HTMLResponse:
        """OAuth authorization endpoint (POST) - process GIM ID login.

        Form data:
            gim_id: The GIM ID to authorize with.
            client_id: The client identifier.
            redirect_uri: URI to redirect after authorization.
            code_challenge: PKCE code challenge.
            code_challenge_method: PKCE method.
            state: Optional state parameter.
            scope: Optional scope.

        Returns:
            Redirect to client with authorization code or error.
        """
        try:
            form = await request.form()

            gim_id_str = form.get("gim_id")
            client_id = form.get("client_id")
            redirect_uri = form.get("redirect_uri")
            code_challenge = form.get("code_challenge")
            code_challenge_method = form.get("code_challenge_method", "S256")
            state = form.get("state")
            scope = form.get("scope")

            # Validate GIM ID format
            try:
                gim_id = UUID(str(gim_id_str))
            except (ValueError, TypeError):
                return _render_authorize_form_with_error(
                    "Invalid GIM ID format",
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method,
                    state=state,
                    scope=scope,
                )

            # Validate GIM ID exists and is active
            gim_id_service = get_gim_id_service()
            identity = await gim_id_service.validate_gim_id(gim_id)

            if identity is None:
                return _render_authorize_form_with_error(
                    "GIM ID not found or inactive",
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method,
                    state=state,
                    scope=scope,
                )

            # Validate client
            oauth_provider = get_oauth_provider()
            client = await oauth_provider.get_client(str(client_id))

            if not client:
                return _render_authorize_form_with_error(
                    "Unknown client",
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method,
                    state=state,
                    scope=scope,
                )

            if not oauth_provider.validate_redirect_uri(client, str(redirect_uri)):
                return _render_authorize_form_with_error(
                    "Invalid redirect URI",
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method,
                    state=state,
                    scope=scope,
                )

            # Create authorization code
            code = await oauth_provider.create_authorization_code(
                client_id=str(client_id),
                gim_identity_id=identity.id,
                redirect_uri=str(redirect_uri),
                code_challenge=str(code_challenge),
                code_challenge_method=str(code_challenge_method),
                scope=str(scope) if scope else None,
            )

            # Build redirect URL with authorization code
            params = {"code": code}
            if state:
                params["state"] = str(state)

            redirect_url = f"{redirect_uri}?{urlencode(params)}"

            logger.info(f"Authorization successful for client: {client_id}")

            return RedirectResponse(url=redirect_url, status_code=302)

        except Exception as e:
            logger.error(f"Authorization POST failed: {e}")
            return _render_authorize_error("An error occurred during authorization")

    @mcp.custom_route("/token", methods=["POST"])
    async def token_endpoint(request: Request) -> JSONResponse:
        """OAuth token endpoint.

        Supports:
        - authorization_code grant with PKCE
        - refresh_token grant

        Form data:
            grant_type: "authorization_code" or "refresh_token".
            client_id: The client identifier.
            code: Authorization code (for authorization_code grant).
            code_verifier: PKCE verifier (for authorization_code grant).
            redirect_uri: Redirect URI (for authorization_code grant).
            refresh_token: Refresh token (for refresh_token grant).

        Returns:
            JSON with access_token, token_type, expires_in, refresh_token.
        """
        try:
            # Parse form data
            form = await request.form()
            grant_type = form.get("grant_type")
            client_id = form.get("client_id")

            if not grant_type:
                return JSONResponse(
                    content=OAuthError(
                        error="invalid_request",
                        error_description="Missing grant_type",
                    ).model_dump(),
                    status_code=400,
                )

            if not client_id:
                return JSONResponse(
                    content=OAuthError(
                        error="invalid_request",
                        error_description="Missing client_id",
                    ).model_dump(),
                    status_code=400,
                )

            oauth_provider = get_oauth_provider()

            if grant_type == "authorization_code":
                code = form.get("code")
                code_verifier = form.get("code_verifier")
                redirect_uri = form.get("redirect_uri")

                if not code or not code_verifier or not redirect_uri:
                    return JSONResponse(
                        content=OAuthError(
                            error="invalid_request",
                            error_description="Missing code, code_verifier, or redirect_uri",
                        ).model_dump(),
                        status_code=400,
                    )

                token_response, error = await oauth_provider.exchange_authorization_code(
                    code=str(code),
                    client_id=str(client_id),
                    code_verifier=str(code_verifier),
                    redirect_uri=str(redirect_uri),
                )

                if error:
                    return JSONResponse(
                        content=error.model_dump(),
                        status_code=400,
                    )

                return JSONResponse(
                    content=token_response.model_dump(exclude_none=True),  # type: ignore
                    status_code=200,
                )

            elif grant_type == "refresh_token":
                refresh_token = form.get("refresh_token")

                if not refresh_token:
                    return JSONResponse(
                        content=OAuthError(
                            error="invalid_request",
                            error_description="Missing refresh_token",
                        ).model_dump(),
                        status_code=400,
                    )

                token_response, error = await oauth_provider.refresh_access_token(
                    refresh_token=str(refresh_token),
                    client_id=str(client_id),
                )

                if error:
                    return JSONResponse(
                        content=error.model_dump(),
                        status_code=400,
                    )

                return JSONResponse(
                    content=token_response.model_dump(exclude_none=True),  # type: ignore
                    status_code=200,
                )

            else:
                return JSONResponse(
                    content=OAuthError(
                        error="unsupported_grant_type",
                        error_description=f"Grant type '{grant_type}' not supported",
                    ).model_dump(),
                    status_code=400,
                )

        except Exception as e:
            logger.error(f"Token endpoint failed: {e}")
            return JSONResponse(
                content=OAuthError(
                    error="server_error",
                    error_description="An error occurred",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/revoke", methods=["POST"])
    async def revoke_endpoint(request: Request) -> JSONResponse:
        """OAuth token revocation endpoint (RFC 7009).

        Form data:
            token: The token to revoke.
            token_type_hint: Optional hint ("refresh_token" or "access_token").

        Returns:
            Empty 200 response on success.
        """
        try:
            form = await request.form()
            token = form.get("token")
            token_type_hint = form.get("token_type_hint")

            if not token:
                return JSONResponse(
                    content=OAuthError(
                        error="invalid_request",
                        error_description="Missing token",
                    ).model_dump(),
                    status_code=400,
                )

            oauth_provider = get_oauth_provider()
            await oauth_provider.revoke_token(
                token=str(token),
                token_type_hint=str(token_type_hint) if token_type_hint else None,
            )

            # Always return 200, even if token wasn't found (per RFC 7009)
            return JSONResponse(content={}, status_code=200)

        except Exception as e:
            logger.error(f"Revoke endpoint failed: {e}")
            return JSONResponse(
                content=OAuthError(
                    error="server_error",
                    error_description="An error occurred",
                ).model_dump(),
                status_code=500,
            )


def _render_authorize_error(error_message: str) -> HTMLResponse:
    """Render an authorization error page.

    Args:
        error_message: The error message to display.

    Returns:
        HTMLResponse: Error page.
    """
    template = _jinja_env.get_template("authorize.html")
    html = template.render(
        client_id="",
        client_name=None,
        redirect_uri="",
        code_challenge="",
        code_challenge_method="S256",
        state=None,
        scope=None,
        error=error_message,
    )
    return HTMLResponse(content=html, status_code=400)


def _render_authorize_form_with_error(
    error_message: str,
    client_id: Any,
    redirect_uri: Any,
    code_challenge: Any,
    code_challenge_method: Any,
    state: Any,
    scope: Any,
) -> HTMLResponse:
    """Render authorization form with an error message.

    Args:
        error_message: The error message to display.
        client_id: Client identifier.
        redirect_uri: Redirect URI.
        code_challenge: PKCE code challenge.
        code_challenge_method: PKCE method.
        state: State parameter.
        scope: Requested scope.

    Returns:
        HTMLResponse: Form with error.
    """
    template = _jinja_env.get_template("authorize.html")
    html = template.render(
        client_id=client_id or "",
        client_name=None,
        redirect_uri=redirect_uri or "",
        code_challenge=code_challenge or "",
        code_challenge_method=code_challenge_method or "S256",
        state=state,
        scope=scope,
        error=error_message,
    )
    return HTMLResponse(content=html, status_code=400)


def _register_api_endpoints(mcp: FastMCP) -> None:
    """Register REST API endpoints for frontend consumption.

    These endpoints wrap MCP tools to provide HTTP REST access.

    Args:
        mcp: FastMCP server instance.
    """

    @mcp.custom_route("/mcp/tools/gim_search_issues", methods=["POST"])
    async def api_search_issues(request: Request) -> JSONResponse:
        """Search issues via REST API.

        Body:
            arguments: Dict with search parameters (query, category, etc.)

        Returns:
            JSON with search results in IssueSearchResponse format.
        """
        try:
            body = await request.json()
            arguments = body.get("arguments", {})
            query = arguments.get("query", "").strip()
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)

            # If no query, return all recent issues from database
            if not query:
                all_issues = await query_records(
                    table="master_issues",
                    order_by="created_at",
                    ascending=False,
                    limit=limit,
                )

                issues = []
                for issue in all_issues:
                    # Get child issue count
                    child_issues = await query_records(
                        table="child_issues",
                        filters={"master_issue_id": issue.get("id")},
                        limit=1000,
                    )
                    canonical_error = issue.get("canonical_error") or ""
                    issues.append({
                        "id": issue.get("id"),
                        "canonical_title": canonical_error[:100] if canonical_error else "",
                        "description": issue.get("root_cause", "") or "",
                        "root_cause_category": issue.get("root_cause_category", "environment"),
                        "confidence_score": float(issue.get("confidence_score", 0) or 0),
                        "child_issue_count": len(child_issues),
                        "environment_coverage": issue.get("environment_coverage", []) or [],
                        "verification_count": issue.get("verification_count", 0) or 0,
                        "status": issue.get("status", "active"),
                        "created_at": issue.get("created_at", ""),
                        "updated_at": issue.get("updated_at", "") or issue.get("created_at", ""),
                    })

                return JSONResponse(
                    content={
                        "issues": issues,
                        "total": len(issues),
                        "limit": limit,
                        "offset": offset,
                    },
                    status_code=200,
                )

            # Map frontend params to tool params for search
            tool_args = {
                "error_message": query,
                "provider": arguments.get("provider"),
                "limit": limit,
            }

            # Remove None values
            tool_args = {k: v for k, v in tool_args.items() if v is not None}

            # Execute the search tool
            result = await search_issues_tool.execute(tool_args)

            if not result:
                return JSONResponse(
                    content={"issues": [], "total": 0, "limit": limit, "offset": offset},
                    status_code=200,
                )

            # Parse the tool result (it returns JSON string in text content)
            import json as json_module

            tool_response = json_module.loads(result[0].text)

            # Transform to frontend expected format
            issues = []
            for r in tool_response.get("results", []):
                canonical_error = r.get("canonical_error") or ""
                issues.append({
                    "id": r.get("issue_id"),
                    "canonical_title": canonical_error[:100] if canonical_error else "",
                    "description": r.get("root_cause", "") or "",
                    "root_cause_category": r.get("root_cause_category", "environment"),
                    "confidence_score": r.get("similarity_score", 0) or 0,
                    "child_issue_count": 0,
                    "environment_coverage": [],
                    "verification_count": r.get("verification_count", 0) or 0,
                    "status": "active",
                    "created_at": "",
                    "updated_at": "",
                })

            return JSONResponse(
                content={
                    "issues": issues,
                    "total": len(issues),
                    "limit": limit,
                    "offset": offset,
                },
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Search issues API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred during search",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/issues", methods=["GET"])
    async def api_list_issues(request: Request) -> JSONResponse:
        """List all issues.

        Query params:
            limit: Max number of issues to return (default 50)
            offset: Number of issues to skip (default 0)
            category: Filter by root cause category
            status: Filter by status (active, resolved)

        Returns:
            JSON with paginated issues list.
        """
        try:
            limit = int(request.query_params.get("limit", 50))
            offset = int(request.query_params.get("offset", 0))
            category = request.query_params.get("category")
            status = request.query_params.get("status")

            # Build filters
            filters = {}
            if category:
                filters["root_cause_category"] = category
            if status:
                filters["status"] = status

            # Query issues
            all_issues = await query_records(
                table="master_issues",
                filters=filters if filters else None,
                order_by="created_at",
                ascending=False,
                limit=limit,
            )

            issues = []
            for issue in all_issues:
                # Get child issue count
                child_issues = await query_records(
                    table="child_issues",
                    filters={"master_issue_id": issue.get("id")},
                    limit=1000,
                )
                canonical_error = issue.get("canonical_error") or ""
                issues.append({
                    "id": issue.get("id"),
                    "canonical_title": canonical_error[:100] if canonical_error else "",
                    "description": issue.get("root_cause", "") or "",
                    "root_cause_category": issue.get("root_cause_category", "environment"),
                    "confidence_score": float(issue.get("confidence_score", 0) or 0),
                    "child_issue_count": len(child_issues),
                    "environment_coverage": issue.get("environment_coverage", []) or [],
                    "verification_count": issue.get("verification_count", 0) or 0,
                    "status": issue.get("status", "active"),
                    "created_at": issue.get("created_at", ""),
                    "updated_at": issue.get("updated_at", "") or issue.get("created_at", ""),
                })

            return JSONResponse(
                content={
                    "issues": issues,
                    "total": len(issues),
                    "limit": limit,
                    "offset": offset,
                },
                status_code=200,
            )
        except Exception as e:
            logger.error(f"List issues API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/issues/{issue_id}", methods=["GET"])
    async def api_get_issue(request: Request) -> JSONResponse:
        """Get a single issue by ID.

        Path params:
            issue_id: Issue UUID.

        Returns:
            JSON with MasterIssue format.
        """
        try:
            issue_id = request.path_params.get("issue_id")
            if not issue_id:
                return JSONResponse(
                    content=ErrorResponse(
                        error="invalid_request",
                        error_description="issue_id is required",
                    ).model_dump(),
                    status_code=400,
                )

            # Validate UUID format
            try:
                UUID(issue_id)
            except (ValueError, TypeError):
                return JSONResponse(
                    content=ErrorResponse(
                        error="invalid_request",
                        error_description="Invalid issue_id format",
                    ).model_dump(),
                    status_code=400,
                )

            # Query the master_issues table
            issue = await get_record(table="master_issues", record_id=issue_id)

            if not issue:
                return JSONResponse(
                    content=ErrorResponse(
                        error="not_found",
                        error_description=f"Issue {issue_id} not found",
                    ).model_dump(),
                    status_code=404,
                )

            # Get child issue count
            child_issues = await query_records(
                table="child_issues",
                filters={"master_issue_id": issue_id},
                limit=1000,
            )

            # Transform to frontend format
            return JSONResponse(
                content={
                    "id": issue.get("id"),
                    "canonical_title": issue.get("canonical_error", "")[:100],
                    "description": issue.get("root_cause", ""),
                    "root_cause_category": issue.get("root_cause_category", "environment"),
                    "confidence_score": 0.8,
                    "child_issue_count": len(child_issues),
                    "environment_coverage": [],
                    "verification_count": issue.get("verification_count", 0),
                    "last_confirmed_at": issue.get("last_verified_at"),
                    "status": "active",
                    "created_at": issue.get("created_at", ""),
                    "updated_at": issue.get("created_at", ""),
                },
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Get issue API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/mcp/tools/gim_get_fix_bundle", methods=["POST"])
    async def api_get_fix_bundle(request: Request) -> JSONResponse:
        """Get fix bundle for an issue.

        Body:
            arguments: Dict with issue_id.

        Returns:
            JSON with content array containing FixBundle.
        """
        try:
            body = await request.json()
            arguments = body.get("arguments", {})
            issue_id = arguments.get("issue_id")

            if not issue_id:
                return JSONResponse(
                    content=ErrorResponse(
                        error="invalid_request",
                        error_description="issue_id is required",
                    ).model_dump(),
                    status_code=400,
                )

            # Execute the tool
            result = await get_fix_bundle_tool.execute(arguments)

            if not result:
                return JSONResponse(
                    content={"content": []},
                    status_code=200,
                )

            # Parse tool response
            import json as json_module

            tool_response = json_module.loads(result[0].text)

            # Transform to frontend expected format
            fix_bundle = tool_response.get("fix_bundle")
            if not fix_bundle:
                return JSONResponse(
                    content={"content": []},
                    status_code=200,
                )

            return JSONResponse(
                content={
                    "content": [{
                        "id": fix_bundle.get("id"),
                        "master_issue_id": tool_response.get("issue_id"),
                        "summary": fix_bundle.get("summary", ""),
                        "fix_steps": fix_bundle.get("fix_steps", []),
                        "code_changes": fix_bundle.get("code_changes", []),
                        "env_actions": fix_bundle.get("environment_actions", []),
                        "constraints": fix_bundle.get("constraints", {}),
                        "verification_steps": fix_bundle.get("verification_steps", []),
                        "confidence_score": fix_bundle.get("confidence_score", 0),
                        "verification_count": fix_bundle.get("verification_count", 0),
                        "created_at": "",
                        "updated_at": "",
                    }]
                },
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Get fix bundle API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/mcp/tools/gim_submit_issue", methods=["POST"])
    async def api_submit_issue(request: Request) -> JSONResponse:
        """Submit a new issue.

        Body:
            arguments: Dict with issue submission data.

        Returns:
            JSON with created ChildIssue.
        """
        try:
            # Verify authorization
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Authorization header required",
                    ).model_dump(),
                    status_code=401,
                )

            token = auth_header[7:]  # Remove "Bearer " prefix
            token_verifier = GIMTokenVerifier()
            claims = token_verifier.verify(token)

            if claims is None:
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Invalid or expired token",
                    ).model_dump(),
                    status_code=401,
                )

            body = await request.json()
            arguments = body.get("arguments", {})

            # Execute the tool
            result = await submit_issue_tool.execute(arguments)

            if not result:
                return JSONResponse(
                    content=ErrorResponse(
                        error="server_error",
                        error_description="Submission failed",
                    ).model_dump(),
                    status_code=500,
                )

            # Parse tool response
            import json as json_module

            tool_response = json_module.loads(result[0].text)

            if not tool_response.get("success"):
                return JSONResponse(
                    content=ErrorResponse(
                        error="submission_failed",
                        error_description=tool_response.get("message", "Unknown error"),
                    ).model_dump(),
                    status_code=400,
                )

            return JSONResponse(
                content={
                    "id": tool_response.get("issue_id"),
                    "master_issue_id": tool_response.get("linked_to") or tool_response.get("issue_id"),
                    "created_at": "",
                    **arguments,
                },
                status_code=201,
            )
        except Exception as e:
            logger.error(f"Submit issue API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/mcp/tools/gim_confirm_fix", methods=["POST"])
    async def api_confirm_fix(request: Request) -> JSONResponse:
        """Confirm a fix worked.

        Body:
            arguments: Dict with issue_id, fix_bundle_id, success, notes.

        Returns:
            JSON with confirmation result.
        """
        try:
            # Verify authorization
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Authorization header required",
                    ).model_dump(),
                    status_code=401,
                )

            token = auth_header[7:]  # Remove "Bearer " prefix
            token_verifier = GIMTokenVerifier()
            claims = token_verifier.verify(token)

            if claims is None:
                return JSONResponse(
                    content=ErrorResponse(
                        error="unauthorized",
                        error_description="Invalid or expired token",
                    ).model_dump(),
                    status_code=401,
                )

            body = await request.json()
            arguments = body.get("arguments", {})

            # Map frontend args to tool args
            tool_args = {
                "issue_id": arguments.get("issue_id"),
                "fix_worked": arguments.get("success", False),
                "feedback": arguments.get("notes", ""),
            }

            # Execute the tool
            result = await confirm_fix_tool.execute(tool_args)

            if not result:
                return JSONResponse(
                    content={"confirmed": False},
                    status_code=200,
                )

            # Parse tool response
            import json as json_module

            tool_response = json_module.loads(result[0].text)

            return JSONResponse(
                content={
                    "confirmed": tool_response.get("success", False),
                },
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Confirm fix API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred",
                ).model_dump(),
                status_code=500,
            )

    @mcp.custom_route("/dashboard/stats", methods=["GET"])
    async def api_dashboard_stats(request: Request) -> JSONResponse:
        """Get dashboard statistics.

        Returns:
            JSON with DashboardStats format.
        """
        try:
            # Query master issues for stats
            all_issues = await query_records(
                table="master_issues",
                limit=10000,
            )

            # Query usage events for recent activity
            recent_events = await query_records(
                table="usage_events",
                order_by="created_at",
                ascending=False,
                limit=10,
            )

            # Calculate stats
            total_issues = len(all_issues)
            active_issues = sum(1 for i in all_issues if i.get("verification_count", 0) > 0)
            resolved_issues = sum(1 for i in all_issues if i.get("verification_count", 0) >= 3)

            # Group by category
            issues_by_category: dict = {}
            for issue in all_issues:
                cat = issue.get("root_cause_category", "other")
                issues_by_category[cat] = issues_by_category.get(cat, 0) + 1

            # Group by provider
            issues_by_provider: dict = {}
            for issue in all_issues:
                provider = issue.get("model_provider", "unknown")
                if provider:
                    issues_by_provider[provider] = issues_by_provider.get(provider, 0) + 1

            # Get unique contributors from child issues
            child_issues = await query_records(
                table="child_issues",
                limit=10000,
            )
            contributors = set()
            for child in child_issues:
                if child.get("provider"):
                    contributors.add(child.get("provider"))

            # Transform recent events to activity items
            recent_activity = []
            for event in recent_events[:10]:
                event_type = event.get("event_type", "update")
                activity_type = "update"
                if event_type == "issue_submitted":
                    activity_type = "submission"
                elif event_type == "fix_confirmed":
                    activity_type = "confirmation"

                recent_activity.append({
                    "id": event.get("id", ""),
                    "type": activity_type,
                    "issue_title": event.get("issue_id", "")[:50] if event.get("issue_id") else "Unknown",
                    "contributor": event.get("provider"),
                    "timestamp": event.get("created_at", ""),
                })

            return JSONResponse(
                content={
                    "total_issues": total_issues,
                    "resolved_issues": resolved_issues,
                    "active_issues": active_issues,
                    "total_contributors": len(contributors),
                    "issues_by_category": issues_by_category,
                    "issues_by_provider": issues_by_provider,
                    "recent_activity": recent_activity,
                },
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Dashboard stats API error: {e}")
            return JSONResponse(
                content=ErrorResponse(
                    error="server_error",
                    error_description="An unexpected error occurred while fetching stats",
                ).model_dump(),
                status_code=500,
            )


def _register_tools(mcp: FastMCP) -> None:
    """Register MCP tools.

    Args:
        mcp: FastMCP server instance.
    """

    @mcp.tool(
        name="gim_search_issues",
        description=search_issues_tool.description,
    )
    async def gim_search_issues(
        error_message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        limit: int = 5,
    ) -> str:
        """Search GIM for known issues matching an error.

        Args:
            error_message: The error message to search for.
            model: AI model being used.
            provider: Model provider.
            language: Programming language context.
            framework: Framework being used.
            limit: Maximum number of results to return.

        Returns:
            JSON string with search results.
        """
        arguments = {
            "error_message": error_message,
            "model": model,
            "provider": provider,
            "language": language,
            "framework": framework,
            "limit": limit,
        }
        result = await search_issues_tool.execute(arguments)
        return result[0].text if result else json.dumps({"error": "No results"})

    @mcp.tool(
        name="gim_get_fix_bundle",
        description=get_fix_bundle_tool.description,
    )
    async def gim_get_fix_bundle(
        issue_id: str,
        include_related: bool = True,
    ) -> str:
        """Get the full fix bundle for a specific issue.

        Args:
            issue_id: The issue ID to get fix bundle for.
            include_related: Whether to include related issues.

        Returns:
            JSON string with fix bundle details.
        """
        arguments = {
            "issue_id": issue_id,
            "include_related": include_related,
        }
        result = await get_fix_bundle_tool.execute(arguments)
        return result[0].text if result else json.dumps({"error": "No results"})

    @mcp.tool(
        name="gim_submit_issue",
        description=submit_issue_tool.description,
    )
    async def gim_submit_issue(
        error_message: str,
        root_cause: str,
        fix_summary: str,
        fix_steps: List[str],
        error_context: Optional[str] = None,
        code_snippet: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> str:
        """Submit a new resolved issue with fix to GIM.

        Args:
            error_message: The error message encountered.
            root_cause: Explanation of what caused the error.
            fix_summary: Brief summary of the fix.
            fix_steps: Step-by-step instructions to fix the issue.
            error_context: Additional context about when/where the error occurred.
            code_snippet: Code that triggered the error (will be sanitized).
            model: AI model being used.
            provider: Model provider.
            language: Programming language context.
            framework: Framework being used.

        Returns:
            JSON string with submission result.
        """
        arguments = {
            "error_message": error_message,
            "root_cause": root_cause,
            "fix_summary": fix_summary,
            "fix_steps": fix_steps,
            "error_context": error_context,
            "code_snippet": code_snippet,
            "model": model,
            "provider": provider,
            "language": language,
            "framework": framework,
        }
        result = await submit_issue_tool.execute(arguments)
        return result[0].text if result else json.dumps({"error": "Submission failed"})

    @mcp.tool(
        name="gim_confirm_fix",
        description=confirm_fix_tool.description,
    )
    async def gim_confirm_fix(
        issue_id: str,
        fix_worked: bool,
        feedback: Optional[str] = None,
    ) -> str:
        """Confirm whether a fix worked.

        Args:
            issue_id: The issue ID.
            fix_worked: Whether the fix resolved the issue.
            feedback: Optional feedback about the fix.

        Returns:
            JSON string with confirmation result.
        """
        arguments = {
            "issue_id": issue_id,
            "fix_worked": fix_worked,
            "feedback": feedback,
        }
        result = await confirm_fix_tool.execute(arguments)
        return result[0].text if result else json.dumps({"error": "Confirmation failed"})

    @mcp.tool(
        name="gim_report_usage",
        description=report_usage_tool.description,
    )
    async def gim_report_usage(
        event_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Report usage analytics event.

        Args:
            event_type: Type of event to report.
            metadata: Optional event metadata.

        Returns:
            JSON string with report result.
        """
        arguments = {
            "event_type": event_type,
            "metadata": metadata,
        }
        result = await report_usage_tool.execute(arguments)
        return result[0].text if result else json.dumps({"error": "Report failed"})


def run_server() -> None:
    """Run the MCP server based on configuration."""
    settings = get_settings()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GIM MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=settings.transport_mode,
        help="Transport mode (default: from config)",
    )
    parser.add_argument(
        "--host",
        default=settings.http_host,
        help="HTTP host (default: from config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.http_port,
        help="HTTP port (default: from config)",
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable authentication (not recommended for production)",
    )
    args = parser.parse_args()

    # Create server
    use_auth = not args.no_auth
    mcp = create_mcp_server(use_auth=use_auth)

    logger.info(
        f"Starting GIM MCP Server "
        f"(transport={args.transport}, auth={'enabled' if use_auth else 'disabled'})"
    )

    # Run with appropriate transport
    if args.transport == "http":
        # Configure CORS middleware for frontend access
        cors_middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=[
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ]

        mcp.run(
            transport="http",
            host=args.host,
            port=args.port,
            path="/",  # Serve MCP at root path for OAuth compatibility
            middleware=cors_middleware,
        )
    else:
        mcp.run(transport="stdio")


# For direct execution
if __name__ == "__main__":
    run_server()
