# Agent Brief: QA-STRUCT-001

**Agent ID:** QA-STRUCT-001
**Agent Name:** Data Structurer QA
**Type:** QA
**Phase:** 3 - Content Generation
**Paired Dev Agent:** DEV-STRUCT-001

---

## Validation Checklist

- [ ] All required fields extracted
- [ ] Confidence scores calculated correctly
- [ ] Low confidence fields flagged
- [ ] Missing fields tracked
- [ ] Data types validated
- [ ] Price ranges make sense
- [ ] Dates parsed correctly
- [ ] Amenities categorized properly
- [ ] Cost per extraction within budget
- [ ] Token usage tracked

---

## Test Cases

1. Complete brochure with all fields
2. Brochure missing price information
3. Brochure with ambiguous location
4. Brochure with multiple property types
5. Brochure with complex payment plan
6. Poor quality markdown input
7. Non-English content sections
8. Very long brochure (token limits)

---

## Accuracy Validation

- Compare extracted data against manual extraction
- Verify confidence scores match actual accuracy
- Check for hallucinated data

---

## Quality Metrics

- Field accuracy: >90%
- Confidence calibration: actual accuracy within 10% of confidence
- Cost per extraction: <$0.05

---

**Begin review.**
