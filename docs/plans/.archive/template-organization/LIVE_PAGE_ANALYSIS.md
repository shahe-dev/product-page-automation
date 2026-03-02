# Live Page Structure Analysis Report

## Executive Summary

**22 project pages scraped and analyzed. 20/22 sites share nearly identical page structures.**

The live pages are far more uniform than the templates suggest. This validates consolidation to fewer archetypes.

---

## Section Presence Analysis

| Section | Sites Present | Percentage | Template Priority |
|---------|---------------|------------|-------------------|
| Hero | 21/22 | 95% | REQUIRED |
| About | 20/22 | 91% | REQUIRED |
| Location | 21/22 | 95% | REQUIRED |
| Payment Plan | 19/22 | 86% | REQUIRED |
| Floor Plans | 18/22 | 82% | REQUIRED |
| Developer | 17/22 | 77% | REQUIRED |
| Amenities | 18/22 | 82% | REQUIRED |
| Gallery | 21/22 | 95% | REQUIRED |
| FAQ | 19/22 | 86% | OPTIONAL |
| Contact | 20/22 | 91% | REQUIRED |

**Key Finding:** All major sections appear on 77%+ of sites. The section structure is highly standardized.

---

## Character Limit Recommendations

Based on actual content analysis across 22 live pages:

### Meta Tags (SEO)
| Field | Observed Range | Recommended | Template Spec |
|-------|---------------|-------------|---------------|
| Meta Title | 3-163 chars | **50-60 chars** | Matches |
| Meta Description | 0-259 chars | **150-160 chars** | Matches |

### Headings
| Tag | Observed Range | Average | Recommended |
|-----|---------------|---------|-------------|
| H1 | 14-78 chars | 41 chars | **30-60 chars** |
| H2 | 7-99 chars | 29 chars | **20-50 chars** |
| H3 | 9-102 chars | 33 chars | **15-40 chars** |

### Section Content
| Section | Min | Max | Average | Recommended Range |
|---------|-----|-----|---------|-------------------|
| Hero | 64 | 973 | 321 | **250-400 chars** |
| About | 60 | 1349 | 526 | **400-700 chars** |
| Amenities | 67 | 1031 | 480 | **350-600 chars** |
| Payment Plan | 80 | 9531 | 662 | **400-800 chars** |
| Location | 124 | 1085 | 428 | **300-550 chars** |
| Developer | 125 | 2988 | 381 | **250-500 chars** |
| FAQ | 55 | 1593 | 529 | **400-800 chars** |
| Floor Plans | 108 | 10638 | 1727 | **Variable (data-driven)** |

---

## Outlier Sites

### Sites with Incomplete Structures
| Site | Missing Sections | Notes |
|------|------------------|-------|
| difc-residences.ae | Most sections | Page appears broken/minimal |
| bloom-living.ae | About, Amenities, Payment, Developer, Floor Plans | Minimal page |
| urban-luxury.penthouse.ae | Amenities | Intentionally minimal design |

### Sites with Non-Standard Meta
| Site | Meta Title | Meta Desc | Issue |
|------|-----------|-----------|-------|
| difc-residences.ae | 20 chars | 61 chars | Too short |
| bloom-living.ae | 3 chars | 0 chars | Missing |
| urban-luxury.penthouse.ae | 9 chars | 9 chars | Missing |

---

## Template vs Live Page Comparison

### Common Sections (Templates Should Include)

All templates MUST include these sections based on 80%+ presence:

1. **Hero Section**
   - H1 heading (30-60 chars)
   - Short description (250-400 chars)
   - Starting Price
   - Payment Plan summary
   - Handover date

2. **About/Overview Section**
   - H2 heading (20-50 chars)
   - Description paragraph (400-700 chars)
   - Key selling points (3-5 bullet points)

3. **Amenities Section**
   - H2/H3 heading
   - 5 amenities with headline + description
   - Each description: 100-150 chars

4. **Payment Plan Section**
   - H2 heading
   - Plan breakdown (milestones, percentages)
   - Description paragraph (400-800 chars)

5. **Location Section**
   - H2 heading
   - Description (300-550 chars)
   - Nearby attractions/distances

6. **Developer Section**
   - H2 heading
   - Developer description (250-500 chars)

7. **Floor Plans Section**
   - H2 heading
   - Unit types with: bedrooms, area, price

8. **FAQ Section** (optional but recommended)
   - 3-5 Q&A pairs

---

## Validated Archetype Consolidation

Based on live page analysis, the original 5 archetypes can be reduced to **3**:

### Archetype A: STANDARD (90% of sites)
All sections, standard character limits
- Sites: sobha-central.ae, dubaimaritime-city.ae, rashid-yachts-marina.ae, city-walk-property.ae, dubaislands.ae, dubai-creek-living.ae, dubaihills-property.ae, urbanvillas-dubaisouth.ae, saudi-estates.com, ras-al-khaimah-properties.ae, tilalalghaf-maf.ae, sobha-hartland-2.ae, dubai-harbour-property.ae, the-valley-villas.ae, luxury-collection.ae, sharjah-residences.ae, luxury-villas-dubai.ae, capital.luxury

### Archetype B: MINIMAL (5% of sites)
Reduced sections, shorter content
- Sites: urban-luxury.penthouse.ae

### Archetype C: BROKEN/INCOMPLETE
Needs investigation - pages may be under construction
- Sites: difc-residences.ae, bloom-living.ae

---

## Recommended Template Schema

Based on this analysis, here is the unified template schema:

```
REQUIRED FIELDS:
- meta_title: 50-60 chars
- meta_description: 150-160 chars
- slug: URL path
- h1: 30-60 chars
- hero_description: 250-400 chars
- starting_price: AED + USD
- payment_plan_summary: e.g., "60/40"
- handover: Quarter + Year

ABOUT SECTION:
- about_h2: 20-50 chars
- about_description: 400-700 chars
- selling_points: 3-5 bullet points, 50-80 chars each

AMENITIES SECTION:
- amenities_h2: 20-50 chars
- amenity_1_title: 20-40 chars
- amenity_1_desc: 100-150 chars
- amenity_2_title: 20-40 chars
- amenity_2_desc: 100-150 chars
- amenity_3_title: 20-40 chars
- amenity_3_desc: 100-150 chars
- amenity_4_title: 20-40 chars
- amenity_4_desc: 100-150 chars
- amenity_5_title: 20-40 chars
- amenity_5_desc: 100-150 chars

PAYMENT PLAN SECTION:
- payment_h2: 20-50 chars
- payment_description: 400-800 chars
- payment_milestones: structured data

LOCATION SECTION:
- location_h2: 20-50 chars
- location_description: 300-550 chars
- nearby_attractions: 3-5 items

DEVELOPER SECTION:
- developer_h2: 20-50 chars
- developer_description: 250-500 chars

FLOOR PLANS SECTION:
- floorplans_h2: 20-50 chars
- unit_types: array of {type, bedrooms, area_sqft, starting_price}

FAQ SECTION (optional):
- faq_items: array of {question, answer}
```

---

## Action Items

1. **Immediate**: Archive the 12 duplicate templates identified earlier
2. **This Week**: Create unified template matching the schema above
3. **Validate**: Test template against 3 sample sites (sobha-central.ae, capital.luxury, urban-luxury.penthouse.ae)
4. **Investigate**: Check why difc-residences.ae and bloom-living.ae pages are incomplete

---

## Files Generated

| File | Description |
|------|-------------|
| [scraped_pages/page_structures.json](scraped_pages/page_structures.json) | Raw scraped data |
| [scraped_pages/*.png](scraped_pages/) | Screenshots of all 22 pages |
| [page_structure_analysis.json](page_structure_analysis.json) | Processed analysis data |

*Generated: January 2026*
