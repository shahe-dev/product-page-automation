# Prompt System Remediation -- Session Prompts

Copy-paste one prompt per fresh Claude Code session. Execute in order.
Each session reads the plan from `docs/plans/2026-01-29-prompt-system-remediation.md`.

---

## Session 1: Wire Database Path + Field Registry

```
Execute the implementation plan at docs/plans/2026-01-29-prompt-system-remediation.md

This session covers:
- Task 1.1: Pass database session from JobManager to ContentGenerator
- Task 1.2: Update ContentGenerator singleton to handle db session lifecycle
- Task 2.1: Create template field registry (backend/app/services/template_fields.py)

Key context:
- The core bug is at backend/app/services/content_generator.py:210 where db=None is hardcoded
- The db session is available in job_manager.py via self.job_repo.db (confirmed at line 912)
- The singleton at content_generator.py:437-454 must be replaced with a factory
- template_fields.py defines per-template field sets based on docs/TEMPLATES_REFERENCE.md
- All 6 template types: aggregators, opr, mpp, adop, adre, commercial

Run tests after each task. Commit after each task passes.
Stop after Task 2.1 is committed.
```

---

## Session 2: Integrate Field Registry + Template Prompts (aggregators, opr, mpp)

```
Execute the implementation plan at docs/plans/2026-01-29-prompt-system-remediation.md

This session covers:
- Task 2.2: Integrate template field registry into ContentGenerator
- Task 2.3 (Part 1): Make PromptManager template-aware -- implement for aggregators, opr, mpp

Key context from previous session (already committed):
- backend/app/services/content_generator.py now accepts db param and uses get_content_generator() factory
- backend/app/services/template_fields.py exists with TEMPLATE_FIELD_REGISTRY for all 6 types
- backend/app/services/job_manager.py passes self.job_repo.db to the generator

For Task 2.2:
- Replace FIELD_LIMITS in content_generator.py with get_fields_for_template() calls
- Update generate_all() and generate_field() to use template-specific field sets
- See plan for exact line-by-line changes

For Task 2.3 Part 1:
- Restructure prompt_manager.py get_default_prompts() to support template-specific keys
- The key format is "{template_type}:{field_name}" with fallback to "{field_name}"
- Update get_prompt() lookup to check template-specific key first
- Implement _get_generic_field_prompts() (rename existing 10 prompts)
- Implement _get_aggregators_prompts() -- SEO-focused, searchability, 24+ aggregator domains
- Implement _get_opr_prompts() -- investment-focused, ROI, neutral factual tone per reference/company/prompts/prompt  opr.md
- Implement _get_mpp_prompts() -- balanced buyer/investor, comprehensive project pages

Each prompt method returns a dict of {field_name: {"content": str, "character_limit": int, "version": 1}}.
Every field in the corresponding *_FIELDS dict from template_fields.py needs a prompt.
Prompts must use {project_name}, {developer}, {location}, {emirate}, {starting_price}, {handover_date}, {amenities}, {property_types}, {payment_plan}, {description} placeholders.
Each prompt ends with "Return ONLY the [field] text, nothing else."
Follow brand guidelines: no prohibited terms, advisor tone not salesperson.

Run tests after each task. Commit after each task.
Stop after opr and mpp prompt methods are committed.
```

---

## Session 3: Template Prompts (adop, adre, commercial)

```
Execute the implementation plan at docs/plans/2026-01-29-prompt-system-remediation.md

This session covers:
- Task 2.3 (Part 2): Implement template-aware prompts for adop, adre, commercial

Key context from previous sessions (already committed):
- backend/app/services/prompt_manager.py already has:
  - Restructured get_default_prompts() with template-specific key format "{template_type}:{field_name}"
  - Updated get_prompt() that checks template-specific key first, then generic fallback
  - _get_generic_field_prompts() with the base 10 prompts
  - _get_aggregators_prompts(), _get_opr_prompts(), _get_mpp_prompts() implemented
- backend/app/services/template_fields.py has ADOP_FIELDS, ADRE_FIELDS, COMMERCIAL_FIELDS

Implement these three methods in prompt_manager.py:

1. _get_adop_prompts()
   - Abu Dhabi off-plan developments (abudhabioffplan.ae)
   - Unique fields: about_paragraph_1/2/3, key_benefit_1/2/3, infrastructure_description + bullets, investment_description + bullets
   - 8 FAQ pairs
   - Tone: new development features, area infrastructure, Abu Dhabi investment benefits

2. _get_adre_prompts()
   - Abu Dhabi ready/secondary market (secondary-market-portal.com)
   - Unique fields: hero_marketing_h2, amenity_*_h3 + descriptions, economic_appeal (rental/resale/enduser), location categorized (entertainment/healthcare/education)
   - 8 FAQ pairs
   - Tone: ready property market, rental yield, resale potential, end-user lifestyle

3. _get_commercial_prompts()
   - Commercial real estate (cre.main-portal.com)
   - Unique fields: economic_indicator_1/2/3 (label+value), project_passport_description, economic_appeal_description, advantage_1/2/3, location with social/education/medical facilities
   - Tone: B2B professional, office/retail focus, business-oriented metrics

Each prompt method returns {field_name: {"content": str, "character_limit": int, "version": 1}}.
Use the same placeholders: {project_name}, {developer}, {location}, {emirate}, {starting_price}, {handover_date}, {amenities}, {property_types}, {payment_plan}, {description}.
End each prompt with "Return ONLY the [field] text, nothing else."
Follow brand guidelines from reference/company/brand-guidelines/brand-context-prompt.md.

Run tests. Commit when all three methods are done.
```

---

## Session 4: Seed Script, Cleanup, E2E Tests

```
Execute the implementation plan at docs/plans/2026-01-29-prompt-system-remediation.md

This session covers:
- Task 3.1: Rewrite seed_prompts.py for all 6 template types
- Task 3.2: Remove dead template prompt file loading from content_generator.py
- Task 3.3: End-to-end smoke tests for all 6 template types

Key context from previous sessions (already committed):
- backend/app/services/template_fields.py has TEMPLATE_FIELD_REGISTRY with all 6 templates
- backend/app/services/prompt_manager.py has template-aware get_default_prompts() with keys like "opr:meta_title"
- backend/app/services/content_generator.py accepts db session and uses get_fields_for_template()

For Task 3.1:
- Rewrite backend/scripts/seed_prompts.py to iterate all 6 template types
- Seed every field from TEMPLATE_FIELD_REGISTRY with prompt content from PromptManager defaults
- Support --force flag to overwrite existing prompts
- See plan for exact code

For Task 3.2:
- Remove _load_template_prompts() method from content_generator.py
- Remove self.template_prompts from __init__
- Simplify _build_system_message() to use template descriptions only (brand context + type description)
- Do NOT remove brand context loading (_load_brand_context stays)

For Task 3.3:
- Create backend/tests/test_prompt_system_e2e.py
- Parametrized test across all 6 template types
- Mock the Anthropic API, verify all fields generate without errors
- Verify generated field set matches TEMPLATE_FIELD_REGISTRY exactly

Run ALL tests at the end:
  pytest backend/tests/test_template_fields.py backend/tests/test_prompt_db_integration.py backend/tests/test_prompt_system_e2e.py -v

Commit after each task. Final commit should have all tests green.
```
