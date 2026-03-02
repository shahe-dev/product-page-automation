"""
Data Extractor Service (DEV-EXTRACT-001)

Free-tier data extraction using regex pattern matching and text analysis.
Extracts structured project data fields from PDF markdown text without API calls.
This is Phase 3's first layer - outputs feed into DEV-STRUCT-001 for Claude structuring.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# UAE Emirates for location matching
UAE_EMIRATES = [
    "Dubai", "Abu Dhabi", "Sharjah", "Ajman",
    "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"
]

# Dubai Communities for location matching
DUBAI_COMMUNITIES = [
    "Downtown Dubai", "Dubai Marina", "JBR", "Jumeirah Beach Residence",
    "Palm Jumeirah", "Business Bay", "Dubai Hills Estate", "Arabian Ranches",
    "DAMAC Hills", "Dubai Creek Harbour", "Mohammed Bin Rashid City",
    "Jumeirah Village Circle", "JVC", "Dubai South", "Al Furjan",
    "Dubai Sports City", "Motor City", "Jumeirah Lake Towers", "JLT",
    "DIFC", "Dubai International Financial Centre", "Dubai Design District",
    "D3", "Meydan", "Dubai Land", "The Greens", "The Views", "Discovery Gardens",
    "Jumeirah Village Triangle", "JVT", "Dubai Marina Mall", "Emirates Hills",
    "Springs", "Meadows", "Lakes", "International City", "Silicon Oasis",
    "Dubai Silicon Oasis", "DSO", "Barsha Heights", "Tecom", "Media City",
    "Internet City", "Knowledge Village", "Academic City", "Dubai Healthcare City",
    "Town Square", "Expo City", "Dubai Islands", "Rashid Yachts & Marina",
    "City Walk", "La Mer", "Port de La Mer", "Bluewaters",
    "Dubai Harbour", "Emaar South", "Dubai Hills", "Villanova",
    "Mudon", "Remraam", "Al Reef", "Saadiyat Island",
    "Yas Island", "Al Reem Island", "MBR City",
    "Jumeirah Golf Estates", "Dubai Creek Residences",
    "Sobha Hartland", "The Valley", "Tilal Al Ghaf",
]

# Known Developers for validation
KNOWN_DEVELOPERS = [
    "Emaar", "DAMAC", "Nakheel", "Meraas", "Dubai Properties",
    "Sobha", "Azizi", "Omniyat", "Select Group", "Ellington",
    "Binghatti", "Danube", "Samana", "Vincitore", "MAG",
    "Deyaar", "Union Properties", "Tiger", "Gemini", "Mag Lifestyle",
    "Nshama", "Reportage", "Aldar", "Eagle Hills", "Bloom",
    "Arada", "Majid Al Futtaim", "Al Habtoor", "IRTH", "Wasl",
    "Dubai Holding", "Meydan", "Tilal Al Ghaf", "RAK Properties",
    "Palma Holding", "Prestige One", "Object 1", "Imtiaz",
]

# Property Types
PROPERTY_TYPES = [
    "Apartment", "Villa", "Townhouse", "Penthouse", "Studio",
    "Duplex", "Triplex", "Residential", "Commercial", "Mixed Use"
]


@dataclass
class FieldResult:
    """Result for a single extracted field."""
    value: Optional[str]
    confidence: float  # 0.0-1.0
    source: str  # "regex", "heading", "context"
    page: Optional[int] = None


@dataclass
class LocationResult:
    """Extracted location information."""
    emirate: Optional[str]
    community: Optional[str]
    sub_community: Optional[str]
    full_location: Optional[str]
    confidence: float


@dataclass
class PriceResult:
    """Extracted price information."""
    min_price: Optional[int]
    max_price: Optional[int]
    currency: str = "AED"
    price_per_sqft: Optional[int] = None
    confidence: float = 0.0


@dataclass
class PaymentPlanResult:
    """Extracted payment plan information."""
    down_payment_pct: Optional[float]
    during_construction_pct: Optional[float]
    on_handover_pct: Optional[float]
    post_handover_pct: Optional[float]
    raw_text: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ExtractionOutput:
    """Complete output from data extraction."""
    project_name: FieldResult
    developer: FieldResult
    location: LocationResult
    prices: PriceResult
    bedrooms: list[str]
    completion_date: FieldResult
    amenities: list[str]
    payment_plan: PaymentPlanResult
    property_type: FieldResult
    total_pages: int
    full_text: str
    extraction_method: str = "regex"
    errors: list[str] = field(default_factory=list)


class DataExtractor:
    """
    Extracts structured project data from PDF markdown text using regex patterns.

    This is the free-tier extraction layer that doesn't make API calls.
    Results feed into Claude-based structuring for refinement.
    """

    def __init__(self):
        """Initialize the data extractor."""
        pass

    # Maximum characters to process (prevents excessive CPU on very large PDFs)
    MAX_EXTRACTION_CHARS = 500_000

    def extract(self, page_text_map: dict[int, str]) -> ExtractionOutput:
        """
        Extract structured data from page text map.

        Args:
            page_text_map: Dict mapping page numbers to markdown text.

        Returns:
            ExtractionOutput with all extracted fields.
        """
        # Combine all pages into full document text
        full_text = self._combine_pages(page_text_map)
        total_pages = len(page_text_map)

        # Truncate to prevent excessive CPU usage on very large PDFs
        if len(full_text) > self.MAX_EXTRACTION_CHARS:
            logger.warning(
                "Text exceeds %d chars (%d actual), truncating for extraction",
                self.MAX_EXTRACTION_CHARS, len(full_text)
            )
            full_text = full_text[:self.MAX_EXTRACTION_CHARS]

        logger.info("Starting data extraction on %d pages", total_pages)

        # Run all field extractors
        project_name = self.extract_project_name(full_text)
        developer = self.extract_developer(full_text)
        location = self.extract_location(full_text)
        prices = self.extract_prices(full_text)
        bedrooms = self.extract_bedrooms(full_text)
        completion_date = self.extract_completion_date(full_text)
        amenities = self.extract_amenities(full_text)
        payment_plan = self.extract_payment_plan(full_text)
        property_type = self.extract_property_type(full_text)

        errors = []
        if project_name.confidence < 0.5:
            errors.append("Low confidence in project name extraction")
        if developer.confidence < 0.5:
            errors.append("Low confidence in developer extraction")

        logger.info(
            "Extraction complete: project=%s, developer=%s, location=%s",
            project_name.value,
            developer.value,
            location.full_location,
        )

        return ExtractionOutput(
            project_name=project_name,
            developer=developer,
            location=location,
            prices=prices,
            bedrooms=bedrooms,
            completion_date=completion_date,
            amenities=amenities,
            payment_plan=payment_plan,
            property_type=property_type,
            total_pages=total_pages,
            full_text=full_text,
            extraction_method="regex",
            errors=errors,
        )

    def _combine_pages(self, page_text_map: dict[int, str]) -> str:
        """Combine all pages into a single text string."""
        sorted_pages = sorted(page_text_map.keys())
        return "\n\n".join(page_text_map[page] for page in sorted_pages)

    def extract_project_name(self, text: str) -> FieldResult:
        """
        Extract project name from text.

        Looks for:
        - H1 headers (# Project Name)
        - All-caps prominent text on cover pages
        - Bold markdown text
        - Title-case prominent text
        - Real estate naming patterns
        """
        lines = text.split("\n")

        # Strategy 1: Look for H1 headers at the start
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if line.startswith("# "):
                name = line[2:].strip()
                # Filter out generic headers
                if name.lower() not in ["overview", "about", "project", "details"]:
                    return FieldResult(
                        value=name,
                        confidence=0.9,
                        source="heading",
                        page=1
                    )

        # Strategy 2: Look for all-caps text in first 20 lines (common for brochure covers)
        # Matches: "GREENCREST", "THE CREST", "GOLF VIEWS"
        generic_caps = {
            "overview", "about", "project", "details", "welcome", "introduction",
            "contents", "index", "dubai", "abu dhabi", "sharjah", "uae",
            "bedroom", "amenities", "features", "floor", "plan", "location",
        }
        for i, line in enumerate(lines[:20]):
            stripped = line.strip()
            # Check if line is mostly uppercase (at least 70% uppercase letters)
            if len(stripped) >= 3:
                alpha_chars = [c for c in stripped if c.isalpha()]
                if alpha_chars:
                    upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                    if upper_ratio >= 0.7:
                        # Clean up the name
                        name = stripped.strip("*#_ ")
                        # Skip generic headers
                        if name.lower() not in generic_caps and len(name) >= 3:
                            # Title-case for display
                            return FieldResult(
                                value=name.title(),
                                confidence=0.85,
                                source="allcaps",
                                page=1
                            )

        # Strategy 3: Look for bold markdown text in first 15 lines
        # Matches: **Project Name**, __Project Name__
        for i, line in enumerate(lines[:15]):
            bold_match = re.search(r"\*\*([^*]+)\*\*|__([^_]+)__", line)
            if bold_match:
                name = (bold_match.group(1) or bold_match.group(2)).strip()
                if name.lower() not in generic_caps and len(name) >= 3:
                    return FieldResult(
                        value=name,
                        confidence=0.85,
                        source="bold",
                        page=1
                    )

        # Strategy 4: Look for "Project:" or "Project Name:" patterns
        pattern = r"(?:Project\s*(?:Name)?|Development)\s*[:\-]\s*([A-Z][A-Za-z\s\-&']+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            name = matches[0].strip()
            return FieldResult(
                value=name,
                confidence=0.8,
                source="regex",
            )

        # Strategy 5: Look for title-case phrases (likely project names)
        # Pattern: "The [Name] by [Developer]" or just "[Name]"
        pattern = r"\b(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\s+(?:by|at|in)\b"
        matches = re.findall(pattern, text)
        if matches:
            name = matches[0].strip()
            return FieldResult(
                value=name,
                confidence=0.7,
                source="regex",
            )

        return FieldResult(
            value=None,
            confidence=0.0,
            source="none",
        )

    def extract_developer(self, text: str) -> FieldResult:
        """
        Extract developer name from text.

        Patterns:
        - "by {Developer}"
        - "Developer: {name}"
        - "Developed by {name}"
        """
        # Strategy 1: "by Developer" pattern
        pattern = r"\bby\s+([A-Z][A-Za-z\s&]+(?:Properties|Group|Developments)?)"
        matches = re.findall(pattern, text)
        for match in matches:
            dev = match.strip()
            # Check if it's a known developer
            for known in KNOWN_DEVELOPERS:
                if known.lower() in dev.lower():
                    return FieldResult(
                        value=known,
                        confidence=0.9,
                        source="regex",
                    )
            # Return first match even if not in known list
            if len(dev) > 3:
                return FieldResult(
                    value=dev,
                    confidence=0.6,
                    source="regex",
                )

        # Strategy 2: "Developer:" pattern
        pattern = r"Developer\s*[:\-]\s*([A-Z][A-Za-z\s&]+?)(?:\n|$|(?:Properties|Group|Developments))"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            dev = matches[0].strip()
            # Check if it's a known developer for better confidence
            for known in KNOWN_DEVELOPERS:
                if known.lower() in dev.lower():
                    return FieldResult(
                        value=known,
                        confidence=0.9,
                        source="regex",
                    )
            return FieldResult(
                value=dev,
                confidence=0.6,
                source="regex",
            )

        # Strategy 3: "Developed by" pattern
        pattern = r"Developed\s+by\s+([A-Z][A-Za-z\s&]+(?:Properties|Group|Developments)?)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            dev = matches[0].strip()
            confidence = 0.7 if any(k.lower() in dev.lower() for k in KNOWN_DEVELOPERS) else 0.5
            return FieldResult(
                value=dev,
                confidence=confidence,
                source="regex",
            )

        return FieldResult(
            value=None,
            confidence=0.0,
            source="none",
        )

    def extract_location(self, text: str) -> LocationResult:
        """
        Extract location information (emirate, community, sub-community).
        """
        emirate = None
        community = None
        sub_community = None
        confidence = 0.0

        # Extract emirate
        for em in UAE_EMIRATES:
            pattern = r"\b" + re.escape(em) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                emirate = em
                confidence = 0.9
                break

        # Extract community (Dubai-specific for now)
        if emirate == "Dubai":
            for comm in DUBAI_COMMUNITIES:
                pattern = r"\b" + re.escape(comm) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    community = comm
                    confidence = 0.9
                    break

        # Build full location string
        parts = [p for p in [community, emirate] if p]
        full_location = ", ".join(parts) if parts else None

        return LocationResult(
            emirate=emirate,
            community=community,
            sub_community=sub_community,
            full_location=full_location,
            confidence=confidence,
        )

    def extract_prices(self, text: str) -> PriceResult:
        """
        Extract price information.

        Patterns:
        - "AED 1,200,000"
        - "Starting from AED 850K"
        - "Price: AED 1.2M"
        """
        prices = []

        # Pattern 1: AED with numbers (with commas or dots)
        pattern = r"AED\s*([0-9,\.]+)\s*(M(?:illion)?|K|thousand)?"
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match, suffix in matches:
            # Clean up the number - handle decimal notation properly
            num_str = match.replace(",", "")
            try:
                value = float(num_str)
                # Apply multiplier if present
                if suffix and suffix.upper().startswith("M"):
                    value *= 1_000_000
                elif suffix and suffix.upper().startswith("K"):
                    value *= 1_000
                prices.append(int(value))
            except ValueError:
                continue

        # Pattern 2: Numbers followed by AED
        pattern = r"([0-9,\.]+)\s*(?:M(?:illion)?|K)?\s*AED"
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match in matches:
            num_str = match.replace(",", "")
            try:
                value = float(num_str)
                # Check for multiplier
                full_match = re.search(
                    re.escape(match) + r"\s*(M(?:illion)?|K)?\s*AED",
                    text,
                    re.IGNORECASE
                )
                if full_match:
                    suffix = full_match.group(1)
                    if suffix and suffix.upper().startswith("M"):
                        value *= 1_000_000
                    elif suffix and suffix.upper().startswith("K"):
                        value *= 1_000
                prices.append(int(value))
            except ValueError:
                continue

        if not prices:
            return PriceResult(
                min_price=None,
                max_price=None,
                confidence=0.0,
            )

        # Remove outliers (prices too low or too high)
        prices = [p for p in prices if 100_000 <= p <= 100_000_000]

        if not prices:
            return PriceResult(
                min_price=None,
                max_price=None,
                confidence=0.0,
            )

        min_price = min(prices)
        max_price = max(prices)
        confidence = 0.8 if len(prices) >= 2 else 0.6

        return PriceResult(
            min_price=min_price,
            max_price=max_price if max_price != min_price else None,
            currency="AED",
            confidence=confidence,
        )

    def extract_bedrooms(self, text: str) -> list[str]:
        """
        Extract bedroom configurations.

        Patterns:
        - "1BR", "2 Bedroom", "Studio", "3 B/R"
        """
        bedrooms = set()

        # Pattern 1: "Studio"
        if re.search(r"\bStudio\b", text, re.IGNORECASE):
            bedrooms.add("Studio")

        # Pattern 2: "1BR", "2BR", etc.
        matches = re.findall(r"\b([1-9])\s*BR\b", text, re.IGNORECASE)
        for match in matches:
            bedrooms.add(f"{match}BR")

        # Pattern 3: "1 Bedroom", "2 Bedrooms"
        matches = re.findall(r"\b([1-9])\s*Bedroom", text, re.IGNORECASE)
        for match in matches:
            bedrooms.add(f"{match}BR")

        # Pattern 4: "1 B/R", "2 B/R"
        matches = re.findall(r"\b([1-9])\s*B\s*/\s*R\b", text, re.IGNORECASE)
        for match in matches:
            bedrooms.add(f"{match}BR")

        # Sort: Studio first, then by number
        sorted_bedrooms = []
        if "Studio" in bedrooms:
            sorted_bedrooms.append("Studio")

        numbered = sorted([b for b in bedrooms if b != "Studio"], key=lambda x: int(x[0]))
        sorted_bedrooms.extend(numbered)

        return sorted_bedrooms

    def extract_completion_date(self, text: str) -> FieldResult:
        """
        Extract completion/handover date.

        Patterns:
        - "Q4 2026"
        - "Handover: 2027"
        - "Completion Date: March 2028"
        """
        # Pattern 1: Quarter format (Q1 2026, Q4 2027)
        pattern = r"(?:Q[1-4]\s*20\d{2})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return FieldResult(
                value=matches[0],
                confidence=0.9,
                source="regex",
            )

        # Pattern 2: Handover/Completion followed by date
        pattern = r"(?:Handover|Completion(?:\s+Date)?|Delivery)\s*[:\-]\s*((?:Q[1-4]\s*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[a-z]*\s*20\d{2})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            date = matches[0].strip()
            return FieldResult(
                value=date,
                confidence=0.8,
                source="regex",
            )

        # Pattern 3: Just year, but only near completion-related keywords
        # and only future years to avoid matching copyright years (P3-14)
        from datetime import datetime, timezone
        current_year = datetime.now(timezone.utc).year
        pattern = r"(?:(?:complet|handover|deliver|ready|expect|estimat)\w*\s.{0,30})?\b(20[2-3][0-9])\b"
        matches = re.findall(pattern, text, re.IGNORECASE)
        # Filter to current year or later
        future_matches = [m for m in matches if int(m) >= current_year]
        if future_matches:
            return FieldResult(
                value=future_matches[0],
                confidence=0.6,
                source="regex",
            )

        return FieldResult(
            value=None,
            confidence=0.0,
            source="none",
        )

    def extract_amenities(self, text: str) -> list[str]:
        """
        Extract amenities from text.

        Looks for common amenities in bullet lists and descriptions.
        """
        amenities = set()

        # Common amenities to look for
        common_amenities = [
            "Swimming Pool", "Pool", "Gym", "Fitness Center", "Fitness Centre",
            "Parking", "Covered Parking", "Security", "24/7 Security",
            "Concierge", "Kids Play Area", "Playground", "Children's Play Area",
            "Spa", "Sauna", "Steam Room", "Jacuzzi", "BBQ Area",
            "Retail", "Retail Outlets", "Restaurant", "Cafe",
            "Garden", "Landscaped Gardens", "Green Spaces", "Park",
            "Tennis Court", "Basketball Court", "Sports Facilities",
            "Business Center", "Meeting Rooms", "Co-working Space",
            "Yoga Studio", "Multipurpose Hall", "Community Center",
            "Pet Park", "Dog Park", "Cycling Track", "Jogging Track",
            "Smart Home", "Central AC", "Central A/C", "Balcony", "Terrace"
        ]

        for amenity in common_amenities:
            pattern = r"\b" + re.escape(amenity) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                # Normalize the amenity name
                amenities.add(amenity)

        # Remove duplicates (e.g., "Pool" if "Swimming Pool" is present)
        if "Swimming Pool" in amenities:
            amenities.discard("Pool")
        if "Fitness Center" in amenities or "Fitness Centre" in amenities:
            amenities.discard("Gym")

        return sorted(list(amenities))

    def extract_payment_plan(self, text: str) -> PaymentPlanResult:
        """
        Extract payment plan information.

        Patterns:
        - "10% down payment"
        - "60% during construction"
        - "30% on handover"
        """
        down_payment = None
        during_construction = None
        on_handover = None
        post_handover = None
        raw_text = None

        # Look for payment plan section
        payment_section_pattern = r"(Payment\s+Plan[:\s].*?)(?=\n\n|\Z)"
        section_match = re.search(payment_section_pattern, text, re.IGNORECASE | re.DOTALL)
        if section_match:
            raw_text = section_match.group(1)[:500]  # Limit to 500 chars

        # Extract percentages
        # Pattern 1: Down payment
        pattern = r"(\d+)%?\s*(?:down\s*payment|booking|reservation)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            down_payment = float(matches[0])

        # Pattern 2: During construction
        pattern = r"(\d+)%?\s*(?:during\s*construction|construction\s*period)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            during_construction = float(matches[0])

        # Pattern 3: On handover (more specific to avoid matching "on completion" alone)
        pattern = r"(\d+)%?\s*(?:on\s*handover|on\s*completion)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            on_handover = float(matches[0])

        # Pattern 4: Post handover
        pattern = r"(\d+)%?\s*(?:post\s*handover|after\s*handover|post[-\s]completion)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            post_handover = float(matches[0])

        # Calculate confidence based on how many components we found
        components_found = sum([
            down_payment is not None,
            during_construction is not None,
            on_handover is not None,
        ])
        confidence = components_found * 0.3  # 0.3 per component found

        return PaymentPlanResult(
            down_payment_pct=down_payment,
            during_construction_pct=during_construction,
            on_handover_pct=on_handover,
            post_handover_pct=post_handover,
            raw_text=raw_text,
            confidence=confidence,
        )

    def extract_property_type(self, text: str) -> FieldResult:
        """
        Extract property type.

        Types: Apartment, Villa, Townhouse, Penthouse, etc.
        """
        for prop_type in PROPERTY_TYPES:
            pattern = r"\b" + re.escape(prop_type) + r"s?\b"
            if re.search(pattern, text, re.IGNORECASE):
                return FieldResult(
                    value=prop_type,
                    confidence=0.8,
                    source="regex",
                )

        return FieldResult(
            value=None,
            confidence=0.0,
            source="none",
        )

    def get_page_context(
        self,
        page_text_map: dict[int, str],
        page_num: int,
        window: int = 2
    ) -> str:
        """
        Extract text from pages surrounding a specific page.

        Used by floor plan extractor for text cross-referencing.

        Args:
            page_text_map: Dict mapping page numbers to text.
            page_num: The target page number (1-indexed).
            window: Number of pages before and after to include.

        Returns:
            Combined text from surrounding pages, or empty string if map is empty.
        """
        if not page_text_map:
            return ""

        start_page = max(1, page_num - window)
        end_page = min(max(page_text_map.keys()), page_num + window)

        context_pages = range(start_page, end_page + 1)
        context_text = []

        for p in context_pages:
            if p in page_text_map:
                context_text.append(f"--- Page {p} ---")
                context_text.append(page_text_map[p])

        return "\n\n".join(context_text)
