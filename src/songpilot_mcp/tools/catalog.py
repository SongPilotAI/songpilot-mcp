"""Songs, lyrics and albums."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from songpilot_mcp.server import mcp
from songpilot_mcp.tools._api import Input, call


class SongFields(Input):
    duration_ms: int | None = Field(None, ge=0, description="Length in milliseconds")
    explicit: bool | None = Field(None, description="Explicit content")
    track_number: int | None = Field(None, ge=1, description="Track number")
    album_id: UUID | None = Field(None, description="Album; null removes it")
    artist_id: UUID | None = Field(
        None, description="Artist profile (defaults to the workspace's artist)"
    )
    genre: str | None = None
    isrc_code: str | None = Field(None, description="Track ISRC for the recording")
    iswc_code: str | None = Field(None, description="ISWC for the composition")
    mastering_status: Literal["unmastered", "mastered_by_user"] | None = Field(
        None, description="mastered_by_user when the audio is already mastered"
    )


class SongCreate(SongFields):
    name: str = Field(min_length=1, description="Song title")


class SongUpdate(SongFields):
    name: str | None = Field(None, min_length=1, description="Song title")
    estimated_bpm: float | None = Field(None, ge=20, le=400, description="Tempo")


class AlbumFields(Input):
    album_type: Literal["album", "single", "ep"] | None = None
    release_date: str | None = Field(None, description="YYYY-MM-DD")
    description: str | None = None
    genre: str | None = None
    artist_id: UUID | None = Field(None, description="Artist profile")


class AlbumCreate(AlbumFields):
    name: str = Field(min_length=1, description="Album title")


class AlbumUpdate(AlbumFields):
    name: str | None = Field(None, min_length=1, description="Album title")


@mcp.tool()
async def list_songs() -> Any:
    """List every song in the workspace, newest first, without lyrics."""
    return await call("GET", "/api/songs/all")


@mcp.tool()
async def get_song(song_id: UUID) -> Any:
    """Get one song with its album, artist and lyrics status."""
    return await call("GET", f"/api/songs/{song_id}")


@mcp.tool()
async def create_song(song: SongCreate) -> Any:
    """Add a song to the workspace. Audio is attached separately in the app."""
    return await call("POST", "/api/songs", json=song.body())


@mcp.tool()
async def update_song(song_id: UUID, changes: SongUpdate) -> Any:
    """Change a song. Only the fields you send are changed."""
    return await call("PUT", f"/api/songs/{song_id}", json=changes.body())


@mcp.tool()
async def update_song_lyrics(song_id: UUID, lyrics: str) -> Any:
    """Replace a song's lyrics text. Word timing already saved is kept."""
    return await call("PUT", f"/api/songs/{song_id}/lyrics", json={"lyrics": lyrics})


@mcp.tool()
async def list_albums(include_songs: bool = False) -> Any:
    """List every album in the workspace, newest first."""
    params = {"includeSongs": "true"} if include_songs else None
    return await call("GET", "/api/albums", params=params)


@mcp.tool()
async def get_album(album_id: UUID) -> Any:
    """Get one album."""
    return await call("GET", f"/api/albums/{album_id}")


@mcp.tool()
async def create_album(album: AlbumCreate) -> Any:
    """Create an album. Add songs to it with update_song and album_id."""
    return await call("POST", "/api/albums", json=album.body())


@mcp.tool()
async def update_album(album_id: UUID, changes: AlbumUpdate) -> Any:
    """Change an album. Only the fields you send are changed."""
    return await call("PUT", f"/api/albums/{album_id}", json=changes.body())
