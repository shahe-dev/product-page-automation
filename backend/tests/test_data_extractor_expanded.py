"""Tests for expanded DataExtractor patterns."""
from app.services.data_extractor import (
    DataExtractor,
    KNOWN_DEVELOPERS,
    DUBAI_COMMUNITIES,
)


class TestExpandedPatterns:
    def setup_method(self):
        self.extractor = DataExtractor()

    def test_nshama_in_known_developers(self):
        assert any("Nshama" in d for d in KNOWN_DEVELOPERS)

    def test_town_square_in_communities(self):
        assert any("Town Square" in c for c in DUBAI_COMMUNITIES)

    def test_dubai_islands_in_communities(self):
        assert any("Dubai Islands" in c for c in DUBAI_COMMUNITIES)

    def test_extract_nshama_developer(self):
        text = "EVELYN on the Park by Nshama in Town Square, Dubai"
        result = self.extractor.extract_developer(text)
        assert result.value is not None
        assert "nshama" in result.value.lower()
        assert result.confidence >= 0.7

    def test_extract_town_square_community(self):
        text = "Located in Town Square, Dubai"
        result = self.extractor.extract_location(text)
        assert result.community is not None
        assert "Town Square" in result.community

    def test_extract_aed_price_with_comma(self):
        text = "Starting from AED 820,000"
        result = self.extractor.extract_prices(text)
        assert result.min_price == 820000

    def test_handover_date_extraction(self):
        text = "Expected handover: Q4 2027"
        result = self.extractor.extract_completion_date(text)
        assert result.value is not None
        assert "2027" in result.value

    def test_payment_plan_extraction(self):
        text = "Payment Plan: 80/20. 80% during construction, 20% on handover."
        result = self.extractor.extract_payment_plan(text)
        assert result.confidence > 0

    def test_aldar_developer(self):
        text = "A project by Aldar Properties in Saadiyat Island"
        result = self.extractor.extract_developer(text)
        assert result.value is not None
        assert "aldar" in result.value.lower()

    def test_full_extract_with_expanded_entities(self):
        """Full extract() method picks up new entities."""
        page_text_map = {
            1: "EVELYN on the Park by Nshama\nTown Square, Dubai\nAED 820,000",
            2: "Studio, 1BR, 2BR, 3BR\nHandover: Q4 2027",
        }
        result = self.extractor.extract(page_text_map)
        assert result.developer.value is not None
        assert result.location.community == "Town Square"
        assert result.location.emirate == "Dubai"
        assert result.prices.min_price == 820000
