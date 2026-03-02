"""Fixtures for floor plan extraction quality tests.

Provides session-scoped caches for PDF bytes, ground truth JSON,
and page text maps. All tests in this directory use real PDF brochures
from the 'sample brochures 2/' folder at the project root.
"""
import json
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
BROCHURES_DIR = PROJECT_ROOT / "floor-plan-tool" / "sample brochures 2"
GROUND_TRUTH_DIR = pathlib.Path(__file__).resolve().parent / "ground_truth"

BROCHURE_FILES = {
    # -- Original 5 (have verified ground truth) --
    "evelyn": "EVELYN Brochure Final.pdf",
    "expo_valley": "Expo_Valley_Views_Brochure_Ghadeer.pdf",
    "hilton": "Hilton Residences Brochure.pdf",
    "novayas": "NOVAYAS Brochure.pdf",
    "sobha_eden": "Sobha Central Brochure - The Eden.pdf",
    # -- Expanded corpus (29 additional brochures) --
    "artistry_one": "Artistry One Residences.pdf",
    "avarra_palace": "AVARRA_BY_PALACE_FLOORPLANS_.pdf",
    "bashayer": "Bashayer Floor Plans.pdf",
    "bella_passo": "BELLA by Passo_Floor Plans_Collections_and_Penthouses_and_mansions.pdf",
    "crestlane_4": "City Walk Crestlane 4 Floor Plans.pdf",
    "crestlane_5": "City Walk Crestlane 5 Floor Plans.pdf",
    "expo_valley_fp": "Expo_Valley_Views_Floor_Plans_Ghadeer.pdf",
    "pinnacle_sobha": "Floor & Unit Plans - The Pinnacle at Sobha Central.pdf",
    "wedyan_canal": "Floor plans - Wedyan The Canal by Al Ghurair Collection.pdf",
    "helvetia_marine": "FLOOR PLANS & UNIT LAYOUTS Helvetia Marine by DHG.pdf",
    "helvetia_verde": "FLOOR PLANS and UNIT LAYOUTS Helvetia Verde by DHG.pdf",
    "hado_beyond": "Floor plans-Hado by Beyond-Tower A_compressed.pdf",
    "golf_terrace": "Golf Terrace Residences_Sales Deck.pdf",
    "haus_tenet": "Haus of Tenet Brochure Digital.pdf",
    "inaura": "INAURA_DOWNTOWN-DUBAI_BROCHURE.pdf",
    "cedarwood": "JGE_CEDARWOOD_ESTATES_FLOOR_PLANS 2.pdf",
    "mareva": "MAREVA_THE_OASIS_FLOOR_PLANS.pdf",
    "mareva2": "MAREVA2_THE_OASIS_FLOOR_PLANS.pdf",
    "olive_farms": "Olive Farms FP.pdf",
    "palm_beach": "Palm Jebel Ali-The Beach Collection Floor Plans.pdf",
    "palmiera": "PALMIERA-COLLECTIVE_TO_FLOORPLAN.pdf",
    "sheraton": "Sheraton Floor Plan_compressed.pdf",
    "brooks_sanctuary": "THE BROOKS AT SOBHA SANCTUARY BROCHURE & FLOORS .pdf",
    "greens_sanctuary": "THE GREENS AT SOBHA SANCTUARY BROCHURE & FLOORS.pdf",
    "grove_sanctuary": "THE GROVE AT SOBHA SANCTUARY BROCHURE & FLOORS.pdf",
    "difc_residences": "The Residences By DIFC Floor Plates.pdf",
    "heights_fp": "THE_HEIGHTS_FLOOR_PLANS.pdf",
    "heights_fp_2": "THE_HEIGHTS_FLOOR_PLANS (1).pdf",
    "lamborghini": "Tonino Lamborghini Residences - FP.pdf",
}

ALL_KEYS = list(BROCHURE_FILES.keys())
# "hilton" is 117MB and takes 10+ min -- keep it in a slow tier
FAST_KEYS = [k for k in ALL_KEYS if k != "hilton"]
# Original 5 with verified ground truth
VERIFIED_KEYS = ["evelyn", "expo_valley", "hilton", "novayas", "sobha_eden"]


def _skip_if_missing(brochure_key: str):
    """Skip test if brochure PDF is not on disk."""
    path = BROCHURES_DIR / BROCHURE_FILES[brochure_key]
    if not path.exists():
        pytest.skip(f"Brochure not found: {path}")


@pytest.fixture(scope="session")
def pdf_bytes_cache():
    """Session-scoped cache: read each PDF from disk only once."""
    cache = {}

    def _get(key: str) -> bytes:
        _skip_if_missing(key)
        if key not in cache:
            cache[key] = (BROCHURES_DIR / BROCHURE_FILES[key]).read_bytes()
        return cache[key]

    return _get


@pytest.fixture(scope="session")
def ground_truth_cache():
    """Session-scoped cache for ground truth JSON files."""
    cache = {}

    def _get(key: str) -> dict:
        if key not in cache:
            path = GROUND_TRUTH_DIR / f"{key}.json"
            if not path.exists():
                pytest.skip(f"Ground truth not found: {path}")
            cache[key] = json.loads(path.read_text(encoding="utf-8"))
        return cache[key]

    return _get


@pytest.fixture(scope="session")
def page_text_cache(pdf_bytes_cache):
    """Extract page text via PyMuPDF directly (fast, no page rendering)."""
    import fitz

    cache = {}

    def _get(key: str) -> dict[int, str]:
        if key not in cache:
            pdf_bytes = pdf_bytes_cache(key)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_map = {}
            for i in range(len(doc)):
                text = doc[i].get_text("text").strip()
                if text:
                    text_map[i + 1] = text  # 1-indexed page numbers
            doc.close()
            cache[key] = text_map
        return cache[key]

    return _get
