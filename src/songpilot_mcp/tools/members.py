"""Members, member photos and social accounts."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from songpilot_mcp.server import mcp
from songpilot_mcp.tools._api import Input, call

SocialPlatform = Literal[
    "instagram", "tiktok", "youtube", "twitter", "facebook", "spotify"
]


class MemberPersona(Input):
    performance_style: str | None = Field(None, max_length=500)
    energy: Literal["calm", "steady", "high", "wild"] | None = None
    personality: str | None = Field(None, max_length=500)


class MemberFields(Input):
    role: str | None = Field(None, description="Role in the act, e.g. vocalist")
    bio: str | None = None
    display_order: int | None = Field(None, description="Position in lists")
    is_active: bool | None = Field(None, description="Currently part of the act")
    ipi_code: str | None = Field(
        None, pattern=r"^\d{9,11}$", description="IPI/CAE number, 9-11 digits"
    )


class MemberCreate(MemberFields):
    name: str = Field(min_length=1, description="Name, unique in the workspace")


class MemberUpdate(MemberFields):
    name: str | None = Field(None, min_length=1)
    persona: MemberPersona | None = Field(
        None, description="How the member comes across on camera; replaced whole"
    )


@mcp.tool()
async def list_members() -> Any:
    """List the workspace's members with their profile photo and likeness photos."""
    return await call("GET", "/api/members")


@mcp.tool()
async def get_member(member_id: UUID) -> Any:
    """Get one member with their linked photos."""
    return await call("GET", f"/api/members/{member_id}")


@mcp.tool()
async def create_member(member: MemberCreate) -> Any:
    """Add a member to the act."""
    return await call(
        "POST",
        "/api/members",
        json=member.body(),
        errors={409: "A member with that name already exists."},
    )


@mcp.tool()
async def update_member(member_id: UUID, changes: MemberUpdate) -> Any:
    """Change a member. Only the fields you send are changed."""
    return await call(
        "PUT",
        f"/api/members/{member_id}",
        json=changes.body(),
        errors={409: "A member with that name already exists."},
    )


@mcp.tool()
async def link_member_photo(
    member_id: UUID,
    asset_id: UUID,
    category: Literal["training", "professional", "avatar", "banner"],
    is_primary: bool = False,
) -> Any:
    """Link a photo that is already in the workspace to a member.

    category:
    - training: an uploaded photo of the member's face, used to keep their
      likeness in generated images and videos. AI-generated images are refused.
    - professional: a press or promo photo
    - avatar / banner: the member's profile picture or header image
    """
    return await call(
        "POST",
        f"/api/members/{member_id}/assets",
        json={
            "assetId": str(asset_id),
            "assetType": "photo",
            "category": category,
            "isPrimary": is_primary,
        },
        errors={
            400: (
                "That image cannot be linked this way. Likeness photos must be "
                "photos you uploaded, not generated images."
            ),
            404: "Member or image not found in this workspace.",
        },
    )


@mcp.tool()
async def list_social_accounts(
    platform: SocialPlatform | None = None,
    member_id: UUID | None = None,
    owner: Literal["artist", "all"] | None = None,
) -> Any:
    """List connected social accounts.

    Filter by platform, by member_id (that member's own accounts), or with
    owner="artist" for only the artist's accounts.
    """
    return await call(
        "GET",
        "/api/social-media/accounts",
        params={
            "platform": platform,
            "memberId": str(member_id) if member_id else None,
            "owner": owner,
        },
    )


@mcp.tool()
async def get_connect_link(
    platform: SocialPlatform, member_id: UUID | None = None
) -> dict[str, str]:
    """Get a sign-in link that connects a social account to the workspace.

    Open the link in a browser and approve access on the platform. With
    member_id the account becomes that member's own instead of the artist's.
    """
    body: dict[str, Any] = {"platform": platform}
    if member_id:
        body["memberId"] = str(member_id)
    result = await call("POST", "/api/social-media/accounts/connect", json=body)
    url = result.get("redirectUrl") if isinstance(result, dict) else None
    if not url:
        return {"message": f"{platform} cannot be connected right now."}
    return {"connect_url": url}
