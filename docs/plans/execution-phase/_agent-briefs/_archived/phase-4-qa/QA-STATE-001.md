# Agent Brief: QA-STATE-001

**Agent ID:** QA-STATE-001
**Agent Name:** State Management QA
**Type:** QA
**Phase:** 4 - Frontend
**Paired Dev Agent:** DEV-STATE-001

---

## Validation Checklist

- [ ] All stores functional
- [ ] UI store manages sidebar/theme/toasts
- [ ] API client authentication works
- [ ] Error handling catches 401
- [ ] useProjects CRUD works
- [ ] useJobs status tracking works
- [ ] useAuth login/logout works
- [ ] Optimistic updates work
- [ ] Cache invalidation works
- [ ] No unnecessary re-renders

---

## Test Cases

1. UI store sidebar toggle
2. UI store theme change persists
3. Toast notification queue
4. API client adds auth header
5. API client handles 401
6. Fetch projects list
7. Create new project
8. Update project optimistically
9. Delete project with confirmation
10. Job creation and status tracking
11. Login/logout flow
12. Token refresh

---

## Performance Tests

- Store updates don't cascade re-renders
- Selector memoization works
- API cache reduces requests
- Large list performance

---

## Error Handling Tests

- Network error handling
- 401 redirects to login
- 404 shows not found
- 500 shows error message
- Retry logic works

---

**Begin review.**
