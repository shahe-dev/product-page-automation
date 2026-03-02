# Agent Brief: QA-WORKFLOW-001

**Agent ID:** QA-WORKFLOW-001
**Agent Name:** Workflow Page QA
**Type:** QA
**Phase:** 4 - Frontend
**Paired Dev Agent:** DEV-WORKFLOW-001

---

## Validation Checklist

- [ ] Kanban board renders correctly
- [ ] All status columns display
- [ ] Cards show correct info
- [ ] Drag-and-drop works
- [ ] Stage transitions follow rules
- [ ] Invalid transitions blocked
- [ ] Assignments work
- [ ] Comments save
- [ ] Priority setting works
- [ ] History tracking accurate

---

## Test Cases

1. Load Kanban board
2. Drag card to valid column
3. Attempt invalid transition (blocked)
4. Assign to user
5. Add comment to card
6. Set card priority
7. View card history
8. Filter by assignee
9. Filter by priority
10. Multiple users editing
11. Column overflow scrolling
12. Mobile view

---

## Workflow Rule Tests

- Draft to Pending requires QA score
- Only Marketing Manager can approve
- Only Publisher can publish
- Cannot skip stages
- Archive from any stage

---

## Accessibility Tests

- Drag-drop keyboard alternative
- Column navigation
- Card details accessible
- Focus management

---

**Begin review.**
