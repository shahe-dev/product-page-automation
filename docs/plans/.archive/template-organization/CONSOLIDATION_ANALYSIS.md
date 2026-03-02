# Aggregator Template Consolidation Analysis

## Executive Summary

**22 templates analyzed. Only 10 are structurally unique. 12 are exact duplicates.**

Current state is highly inefficient - you're maintaining 22 separate sheets when you need at most 4-5 archetypes.

---

## Duplicate Groups Found

### Group A: English Marketing Template (8 identical sites)
| Site | Can Consolidate To |
|------|-------------------|
| bloom.living | **KEEP AS ARCHETYPE** |
| sharjah.residences.ae | Use bloom.living |
| luxury-collection.ae | Use bloom.living |
| dubai-harbour-property.ae | Use bloom.living |
| tilal-al-ghaf | Use bloom.living |
| dubaihills-property.ae | Use bloom.living |
| city-walk-property.ae | Use bloom.living |
| rashid-yachts-marina.ae | Use bloom.living |

### Group B: Russian-English Hybrid Template (5 identical sites)
| Site | Can Consolidate To |
|------|-------------------|
| saudi-estates.com | **KEEP AS ARCHETYPE** |
| dubaislands.ae | Use saudi-estates.com |
| dubaimaritime-city.ae | Use saudi-estates.com |
| sobha-central.ae | Use saudi-estates.com |
| difc-residences.ae | Use saudi-estates.com |

### Group C: Luxury Villas Variant (2 identical)
| Site | Can Consolidate To |
|------|-------------------|
| luxury-villas-dubai.ae | **KEEP AS ARCHETYPE** |
| luxury-villas-dubai.ae-2 | Use luxury-villas-dubai.ae |

---

## Proposed Archetype System

Based on structural analysis, I recommend **5 master archetypes**:

### Archetype 1: STANDARD (based on bloom.living)
**Use for:** Generic aggregator sites with standard layout
**Sections:** Hero, About, Features x2, Bullet Advantages, Amenities x5, Economic Appeal, Developer, Location
**Character limits:** Short paragraphs (120ch), medium paragraphs (300-350ch)
**Languages:** EN, RU, AR

**Sites using this archetype:** bloom.living, sharjah.residences.ae, luxury-collection.ae, dubai-harbour-property.ae, tilal-al-ghaf, dubaihills-property.ae, city-walk-property.ae, rashid-yachts-marina.ae, urbanvillas-dubaisouth.ae

### Archetype 2: STRUCTURED (based on saudi-estates.com)
**Use for:** Sites requiring detailed project passport/data tables
**Sections:** Hero with economic indicators, About, Project Passport (Developer, Location, Payment, Area, Type), Economic Appeal, Payment Plan details, Advantages, Amenities, Developer info, Location
**Character limits:** Detailed paragraphs (100-400ch)
**Languages:** EN, RU, AR (Russian-primary labels)

**Sites using this archetype:** saudi-estates.com, dubaislands.ae, dubaimaritime-city.ae, sobha-central.ae, difc-residences.ae

### Archetype 3: PREMIUM (based on capital.luxury)
**Use for:** High-end properties requiring comprehensive coverage
**Sections:** Full suite - Hero, About Area, Project Details, Economic Appeal, Payment Plans, Post-delivery support, Advantages, Amenities, Developer About, Location advantages, Social facilities, Education/Medicine, Culture, FAQ
**Character limits:** Variable, most detailed
**Languages:** EN, RU, AR

**Sites using this archetype:** capital.luxury, ras-al-khaimah-properties.ae

### Archetype 4: USP-FOCUSED (based on sobha-hartland)
**Use for:** Projects with strong unique selling points
**Sections:** Hero with USP bullets, About, Features, Advantages, Amenities, Economic Appeal, Developer, Location
**Difference from STANDARD:** Hero section emphasizes data-driven USPs

**Sites using this archetype:** sobha-hartland, the-valley-villas, dubai-creek-living.ae, luxury-villas-dubai.ae

### Archetype 5: MINIMAL (based on urban-luxury.penthouse.ae)
**Use for:** Simple, clean layouts focusing on essentials
**Sections:** Hero, About, Key details, Features with bullet points, Developer, Location
**Character limits:** Strict and short (30-50ch headings, 100-400ch text)
**Languages:** EN, RU, AR + EXAMPLE column

**Sites using this archetype:** urban-luxury.penthouse.ae

---

## Common Fields Across All Archetypes (Core Schema)

These fields appear in 80%+ of templates - they form your base schema:

| Field | Required | Notes |
|-------|----------|-------|
| Title (SEO) | Yes | 50-60 characters |
| Desc (SEO) | Yes | Max 156 characters |
| Slug | Yes | URL path |
| H1 | Yes | Project + Developer/Area, 50-70ch |
| Hero description | Yes | 70-120ch |
| Starting Price | Yes | AED + USD |
| Handover | Yes | Quarter + Year |
| Payment Plan | Yes | Summary |
| About heading | Yes | H2, 40-80ch |
| About paragraph | Yes | 150-400ch |
| Amenities | Yes | 3-5 items with titles + descriptions |
| Developer info | Yes | Name + short description |
| Location | Yes | Area name |

---

## Recommended Actions

### Immediate (This Week)
1. **Delete 12 duplicate sheets** - Keep only the archetype representatives
2. **Create master template registry** - Map each site to its archetype
3. **Update CSV** - Add archetype column to `Aggregators with project pages.csv`

### Short-term (Next Sprint)
4. **Build parameterized prompts** - One prompt per archetype, not per site
5. **Create archetype validation** - Ensure generated content matches structure
6. **Add site-specific overrides** - For character limit variations only

### Medium-term
7. **Reduce to 3 archetypes** - STANDARD, PREMIUM, MINIMAL (merge USP-FOCUSED into STANDARD with conditional)
8. **Automate archetype detection** - Based on site domain or first-time setup

---

## Efficiency Gains

| Metric | Current | Proposed | Improvement |
|--------|---------|----------|-------------|
| Templates to maintain | 22 | 5 | 77% reduction |
| Prompts needed | 22 | 5 | 77% reduction |
| QA test cases | 22+ | 5 | 77% reduction |
| Error surface area | High | Low | Significant |

---

## Open Questions

1. **Are the Russian-label templates intentional?** (saudi-estates.com group uses Russian field names)
2. **Is capital.luxury actually in use?** (Most complex template, unique)
3. **Should EXAMPLE column be standard?** (Only urban-luxury.penthouse.ae has it)

---

## Next Steps

1. Review this analysis and confirm archetype assignments
2. I can scrape the live project pages to validate that the templates match actual site structures
3. Create the master archetype sheets with proper documentation

*Generated: January 2026*
