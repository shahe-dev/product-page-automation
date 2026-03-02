# Agent Brief: DEV-PROJDETAIL-001

**Agent ID:** DEV-PROJDETAIL-001
**Agent Name:** Project Detail Agent
**Type:** Development
**Phase:** 4 - Frontend
**Context Budget:** 55,000 tokens

---

## Mission

Implement project detail page with image gallery, floor plan viewer, and property data display.

---

## Documentation to Read

### Primary
1. `docs/03-frontend/PAGE_SPECIFICATIONS.md` - Project detail spec
2. `docs/02-modules/PROJECT_DATABASE.md` - Project data structure

---

## Dependencies

**Upstream:** DEV-DASHBOARD-001
**Downstream:** DEV-QAPAGE-001

---

## Outputs

### `frontend/src/pages/ProjectDetailPage.tsx`
### `frontend/src/components/projects/ProjectDetail.tsx`
### `frontend/src/components/projects/ImageGallery.tsx`
### `frontend/src/components/projects/FloorPlanViewer.tsx`

---

## Acceptance Criteria

1. **Project Header:**
   - Project name and developer
   - Status badge with actions
   - Quick action buttons
   - Breadcrumb navigation

2. **Image Gallery:**
   - Grid view of all images
   - Category tabs (interior, exterior, amenity, logo)
   - Lightbox for full view
   - Image download option
   - Image metadata display

3. **Floor Plan Viewer:**
   - Floor plan images display
   - Unit type labels
   - Bedroom/bathroom count
   - Square footage
   - Zoom functionality

4. **Property Data:**
   - Core details section
   - Price range display
   - Payment plan breakdown
   - Amenities list
   - Location information
   - Edit inline (if authorized)

5. **Content Preview:**
   - Generated content display
   - QA scores per field
   - Link to Google Sheet
   - Regeneration options

---

## QA Pair: QA-PROJDETAIL-001

---

**Begin execution.**
