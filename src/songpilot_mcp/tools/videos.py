"""Music video projects and templates."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from songpilot_mcp.server import mcp
from songpilot_mcp.tools._api import Input, call

AspectRatio = Literal["9:16", "16:9", "1:1", "4:5"]
TemplateType = Literal["video", "campaign", "social_post", "email", "social_recipe"]


class MusicVideoCreate(Input):
    name: str = Field(min_length=1)
    song_id: UUID | None = Field(None, description="Song the video is for")
    aspect_ratio: AspectRatio | None = None
    template_id: UUID | None = Field(None, description="Video template to start from")
    deliverable_format: (
        Literal["social_post", "teaser", "lyric_visual", "full_video"] | None
    ) = None
    target_platforms: list[str] | None = Field(
        None, description="e.g. instagram, tiktok, youtube"
    )
    production_mode: Literal["artist_led", "ai_generated"] | None = None


class MusicVideoUpdate(Input):
    name: str | None = Field(None, min_length=1)
    song_id: UUID | None = Field(None, description="Song to link; null unlinks it")
    status: (
        Literal["draft", "storyboard", "recording", "editing", "complete"] | None
    ) = None
    aspect_ratio: AspectRatio | None = None
    style_bible: dict[str, Any] | None = Field(
        None, description="The project's look and concept; replaced whole"
    )
    style_locked: bool | None = None
    cast_member_ids: list[UUID] | None = Field(
        None, description="Members on camera; replaced whole"
    )
    estimated_bpm: float | None = Field(None, ge=20, le=400)


class TemplateFields(Input):
    description: str | None = None
    category: str | None = None
    config: dict[str, Any] | None = Field(None, description="Replaced whole")
    is_public: bool | None = Field(
        None,
        serialization_alias="isPublic",
        description="Share it read-only with every SongPilot workspace",
    )


class TemplateCreate(TemplateFields):
    name: str = Field(min_length=1)
    type: TemplateType


class TemplateUpdate(TemplateFields):
    name: str | None = Field(None, min_length=1)


@mcp.tool()
async def list_music_videos() -> Any:
    """List the workspace's music video projects, newest first."""
    return await call("GET", "/api/music-videos")


@mcp.tool()
async def get_music_video(music_video_id: UUID) -> Any:
    """Get one music video project."""
    return await call("GET", f"/api/music-videos/{music_video_id}")


@mcp.tool()
async def create_music_video(video: MusicVideoCreate) -> Any:
    """Create an empty music video project. Uses no credits."""
    return await call("POST", "/api/music-videos", json=video.body())


@mcp.tool()
async def update_music_video(music_video_id: UUID, changes: MusicVideoUpdate) -> Any:
    """Change a music video project. Scenes are not changed. Uses no credits."""
    return await call("PUT", f"/api/music-videos/{music_video_id}", json=changes.body())


@mcp.tool()
async def list_templates(
    type: TemplateType | None = None,
    category: str | None = None,
) -> Any:
    """List templates the workspace can use: its own, system and public ones."""
    return await call(
        "GET", "/api/templates", params={"type": type, "category": category}
    )


@mcp.tool()
async def get_template(template_id: UUID) -> Any:
    """Get one template."""
    return await call("GET", f"/api/templates/{template_id}")


@mcp.tool()
async def create_template(template: TemplateCreate) -> Any:
    """Create a template owned by the workspace."""
    return await call("POST", "/api/templates", json=template.body())


@mcp.tool()
async def update_template(template_id: UUID, changes: TemplateUpdate) -> Any:
    """Change one of the workspace's own templates. System templates cannot change."""
    return await call(
        "PUT",
        f"/api/templates/{template_id}",
        json=changes.body(),
        errors={403: "Only the workspace's own templates can be changed."},
    )
