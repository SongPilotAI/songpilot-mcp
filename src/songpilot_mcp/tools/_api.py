"""Shared plumbing for the typed tools."""

from typing import Any

from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict

from songpilot_mcp.client import ApiError, get_client


class Input(BaseModel):
    """Base for tool inputs: unknown fields are rejected, not silently dropped."""

    model_config = ConfigDict(extra="forbid")

    def body(self) -> dict[str, Any]:
        """The fields the caller set, under the API's field names."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)


async def call(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    errors: dict[int, str] | None = None,
) -> Any:
    """Call the API and turn a failure into a short tool error."""
    try:
        return await get_client().api_request(
            method, path, json=json, params=params, errors=errors
        )
    except ApiError as e:
        raise ToolError(str(e)) from e
