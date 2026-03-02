"""Tests for prompts API endpoints."""

import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_list_prompts_grouped_returns_valid_structure(
    client, test_user, auth_headers
):
    """Test that /prompts/grouped returns valid response structure."""
    response = await client.get(
        "/api/v1/prompts/grouped?template_type=aggregators",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Check top-level fields
    assert data["template_type"] == "aggregators"
    assert isinstance(data["total_fields"], int)
    assert data["total_fields"] > 0
    assert isinstance(data["total_prompts_defined"], int)
    assert isinstance(data["coverage_percent"], float)
    assert isinstance(data["sections"], list)
    assert len(data["sections"]) > 0

    # Check section structure
    section = data["sections"][0]
    assert "section" in section
    assert "field_count" in section
    assert "prompts_defined" in section
    assert "fields" in section
    assert isinstance(section["fields"], list)

    # Check field structure
    if section["fields"]:
        field = section["fields"][0]
        assert "field_name" in field
        assert "row" in field
        assert "character_limit" in field
        assert "required" in field
        assert "has_prompt" in field
        assert "prompt_id" in field
        assert "version" in field
        assert "content_preview" in field


@pytest.mark.asyncio
async def test_list_prompts_grouped_coverage_calculation(
    client, test_db, test_user, auth_headers
):
    """Test that coverage percentage is calculated correctly."""
    # Import here to avoid circular imports
    from app.models.database import Prompt

    # Create a prompt for the aggregators template
    now = datetime.now(timezone.utc)
    prompt = Prompt(
        name="meta_title",
        template_type="aggregators",
        content_variant="standard",
        content="Generate a meta title for {project_name}",
        character_limit=60,
        version=1,
        is_active=True,
        created_by=test_user.id,
        updated_by=test_user.id,
        created_at=now,
        updated_at=now,
    )
    test_db.add(prompt)
    await test_db.commit()

    response = await client.get(
        "/api/v1/prompts/grouped?template_type=aggregators",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should have at least 1 prompt defined
    assert data["total_prompts_defined"] >= 1

    # Coverage should be positive
    assert data["coverage_percent"] > 0

    # Verify math: coverage = (prompts_defined / promptable_fields) * 100
    assert "promptable_fields" in data
    expected_coverage = round(
        data["total_prompts_defined"] / data["promptable_fields"] * 100, 1
    )
    assert data["coverage_percent"] == expected_coverage


@pytest.mark.asyncio
async def test_list_prompts_grouped_invalid_template_returns_400(
    client, test_user, auth_headers
):
    """Test that invalid template_type returns 400."""
    response = await client.get(
        "/api/v1/prompts/grouped?template_type=invalid_template",
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_TEMPLATE_TYPE"
    assert "allowed" in data["detail"]["details"]


@pytest.mark.asyncio
async def test_list_prompts_grouped_missing_template_returns_422(
    client, test_user, auth_headers
):
    """Test that missing template_type returns 422 validation error."""
    response = await client.get(
        "/api/v1/prompts/grouped",
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_prompts_grouped_all_templates(client, test_user, auth_headers):
    """Test that all 6 template types work."""
    templates = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]

    for template in templates:
        response = await client.get(
            f"/api/v1/prompts/grouped?template_type={template}",
            headers=auth_headers,
        )
        assert response.status_code == 200, f"Failed for template: {template}"
        data = response.json()
        assert data["template_type"] == template
        assert data["total_fields"] > 0


@pytest.mark.asyncio
async def test_list_prompts_grouped_prompt_details_included(
    client, test_db, test_user, auth_headers
):
    """Test that prompt details are included when prompt exists."""
    from app.models.database import Prompt

    now = datetime.now(timezone.utc)
    prompt = Prompt(
        name="meta_description",
        template_type="opr",
        content_variant="standard",
        content="Generate an SEO meta description for {project_name} in {location}",
        character_limit=160,
        version=3,
        is_active=True,
        created_by=test_user.id,
        updated_by=test_user.id,
        created_at=now,
        updated_at=now,
    )
    test_db.add(prompt)
    await test_db.commit()
    await test_db.refresh(prompt)

    response = await client.get(
        "/api/v1/prompts/grouped?template_type=opr",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Find the field with our prompt
    found = False
    for section in data["sections"]:
        for field in section["fields"]:
            if field["field_name"] == "meta_description":
                found = True
                assert field["has_prompt"] is True
                assert field["prompt_id"] == str(prompt.id)
                assert field["version"] == 3
                assert field["content_preview"].startswith("Generate an SEO")
                break
        if found:
            break

    assert found, "meta_description field not found in response"


@pytest.mark.asyncio
async def test_list_prompts_grouped_content_variant_filter(
    client, test_db, test_user, auth_headers
):
    """Test that content_variant filter works."""
    from app.models.database import Prompt

    now = datetime.now(timezone.utc)

    # Create standard variant prompt
    standard_prompt = Prompt(
        name="hero_title",
        template_type="aggregators",
        content_variant="standard",
        content="Standard hero title prompt",
        version=1,
        is_active=True,
        created_by=test_user.id,
        updated_by=test_user.id,
        created_at=now,
        updated_at=now,
    )
    test_db.add(standard_prompt)

    # Create luxury variant prompt
    luxury_prompt = Prompt(
        name="hero_title",
        template_type="aggregators",
        content_variant="luxury",
        content="Luxury hero title prompt",
        version=1,
        is_active=True,
        created_by=test_user.id,
        updated_by=test_user.id,
        created_at=now,
        updated_at=now,
    )
    test_db.add(luxury_prompt)
    await test_db.commit()

    # Query standard variant
    response = await client.get(
        "/api/v1/prompts/grouped?template_type=aggregators&content_variant=standard",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Find hero_title field
    for section in data["sections"]:
        for field in section["fields"]:
            if field["field_name"] == "hero_title":
                assert field["has_prompt"] is True
                assert field["content_preview"] == "Standard hero title prompt"
                break

    # Query luxury variant
    response = await client.get(
        "/api/v1/prompts/grouped?template_type=aggregators&content_variant=luxury",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    for section in data["sections"]:
        for field in section["fields"]:
            if field["field_name"] == "hero_title":
                assert field["has_prompt"] is True
                assert field["content_preview"] == "Luxury hero title prompt"
                break


@pytest.mark.asyncio
async def test_list_prompts_grouped_requires_auth(client):
    """Test that endpoint requires authentication."""
    response = await client.get(
        "/api/v1/prompts/grouped?template_type=aggregators",
    )

    assert response.status_code == 403
