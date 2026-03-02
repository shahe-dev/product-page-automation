"""
Comprehensive test suite for DataExtractor service.

Tests cover:
- Main extract() method with all field population
- Project name extraction (headers, patterns, title-case)
- Developer extraction (by pattern, known developers)
- Location extraction (emirate, community, full location)
- Price extraction (AED formats, ranges, starting from)
- Bedroom extraction (BR, Bedroom, Studio formats)
- Completion date extraction (quarter, handover, year)
- Amenities extraction (keyword matching, bullet lists)
- Payment plan extraction (percentages, text format)
- get_page_context() for surrounding page retrieval
"""

import pytest

from app.services.data_extractor import (
    DUBAI_COMMUNITIES,
    KNOWN_DEVELOPERS,
    UAE_EMIRATES,
    DataExtractor,
    ExtractionOutput,
    FieldResult,
    LocationResult,
    PaymentPlanResult,
    PriceResult,
)


# ============================================================================
# Fixtures - Sample Real Estate Brochure Text
# ============================================================================


@pytest.fixture
def sample_brochure_text():
    """Full sample text from a real estate brochure."""
    return """
# Marina Vista

by Emaar Properties

Located in Dubai Marina, Dubai

Premium waterfront living with stunning views.

Starting from AED 1,200,000

Available Units: Studio, 1BR, 2BR, 3BR

Handover: Q4 2026

Payment Plan:
- 20% down payment
- 60% during construction
- 20% on handover

Amenities:
- Swimming Pool
- Gym
- 24/7 Security
- Covered Parking
- Kids Play Area
- Landscaped Gardens

Property Type: Apartment
"""


@pytest.fixture
def minimal_brochure_text():
    """Minimal brochure text with few details."""
    return """
Some project overview text here.
Not much useful information.
Contact us for details.
"""


@pytest.fixture
def multi_page_text_map():
    """Sample page text map for context testing."""
    return {
        1: "# Project Overview\nIntroduction to the project",
        2: "## Location\nDubai Marina, Dubai",
        3: "## Pricing\nStarting from AED 850,000",
        4: "## Amenities\nSwimming Pool, Gym, Parking",
        5: "## Payment Plan\n10% booking, 80% during construction, 10% on handover"
    }


@pytest.fixture
def empty_text_map():
    """Empty page text map."""
    return {}


# ============================================================================
# Tests: DataExtractor.extract() - Main extraction method
# ============================================================================


def test_extract_populates_all_fields(sample_brochure_text):
    """Test that extract() populates all ExtractionOutput fields."""
    extractor = DataExtractor()
    page_text_map = {1: sample_brochure_text}

    result = extractor.extract(page_text_map)

    # Verify result is ExtractionOutput instance
    assert isinstance(result, ExtractionOutput)

    # Verify all major fields are populated
    assert isinstance(result.project_name, FieldResult)
    assert isinstance(result.developer, FieldResult)
    assert isinstance(result.location, LocationResult)
    assert isinstance(result.prices, PriceResult)
    assert isinstance(result.bedrooms, list)
    assert isinstance(result.completion_date, FieldResult)
    assert isinstance(result.amenities, list)
    assert isinstance(result.payment_plan, PaymentPlanResult)
    assert isinstance(result.property_type, FieldResult)

    # Verify metadata fields
    assert result.total_pages == 1
    assert result.full_text != ""
    assert result.extraction_method == "regex"
    assert isinstance(result.errors, list)


def test_extract_with_empty_text_map(empty_text_map):
    """Test extraction with empty text map returns output with None/empty fields."""
    extractor = DataExtractor()

    result = extractor.extract(empty_text_map)

    assert isinstance(result, ExtractionOutput)
    assert result.total_pages == 0
    assert result.full_text == ""
    assert result.project_name.value is None
    assert result.developer.value is None
    assert result.location.emirate is None
    assert result.prices.min_price is None
    assert result.bedrooms == []
    assert result.completion_date.value is None
    assert result.amenities == []


def test_extract_combines_all_pages(multi_page_text_map):
    """Test that extract() combines all page content into full_text."""
    extractor = DataExtractor()

    result = extractor.extract(multi_page_text_map)

    assert result.total_pages == 5
    # Verify full_text contains content from all pages
    assert "Project Overview" in result.full_text
    assert "Dubai Marina" in result.full_text
    assert "AED 850,000" in result.full_text
    assert "Swimming Pool" in result.full_text
    assert "Payment Plan" in result.full_text


def test_extract_logs_low_confidence_errors(minimal_brochure_text):
    """Test that low confidence extractions are logged in errors."""
    extractor = DataExtractor()
    page_text_map = {1: minimal_brochure_text}

    result = extractor.extract(page_text_map)

    # Should have errors for low confidence fields
    assert len(result.errors) > 0
    error_messages = " ".join(result.errors).lower()
    assert "project name" in error_messages or "developer" in error_messages


# ============================================================================
# Tests: extract_project_name()
# ============================================================================


def test_extract_project_name_from_h1_header():
    """Test extracting project name from H1 header (# Marina Vista)."""
    extractor = DataExtractor()
    text = """
# Marina Vista

by Emaar Properties
Located in Dubai Marina
"""

    result = extractor.extract_project_name(text)

    assert result.value == "Marina Vista"
    assert result.confidence == 0.9
    assert result.source == "heading"


def test_extract_project_name_from_title_case():
    """Test extracting project name from prominent title-case text."""
    extractor = DataExtractor()
    text = """
Welcome to The Pearl by Emaar
Located in downtown Dubai
Luxury apartments for sale
"""

    result = extractor.extract_project_name(text)

    assert result.value is not None
    # Should match "The Pearl" part
    assert "Pearl" in result.value or "The Pearl" in result.value
    assert result.confidence > 0.0


def test_extract_project_name_from_pattern():
    """Test extracting from 'Project: Name' pattern."""
    extractor = DataExtractor()
    text = """
Project: Azure Residences
Developer: DAMAC Properties
"""

    result = extractor.extract_project_name(text)

    assert "Azure Residences" in result.value
    assert result.confidence >= 0.8
    assert result.source == "regex"


def test_extract_project_name_not_found():
    """Test project name extraction returns None with low confidence when not found."""
    extractor = DataExtractor()
    text = """
some random text here
no project name present
just generic content
"""

    result = extractor.extract_project_name(text)

    assert result.value is None
    assert result.confidence == 0.0
    assert result.source == "none"


def test_extract_project_name_filters_generic_headers():
    """Test that generic headers like 'Overview' are filtered out."""
    extractor = DataExtractor()
    text = """
# Overview

This is a project overview document
"""

    result = extractor.extract_project_name(text)

    # Should skip "Overview" and return None or look for other patterns
    assert result.value != "Overview"


# ============================================================================
# Tests: extract_developer()
# ============================================================================


def test_extract_developer_by_pattern():
    """Test extracting developer from 'by Emaar' pattern."""
    extractor = DataExtractor()
    text = """
# Marina Vista
by Emaar
Located in Dubai Marina
"""

    result = extractor.extract_developer(text)

    assert result.value == "Emaar"
    assert result.confidence == 0.9
    assert result.source == "regex"


def test_extract_developer_developed_by():
    """Test extracting from 'Developed by DAMAC' pattern."""
    extractor = DataExtractor()
    text = """
Premium apartments
Developed by DAMAC Properties
In the heart of Dubai
"""

    result = extractor.extract_developer(text)

    assert "DAMAC" in result.value
    assert result.confidence >= 0.5
    assert result.source == "regex"


def test_extract_developer_from_known_list():
    """Test matching against known developer names for higher confidence."""
    extractor = DataExtractor()

    # Test multiple known developers
    for dev in ["Emaar", "DAMAC", "Nakheel", "Meraas"]:
        text = f"by {dev} Properties"
        result = extractor.extract_developer(text)

        assert dev in result.value
        assert result.confidence >= 0.9  # Should have high confidence


def test_extract_developer_colon_format():
    """Test 'Developer: Name' format."""
    extractor = DataExtractor()
    text = """
Project Details
Developer: Sobha Realty
Location: Dubai
"""

    result = extractor.extract_developer(text)

    assert "Sobha" in result.value
    assert result.confidence > 0.0


def test_extract_developer_not_found():
    """Test developer extraction returns None when not found."""
    extractor = DataExtractor()
    text = """
just some generic text
no developer mentioned
"""

    result = extractor.extract_developer(text)

    assert result.value is None
    assert result.confidence == 0.0
    assert result.source == "none"


def test_extract_developer_unknown_name_lower_confidence():
    """Test that unknown developers have lower confidence than known ones."""
    extractor = DataExtractor()
    text = "by Unknown Developer LLC"

    result = extractor.extract_developer(text)

    # Should extract but with lower confidence
    if result.value:
        assert result.confidence < 0.9


# ============================================================================
# Tests: extract_location()
# ============================================================================


def test_extract_location_emirate_dubai():
    """Test detecting Dubai emirate."""
    extractor = DataExtractor()
    text = "Located in Dubai near the beach"

    result = extractor.extract_location(text)

    assert result.emirate == "Dubai"
    assert result.confidence == 0.9


def test_extract_location_community():
    """Test detecting Dubai Marina community."""
    extractor = DataExtractor()
    text = "Premium apartments in Dubai Marina, Dubai"

    result = extractor.extract_location(text)

    assert result.emirate == "Dubai"
    assert result.community == "Dubai Marina"
    assert result.confidence == 0.9


def test_extract_location_full():
    """Test full location with both emirate and community."""
    extractor = DataExtractor()
    text = "Located in Business Bay, Dubai"

    result = extractor.extract_location(text)

    assert result.emirate == "Dubai"
    assert result.community == "Business Bay"
    assert result.full_location == "Business Bay, Dubai"
    assert result.confidence == 0.9


def test_extract_location_abu_dhabi():
    """Test handling multi-word emirate (Abu Dhabi)."""
    extractor = DataExtractor()
    text = "New development in Abu Dhabi"

    result = extractor.extract_location(text)

    assert result.emirate == "Abu Dhabi"
    assert result.confidence == 0.9


def test_extract_location_jvc():
    """Test extracting JVC (Jumeirah Village Circle) abbreviation."""
    extractor = DataExtractor()
    text = "Affordable housing in JVC, Dubai"

    result = extractor.extract_location(text)

    assert result.community == "JVC"
    assert result.emirate == "Dubai"


def test_extract_location_not_found():
    """Test location extraction when no location is present."""
    extractor = DataExtractor()
    text = "Generic property description"

    result = extractor.extract_location(text)

    assert result.emirate is None
    assert result.community is None
    assert result.full_location is None
    assert result.confidence == 0.0


# ============================================================================
# Tests: extract_prices()
# ============================================================================


def test_extract_price_aed_format():
    """Test extracting standard AED price format (AED 1,200,000)."""
    extractor = DataExtractor()
    text = "Prices starting at AED 1,200,000"

    result = extractor.extract_prices(text)

    assert result.min_price == 1_200_000
    assert result.currency == "AED"
    assert result.confidence > 0.0


def test_extract_price_starting_from():
    """Test extracting 'Starting from AED 850K' format."""
    extractor = DataExtractor()
    text = "Starting from AED 850K"

    result = extractor.extract_prices(text)

    assert result.min_price == 850_000
    assert result.currency == "AED"


def test_extract_price_range():
    """Test extracting price range (AED 1.2M - AED 3.5M)."""
    extractor = DataExtractor()
    text = "Prices range from AED 1.2M to AED 3.5M"

    result = extractor.extract_prices(text)

    assert result.min_price == 1_200_000
    assert result.max_price == 3_500_000
    assert result.currency == "AED"
    assert result.confidence >= 0.6


def test_extract_price_per_sqft():
    """Test extracting price per square foot (AED 2,500 per sq ft)."""
    extractor = DataExtractor()
    text = "Units priced at AED 2,500 per sq ft"

    result = extractor.extract_prices(text)

    # Should extract 2,500 but filter it out as too low for property price
    # Or might not extract at all - both are acceptable
    if result.min_price:
        assert result.min_price >= 100_000


def test_extract_price_million_format():
    """Test extracting million format (AED 2.5M)."""
    extractor = DataExtractor()
    text = "Luxury villas from AED 2.5M"

    result = extractor.extract_prices(text)

    assert result.min_price == 2_500_000


def test_extract_price_thousand_format():
    """Test extracting thousand format (AED 500K)."""
    extractor = DataExtractor()
    text = "Affordable studios from AED 450K"

    result = extractor.extract_prices(text)

    assert result.min_price == 450_000


def test_extract_price_filters_outliers():
    """Test that unrealistic prices are filtered out."""
    extractor = DataExtractor()
    text = "Price: AED 50,000 service fee, units from AED 1,000,000"

    result = extractor.extract_prices(text)

    # Should filter out the 50K and keep 1M
    assert result.min_price == 1_000_000


def test_extract_price_not_found():
    """Test price extraction when no prices are present."""
    extractor = DataExtractor()
    text = "Contact us for pricing details"

    result = extractor.extract_prices(text)

    assert result.min_price is None
    assert result.max_price is None
    assert result.confidence == 0.0


def test_extract_price_decimal_notation():
    """Test price with decimal notation (AED 1.2M, AED 1.5M)."""
    extractor = DataExtractor()
    text = "Units priced at AED 1.2M and AED 1.5M"

    result = extractor.extract_prices(text)

    assert result.min_price == 1_200_000
    assert result.max_price == 1_500_000


# ============================================================================
# Tests: extract_bedrooms()
# ============================================================================


def test_extract_bedrooms_br_format():
    """Test extracting bedroom configurations in BR format (1BR, 2BR, 3BR)."""
    extractor = DataExtractor()
    text = "Available units: 1BR, 2BR, 3BR"

    result = extractor.extract_bedrooms(text)

    assert "1BR" in result
    assert "2BR" in result
    assert "3BR" in result
    assert len(result) == 3


def test_extract_bedrooms_bedroom_format():
    """Test extracting '2 Bedroom' format."""
    extractor = DataExtractor()
    text = "Choose from 1 Bedroom, 2 Bedroom, or 3 Bedroom apartments"

    result = extractor.extract_bedrooms(text)

    assert "1BR" in result
    assert "2BR" in result
    assert "3BR" in result


def test_extract_bedrooms_studio():
    """Test that Studio is included in bedroom configurations."""
    extractor = DataExtractor()
    text = "Studio, 1BR, and 2BR apartments available"

    result = extractor.extract_bedrooms(text)

    assert "Studio" in result
    assert "1BR" in result
    assert "2BR" in result


def test_extract_bedrooms_unique_sorted():
    """Test that bedrooms are unique and sorted (Studio first, then numeric)."""
    extractor = DataExtractor()
    text = """
    2BR apartments
    Studio units
    1BR available
    2 Bedroom option
    Studio apartment
    """

    result = extractor.extract_bedrooms(text)

    # Should be unique
    assert result.count("Studio") == 1
    assert result.count("2BR") == 1

    # Should be sorted: Studio, 1BR, 2BR
    assert result[0] == "Studio"
    assert result[1] == "1BR"
    assert result[2] == "2BR"


def test_extract_bedrooms_b_slash_r_format():
    """Test extracting '1 B/R' format."""
    extractor = DataExtractor()
    text = "Units: 1 B/R, 2 B/R, 3 B/R"

    result = extractor.extract_bedrooms(text)

    assert "1BR" in result
    assert "2BR" in result
    assert "3BR" in result


def test_extract_bedrooms_not_found():
    """Test bedroom extraction when no configurations are mentioned."""
    extractor = DataExtractor()
    text = "Contact us for available units"

    result = extractor.extract_bedrooms(text)

    assert result == []


def test_extract_bedrooms_mixed_formats():
    """Test handling mixed bedroom formats in same text."""
    extractor = DataExtractor()
    text = "Studio, 1BR, 2 Bedroom, 3 B/R apartments"

    result = extractor.extract_bedrooms(text)

    assert "Studio" in result
    assert "1BR" in result
    assert "2BR" in result
    assert "3BR" in result
    # All should be normalized to BR format except Studio
    assert len(result) == 4


# ============================================================================
# Tests: extract_completion_date()
# ============================================================================


def test_extract_completion_quarter_year():
    """Test extracting quarter format (Q4 2026)."""
    extractor = DataExtractor()
    text = "Expected completion: Q4 2026"

    result = extractor.extract_completion_date(text)

    assert "Q4 2026" in result.value
    assert result.confidence == 0.9


def test_extract_completion_handover():
    """Test extracting handover date (Handover: 2027)."""
    extractor = DataExtractor()
    text = "Handover: 2027"

    result = extractor.extract_completion_date(text)

    assert "2027" in result.value
    assert result.confidence >= 0.6


def test_extract_completion_month_year():
    """Test extracting month and year (March 2028)."""
    extractor = DataExtractor()
    text = "Completion Date: March 2028"

    result = extractor.extract_completion_date(text)

    assert "2028" in result.value
    assert "Mar" in result.value or "March" in result.value


def test_extract_completion_q1_format():
    """Test extracting Q1 format."""
    extractor = DataExtractor()
    text = "Ready by Q1 2027"

    result = extractor.extract_completion_date(text)

    assert "Q1 2027" in result.value


def test_extract_completion_delivery():
    """Test 'Delivery: 2026' pattern."""
    extractor = DataExtractor()
    text = "Delivery: Q2 2026"

    result = extractor.extract_completion_date(text)

    assert "Q2 2026" in result.value


def test_extract_completion_not_found():
    """Test completion date extraction when not present."""
    extractor = DataExtractor()
    text = "Great location and amenities"

    result = extractor.extract_completion_date(text)

    assert result.value is None
    assert result.confidence == 0.0


def test_extract_completion_year_only():
    """Test extracting just year (2027)."""
    extractor = DataExtractor()
    text = "Project completion scheduled for 2027"

    result = extractor.extract_completion_date(text)

    assert "2027" in result.value
    assert result.confidence == 0.6


# ============================================================================
# Tests: extract_amenities()
# ============================================================================


def test_extract_amenities_from_bullet_list():
    """Test extracting amenities from markdown bullet list."""
    extractor = DataExtractor()
    text = """
Amenities:
- Swimming Pool
- Gym
- 24/7 Security
- Covered Parking
"""

    result = extractor.extract_amenities(text)

    assert "Swimming Pool" in result
    assert "Gym" in result
    assert "24/7 Security" in result
    assert "Covered Parking" in result


def test_extract_amenities_keyword_match():
    """Test extracting amenities from text containing amenity keywords."""
    extractor = DataExtractor()
    text = """
    The project features a state-of-the-art gym and swimming pool.
    Residents enjoy 24/7 security and covered parking spaces.
    Kids play area and landscaped gardens are also available.
    """

    result = extractor.extract_amenities(text)

    assert "Gym" in result or "Fitness Center" in result or "Fitness Centre" in result
    assert "Swimming Pool" in result or "Pool" in result
    assert "Security" in result or "24/7 Security" in result
    assert "Covered Parking" in result or "Parking" in result


def test_extract_amenities_removes_duplicates():
    """Test that duplicate amenities are removed (e.g., Pool vs Swimming Pool)."""
    extractor = DataExtractor()
    text = "Swimming Pool and pool area available"

    result = extractor.extract_amenities(text)

    # Should only have "Swimming Pool", not both "Swimming Pool" and "Pool"
    if "Swimming Pool" in result:
        assert "Pool" not in result


def test_extract_amenities_fitness_variations():
    """Test handling Gym vs Fitness Center variations."""
    extractor = DataExtractor()
    text = "Fitness Center and Gym available"

    result = extractor.extract_amenities(text)

    # Should prefer Fitness Center/Centre over Gym
    has_fitness = "Fitness Center" in result or "Fitness Centre" in result
    if has_fitness:
        assert "Gym" not in result


def test_extract_amenities_sorted():
    """Test that amenities are returned in sorted order."""
    extractor = DataExtractor()
    text = "Spa, BBQ Area, Gym, Swimming Pool"

    result = extractor.extract_amenities(text)

    # Should be sorted alphabetically
    assert result == sorted(result)


def test_extract_amenities_not_found():
    """Test amenities extraction when none are mentioned."""
    extractor = DataExtractor()
    text = "Contact us for more information"

    result = extractor.extract_amenities(text)

    assert result == []


def test_extract_amenities_case_insensitive():
    """Test that amenity matching is case insensitive."""
    extractor = DataExtractor()
    text = "swimming pool, GYM, covered parking"

    result = extractor.extract_amenities(text)

    assert len(result) > 0
    # Should find matches regardless of case


# ============================================================================
# Tests: extract_payment_plan()
# ============================================================================


def test_extract_payment_plan_percentages():
    """Test extracting payment plan percentages (20/60/20)."""
    extractor = DataExtractor()
    text = """
Payment Plan:
- 20% down payment
- 60% during construction
- 20% on handover
"""

    result = extractor.extract_payment_plan(text)

    assert result.down_payment_pct == 20.0
    assert result.during_construction_pct == 60.0
    assert result.on_handover_pct == 20.0
    assert result.confidence >= 0.6


def test_extract_payment_plan_text_format():
    """Test extracting from text format (20% down payment)."""
    extractor = DataExtractor()
    text = "Easy payment: 10% booking, 70% during construction, 20% on completion"

    result = extractor.extract_payment_plan(text)

    assert result.down_payment_pct == 10.0
    assert result.during_construction_pct == 70.0
    assert result.on_handover_pct == 20.0


def test_extract_payment_plan_post_handover():
    """Test extracting post-handover percentage."""
    extractor = DataExtractor()
    text = """
10% booking
40% during construction
30% on handover
20% post handover
"""

    result = extractor.extract_payment_plan(text)

    assert result.down_payment_pct == 10.0
    assert result.during_construction_pct == 40.0
    assert result.on_handover_pct == 30.0
    assert result.post_handover_pct == 20.0


def test_extract_payment_plan_raw_text():
    """Test that raw payment plan text is captured."""
    extractor = DataExtractor()
    text = """
Payment Plan:
Flexible payment options available with installments.
"""

    result = extractor.extract_payment_plan(text)

    assert result.raw_text is not None
    assert "Payment Plan" in result.raw_text


def test_extract_payment_plan_confidence_scoring():
    """Test that confidence increases with more components found."""
    extractor = DataExtractor()

    # One component
    text1 = "10% down payment"
    result1 = extractor.extract_payment_plan(text1)

    # Three components
    text3 = "10% down payment, 70% during construction, 20% on handover"
    result3 = extractor.extract_payment_plan(text3)

    assert result3.confidence > result1.confidence


def test_extract_payment_plan_not_found():
    """Test payment plan extraction when not present."""
    extractor = DataExtractor()
    text = "Contact us for payment options"

    result = extractor.extract_payment_plan(text)

    assert result.down_payment_pct is None
    assert result.during_construction_pct is None
    assert result.on_handover_pct is None
    assert result.confidence == 0.0


def test_extract_payment_plan_reservation_synonym():
    """Test that 'reservation' is treated as down payment."""
    extractor = DataExtractor()
    text = "5% reservation fee required"

    result = extractor.extract_payment_plan(text)

    assert result.down_payment_pct == 5.0


# ============================================================================
# Tests: extract_property_type()
# ============================================================================


def test_extract_property_type_apartment():
    """Test extracting 'Apartment' property type."""
    extractor = DataExtractor()
    text = "Luxury apartments in Dubai Marina"

    result = extractor.extract_property_type(text)

    assert result.value == "Apartment"
    assert result.confidence == 0.8


def test_extract_property_type_villa():
    """Test extracting 'Villa' property type."""
    extractor = DataExtractor()
    text = "Spacious villas with private gardens"

    result = extractor.extract_property_type(text)

    assert result.value == "Villa"


def test_extract_property_type_townhouse():
    """Test extracting 'Townhouse' property type."""
    extractor = DataExtractor()
    text = "Modern townhouses for families"

    result = extractor.extract_property_type(text)

    assert result.value == "Townhouse"


def test_extract_property_type_not_found():
    """Test property type extraction when not present."""
    extractor = DataExtractor()
    text = "Great investment opportunity"

    result = extractor.extract_property_type(text)

    assert result.value is None
    assert result.confidence == 0.0


def test_extract_property_type_plural():
    """Test that plural forms are matched (apartments, villas)."""
    extractor = DataExtractor()
    text = "We offer apartments and penthouses"

    result = extractor.extract_property_type(text)

    # Should match either Apartment or Penthouse
    assert result.value in ["Apartment", "Penthouse"]


# ============================================================================
# Tests: get_page_context()
# ============================================================================


def test_get_page_context_window(multi_page_text_map):
    """Test that get_page_context returns surrounding pages within window."""
    extractor = DataExtractor()

    # Get context for page 3 with window=1
    context = extractor.get_page_context(multi_page_text_map, 3, window=1)

    # Should include pages 2, 3, 4
    assert "Page 2" in context or "Location" in context
    assert "Pricing" in context
    assert "Amenities" in context

    # Should not include page 1 or 5
    assert "Project Overview" not in context
    assert "Payment Plan" not in context


def test_get_page_context_boundary_first_page(multi_page_text_map):
    """Test get_page_context handles first page boundary correctly."""
    extractor = DataExtractor()

    # Get context for page 1 with window=2
    context = extractor.get_page_context(multi_page_text_map, 1, window=2)

    # Should include pages 1, 2, 3 (can't go before page 1)
    assert "Project Overview" in context
    assert "Location" in context
    assert "Pricing" in context

    # Should not wrap around
    assert "--- Page 0 ---" not in context


def test_get_page_context_boundary_last_page(multi_page_text_map):
    """Test get_page_context handles last page boundary correctly."""
    extractor = DataExtractor()

    # Get context for page 5 with window=2
    context = extractor.get_page_context(multi_page_text_map, 5, window=2)

    # Should include pages 3, 4, 5 (can't go beyond page 5)
    assert "Pricing" in context
    assert "Amenities" in context
    assert "Payment Plan" in context

    # Should not go beyond last page
    assert "--- Page 6 ---" not in context


def test_get_page_context_includes_page_markers(multi_page_text_map):
    """Test that context includes page markers for reference."""
    extractor = DataExtractor()

    context = extractor.get_page_context(multi_page_text_map, 3, window=1)

    # Should have page markers
    assert "--- Page 2 ---" in context
    assert "--- Page 3 ---" in context
    assert "--- Page 4 ---" in context


def test_get_page_context_single_page():
    """Test get_page_context with single page map."""
    extractor = DataExtractor()
    page_map = {1: "Only page content"}

    context = extractor.get_page_context(page_map, 1, window=2)

    assert "Only page content" in context
    assert "--- Page 1 ---" in context


def test_get_page_context_missing_pages():
    """Test get_page_context skips missing page numbers."""
    extractor = DataExtractor()
    page_map = {1: "Page 1", 3: "Page 3", 5: "Page 5"}

    # Get context for page 3 with window=2
    context = extractor.get_page_context(page_map, 3, window=2)

    # Should include pages 1, 3, 5 (skipping missing 2 and 4)
    assert "Page 1" in context
    assert "Page 3" in context
    assert "Page 5" in context
    assert "--- Page 2 ---" not in context
    assert "--- Page 4 ---" not in context


def test_get_page_context_window_zero():
    """Test get_page_context with window=0 returns only target page."""
    extractor = DataExtractor()
    page_map = {1: "Page 1", 2: "Page 2", 3: "Page 3"}

    context = extractor.get_page_context(page_map, 2, window=0)

    # Should only include page 2
    assert "Page 2" in context
    assert "Page 1" not in context
    assert "Page 3" not in context


# ============================================================================
# Tests: Edge Cases and Data Variations
# ============================================================================


def test_extract_with_unicode_text():
    """Test extraction handles unicode characters gracefully."""
    extractor = DataExtractor()
    text = """
# Azure Residences
by Emaar Properties
Located in Dubai Marina, UAE
Premium living experience
"""

    result = extractor.extract_project_name(text)

    # Should extract successfully despite unicode
    assert result.value is not None


def test_extract_location_multiple_emirates():
    """Test that first emirate match is used."""
    extractor = DataExtractor()
    text = "Properties in Dubai and Abu Dhabi available"

    result = extractor.extract_location(text)

    # Should match the first emirate found
    assert result.emirate in UAE_EMIRATES


def test_extract_bedrooms_high_count():
    """Test extracting bedroom counts above 5BR."""
    extractor = DataExtractor()
    text = "Luxury villas with 6BR and 7BR configurations"

    result = extractor.extract_bedrooms(text)

    assert "6BR" in result
    assert "7BR" in result


def test_extract_price_very_large():
    """Test extracting very high prices (50M+)."""
    extractor = DataExtractor()
    text = "Ultra-luxury mansion: AED 75M"

    result = extractor.extract_prices(text)

    assert result.min_price == 75_000_000


def test_combine_pages_preserves_order():
    """Test that _combine_pages maintains correct page order."""
    extractor = DataExtractor()

    # Pages intentionally out of order
    page_map = {3: "Third", 1: "First", 2: "Second"}

    combined = extractor._combine_pages(page_map)

    # Should be in sorted order: First, Second, Third
    assert combined.index("First") < combined.index("Second")
    assert combined.index("Second") < combined.index("Third")


def test_extract_amenities_multiple_variations():
    """Test amenity extraction with multiple synonym variations."""
    extractor = DataExtractor()
    text = """
    Central AC and Central A/C
    Fitness Center and Fitness Centre
    Kids Play Area and Playground
    """

    result = extractor.extract_amenities(text)

    # Should handle variations and avoid too many duplicates
    assert len(result) <= 6  # Max variations without excessive duplication


def test_field_result_dataclass():
    """Test FieldResult dataclass structure."""
    field = FieldResult(value="Test", confidence=0.85, source="regex", page=1)

    assert field.value == "Test"
    assert field.confidence == 0.85
    assert field.source == "regex"
    assert field.page == 1


def test_location_result_dataclass():
    """Test LocationResult dataclass structure."""
    location = LocationResult(
        emirate="Dubai",
        community="Dubai Marina",
        sub_community=None,
        full_location="Dubai Marina, Dubai",
        confidence=0.9
    )

    assert location.emirate == "Dubai"
    assert location.community == "Dubai Marina"
    assert location.sub_community is None
    assert location.full_location == "Dubai Marina, Dubai"
    assert location.confidence == 0.9


def test_price_result_dataclass():
    """Test PriceResult dataclass with defaults."""
    price = PriceResult(min_price=1_000_000, max_price=2_000_000, confidence=0.8)

    assert price.min_price == 1_000_000
    assert price.max_price == 2_000_000
    assert price.currency == "AED"  # Default
    assert price.price_per_sqft is None  # Default
    assert price.confidence == 0.8


def test_payment_plan_result_dataclass():
    """Test PaymentPlanResult dataclass structure."""
    plan = PaymentPlanResult(
        down_payment_pct=20.0,
        during_construction_pct=60.0,
        on_handover_pct=20.0,
        post_handover_pct=None,
        raw_text="20/60/20",
        confidence=0.9
    )

    assert plan.down_payment_pct == 20.0
    assert plan.during_construction_pct == 60.0
    assert plan.on_handover_pct == 20.0
    assert plan.post_handover_pct is None
    assert plan.raw_text == "20/60/20"
    assert plan.confidence == 0.9


# ============================================================================
# Tests: Constants and Reference Data
# ============================================================================


def test_uae_emirates_list():
    """Test that UAE_EMIRATES contains expected emirates."""
    assert "Dubai" in UAE_EMIRATES
    assert "Abu Dhabi" in UAE_EMIRATES
    assert "Sharjah" in UAE_EMIRATES
    assert len(UAE_EMIRATES) == 7


def test_dubai_communities_list():
    """Test that DUBAI_COMMUNITIES contains expected communities."""
    assert "Dubai Marina" in DUBAI_COMMUNITIES
    assert "Downtown Dubai" in DUBAI_COMMUNITIES
    assert "Business Bay" in DUBAI_COMMUNITIES
    assert "JVC" in DUBAI_COMMUNITIES
    assert len(DUBAI_COMMUNITIES) > 30


def test_known_developers_list():
    """Test that KNOWN_DEVELOPERS contains major developers."""
    assert "Emaar" in KNOWN_DEVELOPERS
    assert "DAMAC" in KNOWN_DEVELOPERS
    assert "Nakheel" in KNOWN_DEVELOPERS
    assert "Sobha" in KNOWN_DEVELOPERS
    assert len(KNOWN_DEVELOPERS) >= 10
