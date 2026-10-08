"""Releases and their track lists. Submitting for distribution stays in the app."""

from typing import Any, Literal
from uuid import UUID

from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from songpilot_mcp.server import mcp
from songpilot_mcp.tools._api import Input, call

ReleaseType = Literal["single", "ep", "album", "compilation"]


class ReleaseFields(Input):
    description: str | None = None
    release_date: str | None = Field(
        None, serialization_alias="releaseDate", description="YYYY-MM-DD"
    )
    planned_release_date: str | None = Field(
        None, serialization_alias="plannedReleaseDate", description="YYYY-MM-DD"
    )
    genre: str | None = None
    record_label: str | None = Field(None, serialization_alias="recordLabel")
    visual_style_notes: str | None = Field(None, serialization_alias="visualStyleNotes")
    themes: list[str] | None = None
    mood: str | None = None


class ReleaseCreate(ReleaseFields):
    title: str = Field(min_length=1)
    release_type: ReleaseType = Field(serialization_alias="releaseType")


class ReleaseUpdate(ReleaseFields):
    title: str | None = Field(None, min_length=1)
    release_type: ReleaseType | None = Field(None, serialization_alias="releaseType")
    status: Literal["draft", "scheduled", "released", "archived"] | None = None
    explicit_content: bool | None = Field(None, serialization_alias="explicitContent")


_SONGS_ERRORS = {
    404: "Release or one of the songs not found in this workspace.",
    409: "One or more of those songs are already on this release.",
}


@mcp.tool()
async def list_releases() -> Any:
    """List every release in the workspace, newest first."""
    return await call("GET", "/api/releases")


@mcp.tool()
async def get_release(release_id: UUID) -> Any:
    """Get one release with its track list."""
    release = await call("GET", f"/api/releases/{release_id}")
    songs = await call("GET", f"/api/releases/{release_id}/songs")
    return {"release": release, "songs": songs}


@mcp.tool()
async def create_release(
    release: ReleaseCreate, song_ids: list[UUID] | None = None
) -> dict[str, Any]:
    """Create a draft release and, optionally, add songs to it in order."""
    created = await call("POST", "/api/releases", json=release.body())
    if not song_ids:
        return {"release": created, "songs": []}
    try:
        songs = await call(
            "POST",
            f"/api/releases/{created['id']}/songs",
            json={"songIds": [str(s) for s in song_ids]},
            errors=_SONGS_ERRORS,
        )
    except ToolError as e:
        # The draft exists; say so, so the caller fixes it instead of creating another.
        return {"release": created, "songs": [], "songs_error": str(e)}
    return {"release": created, "songs": songs}


@mcp.tool()
async def update_release(release_id: UUID, changes: ReleaseUpdate) -> Any:
    """Change a release. Only the fields you send are changed."""
    return await call("PUT", f"/api/releases/{release_id}", json=changes.body())


@mcp.tool()
async def add_songs_to_release(release_id: UUID, song_ids: list[UUID]) -> Any:
    """Append songs to the end of a release's track list, in the order given."""
    return await call(
        "POST",
        f"/api/releases/{release_id}/songs",
        json={"songIds": [str(s) for s in song_ids]},
        errors=_SONGS_ERRORS,
    )
