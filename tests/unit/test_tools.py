"""Tests for the typed API tools: paths, headers, bodies and error mapping."""

import json
import os
from unittest.mock import patch

import httpx
import pytest
import respx
from httpx import Response
from mcp.server.fastmcp.exceptions import ToolError

import songpilot_mcp.client as client_module
from songpilot_mcp.config import get_settings

BASE = "https://songpilot.test"
WORKSPACE_ID = "11111111-2222-3333-4444-555555555555"
API_KEY = "sp_test_api_key_12345"
SONG = "aaaaaaaa-0000-0000-0000-000000000001"
ALBUM = "aaaaaaaa-0000-0000-0000-000000000002"
MEMBER = "aaaaaaaa-0000-0000-0000-000000000003"
ASSET = "aaaaaaaa-0000-0000-0000-000000000004"
RELEASE = "aaaaaaaa-0000-0000-0000-000000000005"
VIDEO = "aaaaaaaa-0000-0000-0000-000000000006"
TEMPLATE = "aaaaaaaa-0000-0000-0000-000000000007"


@pytest.fixture(autouse=True)
def settings_env():
    with patch.dict(
        os.environ,
        {
            "SONGPILOT_API_KEY": API_KEY,
            "SONGPILOT_WORKSPACE_ID": WORKSPACE_ID,
            "SONGPILOT_MCP_BASE_URL": BASE,
        },
    ):
        get_settings.cache_clear()
        client_module._client = None
        yield
        get_settings.cache_clear()
        client_module._client = None


@pytest.fixture
def mcp_server():
    from songpilot_mcp.main import mcp

    return mcp


@pytest.fixture
def api():
    """Answer every API call with a wrapped success and record the requests."""
    with respx.mock(assert_all_called=False) as router:
        router.route(host="songpilot.test").mock(
            return_value=Response(
                200,
                json={"success": True, "data": {"id": RELEASE}, "timestamp": "t"},
            )
        )
        yield router


def _requests(router):
    return [call.request for call in router.calls]


# (tool, arguments, [(method, path, json body or None)])
CASES = [
    ("list_songs", {}, [("GET", "/api/songs/all", None)]),
    ("get_song", {"song_id": SONG}, [("GET", f"/api/songs/{SONG}", None)]),
    (
        "create_song",
        {"song": {"name": "Night Drive", "genre": "synthpop"}},
        [("POST", "/api/songs", {"name": "Night Drive", "genre": "synthpop"})],
    ),
    (
        "update_song",
        {"song_id": SONG, "changes": {"album_id": None, "explicit": True}},
        [("PUT", f"/api/songs/{SONG}", {"album_id": None, "explicit": True})],
    ),
    (
        "update_song_lyrics",
        {"song_id": SONG, "lyrics": "line one\nline two"},
        [("PUT", f"/api/songs/{SONG}/lyrics", {"lyrics": "line one\nline two"})],
    ),
    ("list_albums", {}, [("GET", "/api/albums", None)]),
    ("get_album", {"album_id": ALBUM}, [("GET", f"/api/albums/{ALBUM}", None)]),
    (
        "create_album",
        {"album": {"name": "Coastlines", "album_type": "ep"}},
        [("POST", "/api/albums", {"name": "Coastlines", "album_type": "ep"})],
    ),
    (
        "update_album",
        {"album_id": ALBUM, "changes": {"description": "Six songs"}},
        [("PUT", f"/api/albums/{ALBUM}", {"description": "Six songs"})],
    ),
    ("list_members", {}, [("GET", "/api/members", None)]),
    ("get_member", {"member_id": MEMBER}, [("GET", f"/api/members/{MEMBER}", None)]),
    (
        "create_member",
        {"member": {"name": "Avery", "role": "vocalist"}},
        [("POST", "/api/members", {"name": "Avery", "role": "vocalist"})],
    ),
    (
        "update_member",
        {"member_id": MEMBER, "changes": {"persona": {"energy": "high"}}},
        [("PUT", f"/api/members/{MEMBER}", {"persona": {"energy": "high"}})],
    ),
    (
        "link_member_photo",
        {"member_id": MEMBER, "asset_id": ASSET, "category": "training"},
        [
            (
                "POST",
                f"/api/members/{MEMBER}/assets",
                {
                    "assetId": ASSET,
                    "assetType": "photo",
                    "category": "training",
                    "isPrimary": False,
                },
            )
        ],
    ),
    ("list_social_accounts", {}, [("GET", "/api/social-media/accounts", None)]),
    (
        "get_connect_link",
        {"platform": "tiktok", "member_id": MEMBER},
        [
            (
                "POST",
                "/api/social-media/accounts/connect",
                {"platform": "tiktok", "memberId": MEMBER},
            )
        ],
    ),
    ("list_releases", {}, [("GET", "/api/releases", None)]),
    (
        "get_release",
        {"release_id": RELEASE},
        [
            ("GET", f"/api/releases/{RELEASE}", None),
            ("GET", f"/api/releases/{RELEASE}/songs", None),
        ],
    ),
    (
        "create_release",
        {
            "release": {"title": "Coastlines", "release_type": "ep"},
            "song_ids": [SONG],
        },
        [
            ("POST", "/api/releases", {"title": "Coastlines", "releaseType": "ep"}),
            ("POST", f"/api/releases/{RELEASE}/songs", {"songIds": [SONG]}),
        ],
    ),
    (
        "update_release",
        {"release_id": RELEASE, "changes": {"planned_release_date": "2026-11-01"}},
        [
            (
                "PUT",
                f"/api/releases/{RELEASE}",
                {"plannedReleaseDate": "2026-11-01"},
            )
        ],
    ),
    (
        "add_songs_to_release",
        {"release_id": RELEASE, "song_ids": [SONG]},
        [("POST", f"/api/releases/{RELEASE}/songs", {"songIds": [SONG]})],
    ),
    ("list_music_videos", {}, [("GET", "/api/music-videos", None)]),
    (
        "get_music_video",
        {"music_video_id": VIDEO},
        [("GET", f"/api/music-videos/{VIDEO}", None)],
    ),
    (
        "create_music_video",
        {"video": {"name": "Night Drive video", "song_id": SONG}},
        [("POST", "/api/music-videos", {"name": "Night Drive video", "song_id": SONG})],
    ),
    (
        "update_music_video",
        {"music_video_id": VIDEO, "changes": {"cast_member_ids": [MEMBER]}},
        [("PUT", f"/api/music-videos/{VIDEO}", {"cast_member_ids": [MEMBER]})],
    ),
    ("list_templates", {}, [("GET", "/api/templates", None)]),
    (
        "get_template",
        {"template_id": TEMPLATE},
        [("GET", f"/api/templates/{TEMPLATE}", None)],
    ),
    (
        "create_template",
        {"template": {"name": "Teaser", "type": "video", "is_public": False}},
        [
            (
                "POST",
                "/api/templates",
                {"name": "Teaser", "type": "video", "isPublic": False},
            )
        ],
    ),
    (
        "update_template",
        {"template_id": TEMPLATE, "changes": {"name": "Teaser v2"}},
        [("PUT", f"/api/templates/{TEMPLATE}", {"name": "Teaser v2"})],
    ),
]


class TestToolRequests:
    @pytest.mark.parametrize(
        "tool,arguments,expected", CASES, ids=[c[0] for c in CASES]
    )
    async def test_paths_bodies_and_headers(
        self, mcp_server, api, tool, arguments, expected
    ):
        await mcp_server.call_tool(tool, arguments)

        requests = _requests(api)
        assert [(r.method, r.url.path) for r in requests] == [
            (method, path) for method, path, _ in expected
        ]
        for request, (_, _, body) in zip(requests, expected, strict=True):
            assert request.headers["Authorization"] == f"Bearer {API_KEY}"
            assert request.headers["X-Workspace-Id"] == WORKSPACE_ID
            assert WORKSPACE_ID not in str(request.url)
            if body is None:
                assert request.content == b""
            else:
                assert json.loads(request.content) == body

    def test_every_typed_tool_is_covered(self, mcp_server):
        names = {t.name for t in mcp_server._tool_manager.list_tools()}
        assert names - {"run_orchestrator"} == {c[0] for c in CASES}

    async def test_query_parameters(self, mcp_server, api):
        await mcp_server.call_tool(
            "list_social_accounts", {"platform": "instagram", "owner": "artist"}
        )
        await mcp_server.call_tool("list_albums", {"include_songs": True})

        social, albums = _requests(api)
        assert dict(social.url.params) == {"platform": "instagram", "owner": "artist"}
        assert dict(albums.url.params) == {"includeSongs": "true"}

    async def test_cf_access_token_is_sent(self, mcp_server, api):
        with patch.dict(os.environ, {"CF_ACCESS_TOKEN": "cf-token"}):
            get_settings.cache_clear()
            client_module._client = None
            await mcp_server.call_tool("list_songs", {})

        assert _requests(api)[0].headers["cf-access-token"] == "cf-token"

    async def test_unknown_fields_are_rejected(self, mcp_server, api):
        with pytest.raises(ToolError):
            await mcp_server.call_tool(
                "update_release",
                {"release_id": RELEASE, "changes": {"distribution_status": "live"}},
            )
        assert not api.calls

    async def test_ids_must_be_uuids(self, mcp_server, api):
        with pytest.raises(ToolError):
            await mcp_server.call_tool("get_song", {"song_id": "../workspaces/x"})
        assert not api.calls

    async def test_connect_link_returns_the_url(self, mcp_server):
        with respx.mock:
            respx.post(f"{BASE}/api/social-media/accounts/connect").mock(
                return_value=Response(
                    201,
                    json={
                        "success": True,
                        "data": {"success": True, "redirectUrl": "https://x/oauth"},
                    },
                )
            )
            _, result = await mcp_server.call_tool(
                "get_connect_link", {"platform": "youtube"}
            )
        assert result == {"connect_url": "https://x/oauth"}

    async def test_connect_link_unavailable(self, mcp_server):
        with respx.mock:
            respx.post(f"{BASE}/api/social-media/accounts/connect").mock(
                return_value=Response(
                    201,
                    json={
                        "success": True,
                        "data": {"success": False, "error": "Vendor app missing"},
                    },
                )
            )
            _, result = await mcp_server.call_tool(
                "get_connect_link", {"platform": "youtube"}
            )
        assert result == {"message": "youtube cannot be connected right now."}


class TestErrorMapping:
    UPSTREAM = "LabelGrid said: release 123 is invalid"

    @pytest.mark.parametrize(
        "status,fragment",
        [
            (400, "could not accept"),
            (401, "SONGPILOT_API_KEY"),
            (403, "not allowed"),
            (404, "Not found"),
            (302, "sign-in"),
            (500, "temporarily unavailable"),
            (418, "(418)"),
        ],
    )
    async def test_status_becomes_short_message(self, mcp_server, status, fragment):
        with respx.mock:
            respx.get(f"{BASE}/api/songs/all").mock(
                return_value=Response(
                    status, json={"success": False, "error": self.UPSTREAM}
                )
            )
            with pytest.raises(ToolError) as exc:
                await mcp_server.call_tool("list_songs", {})

        message = str(exc.value)
        assert fragment in message
        assert "LabelGrid" not in message
        assert self.UPSTREAM not in message

    async def test_tool_specific_message(self, mcp_server):
        with respx.mock:
            respx.post(f"{BASE}/api/members/{MEMBER}/assets").mock(
                return_value=Response(400, json={"error": self.UPSTREAM})
            )
            with pytest.raises(ToolError) as exc:
                await mcp_server.call_tool(
                    "link_member_photo",
                    {"member_id": MEMBER, "asset_id": ASSET, "category": "training"},
                )
        assert "photos you uploaded" in str(exc.value)
        assert "LabelGrid" not in str(exc.value)

    async def test_create_release_keeps_the_draft_when_songs_fail(self, mcp_server):
        with respx.mock:
            respx.post(f"{BASE}/api/releases").mock(
                return_value=Response(
                    201, json={"success": True, "data": {"id": RELEASE}}
                )
            )
            respx.post(f"{BASE}/api/releases/{RELEASE}/songs").mock(
                return_value=Response(409, json={"error": self.UPSTREAM})
            )
            _, result = await mcp_server.call_tool(
                "create_release",
                {
                    "release": {"title": "X", "release_type": "single"},
                    "song_ids": [SONG],
                },
            )
        assert result["release"] == {"id": RELEASE}
        assert "already on this release" in result["songs_error"]

    async def test_network_error(self, mcp_server):
        with respx.mock:
            respx.get(f"{BASE}/api/songs/all").mock(
                side_effect=httpx.ConnectError("boom")
            )
            with pytest.raises(ToolError) as exc:
                await mcp_server.call_tool("list_songs", {})
        assert "Could not reach SongPilot" in str(exc.value)

    async def test_non_json_success_body(self, mcp_server):
        with respx.mock:
            respx.get(f"{BASE}/api/songs/all").mock(
                return_value=Response(200, text="<html>login</html>")
            )
            with pytest.raises(ToolError) as exc:
                await mcp_server.call_tool("list_songs", {})
        assert "html" not in str(exc.value)


class TestApiRequest:
    async def test_rejects_paths_outside_the_api(self):
        with pytest.raises(ValueError):
            await client_module.get_client().api_request("GET", "/agents/x")

    async def test_unwraps_and_passes_unwrapped_bodies(self):
        with respx.mock:
            respx.get(f"{BASE}/api/a").mock(
                return_value=Response(200, json={"success": True, "data": [1]})
            )
            respx.get(f"{BASE}/api/b").mock(return_value=Response(200, json=[2]))
            respx.delete(f"{BASE}/api/c").mock(return_value=Response(204))
            client = client_module.get_client()
            assert await client.api_request("GET", "/api/a") == [1]
            assert await client.api_request("GET", "/api/b") == [2]
            assert await client.api_request("DELETE", "/api/c") is None
