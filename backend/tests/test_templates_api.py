"""Tests for template field management API endpoints."""

import pytest
from datetime import datetime, timezone


@pytest.fixture
async def test_template(test_db, admin_user):
    """Create a test template with field mappings."""
    from app.models.database import Template
    from app.models.enums import TemplateType, ContentVariant

    now = datetime.now(timezone.utc)
    template = Template(
        name="Test Aggregators Template",
        template_type=TemplateType.AGGREGATORS,
        content_variant=ContentVariant.STANDARD,
        sheet_template_url="https://docs.google.com/spreadsheets/d/test",
        field_mappings={
            "meta_title": {
                "row": 4,
                "section": "SEO",
                "char_limit": 60,
                "required": True,
                "field_type": "GENERATED",
                "is_active": True,
            },
            "meta_description": {
                "row": 5,
                "section": "SEO",
                "char_limit": 160,
                "required": True,
                "field_type": "GENERATED",
                "is_active": True,
            },
            "hero_title": {
                "row": 10,
                "section": "Hero",
                "char_limit": 80,
                "required": True,
                "field_type": "GENERATED",
                "is_active": True,
            },
        },
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_db.add(template)
    await test_db.commit()
    await test_db.refresh(template)
    return template


# ============================================================================
# GET /templates/type/{template_type}/fields
# ============================================================================


@pytest.mark.asyncio
async def test_get_fields_by_type_success(client, test_template, auth_headers):
    """Test successful retrieval of field definitions."""
    response = await client.get(
        "/api/v1/templates/type/aggregators/fields",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["template_type"] == "aggregators"
    assert data["field_count"] == 3
    assert "fields" in data

    # Check field structure
    assert "meta_title" in data["fields"]
    meta_title = data["fields"]["meta_title"]
    assert meta_title["row"] == 4
    assert meta_title["section"] == "SEO"
    assert meta_title["char_limit"] == 60
    assert meta_title["required"] is True
    assert meta_title["field_type"] == "GENERATED"
    assert meta_title["is_active"] is True


@pytest.mark.asyncio
async def test_get_fields_by_type_invalid_type(client, auth_headers):
    """Test that invalid template type returns 422."""
    response = await client.get(
        "/api/v1/templates/type/invalid_type/fields",
        headers=auth_headers,
    )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_get_fields_by_type_not_found(client, auth_headers):
    """Test that missing template returns 404."""
    response = await client.get(
        "/api/v1/templates/type/opr/fields",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_fields_requires_auth(client):
    """Test that endpoint requires authentication."""
    response = await client.get("/api/v1/templates/type/aggregators/fields")
    assert response.status_code == 403


# ============================================================================
# PUT /templates/type/{template_type}/fields
# ============================================================================


@pytest.mark.asyncio
async def test_update_fields_success(client, test_db, test_template, admin_headers):
    """Test successful full field replacement."""
    new_fields = {
        "meta_title": {
            "row": 4,
            "section": "SEO",
            "char_limit": 70,  # Updated limit
            "required": True,
            "field_type": "GENERATED",
            "is_active": True,
        },
        "new_field": {
            "row": 20,
            "section": "Content",
            "char_limit": None,
            "required": False,
            "field_type": "HYBRID",
            "is_active": True,
        },
    }

    response = await client.put(
        "/api/v1/templates/type/aggregators/fields",
        headers=admin_headers,
        json={"fields": new_fields},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated"] is True
    assert data["field_count"] == 2

    # Verify persistence
    await test_db.refresh(test_template)
    assert "meta_title" in test_template.field_mappings
    assert "new_field" in test_template.field_mappings
    assert test_template.field_mappings["meta_title"]["char_limit"] == 70


@pytest.mark.asyncio
async def test_update_fields_validation_error(client, test_template, admin_headers):
    """Test that invalid fields return 400."""
    invalid_fields = {
        "meta_title": {
            "row": -1,  # Invalid: negative row
            "section": "",  # Invalid: empty section
            "char_limit": 60,
            "required": True,
            "field_type": "INVALID_TYPE",  # Invalid type
            "is_active": True,
        },
    }

    response = await client.put(
        "/api/v1/templates/type/aggregators/fields",
        headers=admin_headers,
        json={"fields": invalid_fields},
    )

    assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_update_fields_duplicate_rows(client, test_template, admin_headers):
    """Test that duplicate row numbers are rejected (except bullet fields)."""
    duplicate_row_fields = {
        "field_a": {
            "row": 10,
            "section": "Content",
            "char_limit": None,
            "required": False,
            "field_type": "GENERATED",
            "is_active": True,
        },
        "field_b": {
            "row": 10,  # Duplicate row
            "section": "Content",
            "char_limit": None,
            "required": False,
            "field_type": "GENERATED",
            "is_active": True,
        },
    }

    response = await client.put(
        "/api/v1/templates/type/aggregators/fields",
        headers=admin_headers,
        json={"fields": duplicate_row_fields},
    )

    assert response.status_code == 400
    data = response.json()
    assert "duplicate row" in data["detail"]["errors"][0].lower()


@pytest.mark.asyncio
async def test_update_fields_requires_admin(client, test_template, auth_headers):
    """Test that non-admin users cannot update fields."""
    response = await client.put(
        "/api/v1/templates/type/aggregators/fields",
        headers=auth_headers,  # Regular user, not admin
        json={"fields": {}},
    )

    assert response.status_code == 403


# ============================================================================
# POST /templates/type/{template_type}/fields/{field_name}
# ============================================================================


@pytest.mark.asyncio
async def test_add_field_success(client, test_db, test_template, admin_headers):
    """Test successful field addition."""
    new_field = {
        "row": 50,
        "section": "New Section",
        "char_limit": 200,
        "required": False,
        "field_type": "EXTRACTED",
    }

    response = await client.post(
        "/api/v1/templates/type/aggregators/fields/new_custom_field",
        headers=admin_headers,
        json=new_field,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["added"] is True
    assert data["field_name"] == "new_custom_field"

    # Verify persistence
    await test_db.refresh(test_template)
    assert "new_custom_field" in test_template.field_mappings


@pytest.mark.asyncio
async def test_add_field_already_exists(client, test_template, admin_headers):
    """Test that adding existing field returns 409."""
    new_field = {
        "row": 100,
        "section": "Test",
        "char_limit": None,
        "required": False,
        "field_type": "GENERATED",
    }

    response = await client.post(
        "/api/v1/templates/type/aggregators/fields/meta_title",  # Already exists
        headers=admin_headers,
        json=new_field,
    )

    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["error_code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_add_field_requires_admin(client, test_template, auth_headers):
    """Test that non-admin users cannot add fields."""
    response = await client.post(
        "/api/v1/templates/type/aggregators/fields/new_field",
        headers=auth_headers,
        json={"row": 100, "section": "Test", "field_type": "GENERATED"},
    )

    assert response.status_code == 403


# ============================================================================
# DELETE /templates/type/{template_type}/fields/{field_name}
# ============================================================================


@pytest.mark.asyncio
async def test_delete_field_success(client, test_db, test_template, admin_headers):
    """Test successful soft deletion."""
    response = await client.delete(
        "/api/v1/templates/type/aggregators/fields/hero_title",
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    assert data["field_name"] == "hero_title"

    # Verify soft delete
    await test_db.refresh(test_template)
    assert test_template.field_mappings["hero_title"]["is_active"] is False


@pytest.mark.asyncio
async def test_delete_field_not_found(client, test_template, admin_headers):
    """Test deleting non-existent field returns 404."""
    response = await client.delete(
        "/api/v1/templates/type/aggregators/fields/nonexistent_field",
        headers=admin_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_field_requires_admin(client, test_template, auth_headers):
    """Test that non-admin users cannot delete fields."""
    response = await client.delete(
        "/api/v1/templates/type/aggregators/fields/meta_title",
        headers=auth_headers,
    )

    assert response.status_code == 403


# ============================================================================
# PATCH /templates/type/{template_type}/fields/{field_name}
# ============================================================================


@pytest.mark.asyncio
async def test_update_single_field_success(
    client, test_db, test_template, admin_headers
):
    """Test successful partial field update."""
    response = await client.patch(
        "/api/v1/templates/type/aggregators/fields/meta_title",
        headers=admin_headers,
        json={"char_limit": 80, "required": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated"] is True

    # Verify persistence
    await test_db.refresh(test_template)
    assert test_template.field_mappings["meta_title"]["char_limit"] == 80
    assert test_template.field_mappings["meta_title"]["required"] is False
    # Unchanged fields should remain
    assert test_template.field_mappings["meta_title"]["row"] == 4


@pytest.mark.asyncio
async def test_update_single_field_not_found(client, test_template, admin_headers):
    """Test updating non-existent field returns 404."""
    response = await client.patch(
        "/api/v1/templates/type/aggregators/fields/nonexistent_field",
        headers=admin_headers,
        json={"char_limit": 100},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_single_field_requires_admin(
    client, test_template, auth_headers
):
    """Test that non-admin users cannot update fields."""
    response = await client.patch(
        "/api/v1/templates/type/aggregators/fields/meta_title",
        headers=auth_headers,
        json={"char_limit": 100},
    )

    assert response.status_code == 403


# ============================================================================
# GET /templates (list all)
# ============================================================================


@pytest.mark.asyncio
async def test_list_templates_success(client, test_template, auth_headers):
    """Test listing templates."""
    response = await client.get(
        "/api/v1/templates",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    # Find our test template
    template = next(
        (t for t in data["items"] if t["template_type"] == "aggregators"), None
    )
    assert template is not None
    assert template["name"] == "Test Aggregators Template"


@pytest.mark.asyncio
async def test_list_templates_filter_by_type(client, test_template, auth_headers):
    """Test filtering templates by type."""
    response = await client.get(
        "/api/v1/templates?template_type=aggregators",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["template_type"] == "aggregators"


@pytest.mark.asyncio
async def test_list_templates_requires_auth(client):
    """Test that endpoint requires authentication."""
    response = await client.get("/api/v1/templates")
    assert response.status_code == 403
