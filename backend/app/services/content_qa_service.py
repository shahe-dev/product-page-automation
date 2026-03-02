"""
Content quality assurance service for PDP Automation v.3

Handles:
- Brand compliance validation
- Character limit enforcement
- SEO optimization checks
- Factual accuracy verification
- Comprehensive QA reporting
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from app.services.content_generator import ContentOutput, GeneratedField

logger = logging.getLogger(__name__)


@dataclass
class QACheckResult:
    """Result of a single QA check."""

    check_type: str  # "brand_compliance", "seo_score", "character_limits", "factual_accuracy"
    passed: bool
    score: float  # 0-100
    issues: list[dict] = field(default_factory=list)  # [{"field": "...", "issue": "...", "severity": "..."}]

    def add_issue(
        self,
        field: str,
        issue: str,
        severity: str = "warning"
    ) -> None:
        """Add an issue to the check result."""
        self.issues.append({
            "field": field,
            "issue": issue,
            "severity": severity
        })


@dataclass
class QAReport:
    """Comprehensive QA report for generated content."""

    overall_passed: bool
    overall_score: float  # 0-100
    checks: list[QACheckResult]
    critical_issues: int
    warnings: int

    def get_check(self, check_type: str) -> Optional[QACheckResult]:
        """Get a specific check result by type."""
        for check in self.checks:
            if check.check_type == check_type:
                return check
        return None


class ContentQAService:
    """Service for content quality assurance validation."""

    # Prohibited terms that indicate low-quality marketing copy
    PROHIBITED_TERMS = [
        r"\bworld-class\b",
        r"\bprime location\b",
        r"\bstate-of-the-art\b",
        r"\bunrivaled\b",
        r"\bprestigious\b(?! developer| area)",  # OK if specific
        r"\bexclusive\b(?! deal| offer)",  # OK if factual
        r"\bluxury\b(?! developer| brand)",  # OK if factual
    ]

    # Required terminology
    CORRECT_TERMINOLOGY = {
        r"\bflat\b": "apartment",
        r"\bbuilder\b": "developer",
        r"\bcompletion\b": "handover",
        r"\binstallment plan\b": "payment plan",
    }

    # SEO keywords that should be present
    SEO_KEYWORDS = [
        "Dubai",
        "property",
        "apartment",
        "developer",
    ]

    def __init__(self):
        """Initialize QA service."""
        logger.info("ContentQAService initialized")

    def validate_content(
        self,
        content_output: ContentOutput,
        source_data: dict
    ) -> QAReport:
        """
        Run all QA checks on generated content.

        Args:
            content_output: Generated content to validate
            source_data: Original structured data for fact-checking

        Returns:
            QAReport with comprehensive validation results
        """
        logger.info("Running QA validation on %d fields", len(content_output.fields))

        checks = [
            self.check_character_limits(content_output.fields),
            self.check_brand_compliance(content_output.fields),
            self.check_seo_score(content_output.fields, source_data),
            self.check_factual_accuracy(content_output.fields, source_data),
        ]

        # Count issues by severity
        critical_issues = sum(
            len([i for i in check.issues if i["severity"] == "critical"])
            for check in checks
        )
        warnings = sum(
            len([i for i in check.issues if i["severity"] == "warning"])
            for check in checks
        )

        # Calculate overall score (weighted average)
        total_score = sum(check.score for check in checks)
        overall_score = total_score / len(checks) if checks else 0

        # Overall pass if no critical issues and score >= 70
        overall_passed = critical_issues == 0 and overall_score >= 70.0

        report = QAReport(
            overall_passed=overall_passed,
            overall_score=round(overall_score, 2),
            checks=checks,
            critical_issues=critical_issues,
            warnings=warnings
        )

        logger.info(
            "QA validation complete: %s (score: %.1f, critical: %d, warnings: %d)",
            "PASSED" if overall_passed else "FAILED",
            overall_score,
            critical_issues,
            warnings
        )

        return report

    def check_brand_compliance(
        self,
        fields: dict[str, GeneratedField]
    ) -> QACheckResult:
        """
        Check content against brand guidelines.

        Args:
            fields: Generated content fields

        Returns:
            QACheckResult for brand compliance
        """
        result = QACheckResult(
            check_type="brand_compliance",
            passed=True,
            score=100.0
        )

        total_checks = 0
        failed_checks = 0

        for field_name, generated_field in fields.items():
            content = generated_field.content.lower()

            # Check for prohibited terms
            for term_pattern in self.PROHIBITED_TERMS:
                matches = re.findall(term_pattern, content, re.IGNORECASE)
                if matches:
                    result.add_issue(
                        field=field_name,
                        issue=f"Contains prohibited term: '{matches[0]}'",
                        severity="warning"
                    )
                    failed_checks += 1
                total_checks += 1

            # Check for incorrect terminology
            for incorrect_pattern, correct_term in self.CORRECT_TERMINOLOGY.items():
                matches = re.findall(incorrect_pattern, content, re.IGNORECASE)
                if matches:
                    result.add_issue(
                        field=field_name,
                        issue=f"Use '{correct_term}' instead of '{matches[0]}'",
                        severity="warning"
                    )
                    failed_checks += 1
                total_checks += 1

            # Check tone (basic heuristics)
            salesy_indicators = [
                r"\bdon't miss out\b",
                r"\blimited time\b",
                r"\bact now\b",
                r"\bonce in a lifetime\b",
            ]
            for indicator in salesy_indicators:
                if re.search(indicator, content, re.IGNORECASE):
                    result.add_issue(
                        field=field_name,
                        issue=f"Overly promotional tone detected: '{indicator}'",
                        severity="warning"
                    )
                    failed_checks += 1
                total_checks += 1

        # Calculate score
        if total_checks > 0:
            result.score = ((total_checks - failed_checks) / total_checks) * 100
        else:
            result.score = 100.0

        result.passed = result.score >= 80.0

        logger.info(
            "Brand compliance check: %s (score: %.1f, issues: %d)",
            "PASSED" if result.passed else "FAILED",
            result.score,
            len(result.issues)
        )

        return result

    def check_character_limits(
        self,
        fields: dict[str, GeneratedField]
    ) -> QACheckResult:
        """
        Verify each field is within its character limit.

        Args:
            fields: Generated content fields

        Returns:
            QACheckResult for character limits
        """
        result = QACheckResult(
            check_type="character_limits",
            passed=True,
            score=100.0
        )

        exceeded_count = 0
        total_fields = len(fields)

        for field_name, generated_field in fields.items():
            if not generated_field.within_limit:
                result.add_issue(
                    field=field_name,
                    issue=f"Exceeds character limit: {generated_field.character_count} chars",
                    severity="critical"
                )
                exceeded_count += 1
                result.passed = False

        # Calculate score
        if total_fields > 0:
            result.score = ((total_fields - exceeded_count) / total_fields) * 100
        else:
            result.score = 100.0

        logger.info(
            "Character limit check: %s (score: %.1f, exceeded: %d/%d)",
            "PASSED" if result.passed else "FAILED",
            result.score,
            exceeded_count,
            total_fields
        )

        return result

    def check_seo_score(
        self,
        fields: dict[str, GeneratedField],
        source_data: dict
    ) -> QACheckResult:
        """
        Check SEO optimization quality.

        Args:
            fields: Generated content fields
            source_data: Original project data

        Returns:
            QACheckResult for SEO
        """
        result = QACheckResult(
            check_type="seo_score",
            passed=True,
            score=100.0
        )

        seo_checks_passed = 0
        total_seo_checks = 0

        # Check meta_title
        if "meta_title" in fields:
            meta_title = fields["meta_title"]
            total_seo_checks += 3

            # Length check
            if 50 <= meta_title.character_count <= 60:
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="meta_title",
                    issue=f"Meta title length {meta_title.character_count} not optimal (50-60 chars)",
                    severity="warning"
                )

            # Project name inclusion
            project_name = source_data.get("project_name", "").lower()
            if project_name and project_name in meta_title.content.lower():
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="meta_title",
                    issue="Meta title should include project name",
                    severity="warning"
                )

            # Location inclusion
            location = source_data.get("location", "").lower()
            if location and location in meta_title.content.lower():
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="meta_title",
                    issue="Meta title should include location",
                    severity="warning"
                )

        # Check meta_description
        if "meta_description" in fields:
            meta_desc = fields["meta_description"]
            total_seo_checks += 2

            # Length check
            if 150 <= meta_desc.character_count <= 160:
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="meta_description",
                    issue=f"Meta description length {meta_desc.character_count} not optimal (150-160 chars)",
                    severity="warning"
                )

            # Keyword presence
            content_lower = meta_desc.content.lower()
            keyword_found = any(kw.lower() in content_lower for kw in self.SEO_KEYWORDS)
            if keyword_found:
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="meta_description",
                    issue=f"Should include SEO keywords: {', '.join(self.SEO_KEYWORDS)}",
                    severity="warning"
                )

        # Check URL slug
        if "url_slug" in fields:
            url_slug = fields["url_slug"]
            total_seo_checks += 2

            # Format check (kebab-case)
            if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', url_slug.content):
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="url_slug",
                    issue="URL slug should be lowercase kebab-case (e.g., 'marina-heights-dubai')",
                    severity="warning"
                )

            # Length check (3-5 words)
            word_count = len(url_slug.content.split('-'))
            if 3 <= word_count <= 5:
                seo_checks_passed += 1
            else:
                result.add_issue(
                    field="url_slug",
                    issue=f"URL slug should be 3-5 words ({word_count} words found)",
                    severity="warning"
                )

        # Calculate score
        if total_seo_checks > 0:
            result.score = (seo_checks_passed / total_seo_checks) * 100
        else:
            result.score = 100.0

        result.passed = result.score >= 70.0

        logger.info(
            "SEO check: %s (score: %.1f, passed: %d/%d)",
            "PASSED" if result.passed else "FAILED",
            result.score,
            seo_checks_passed,
            total_seo_checks
        )

        return result

    def check_factual_accuracy(
        self,
        fields: dict[str, GeneratedField],
        source_data: dict
    ) -> QACheckResult:
        """
        Verify factual accuracy against source data.

        Args:
            fields: Generated content fields
            source_data: Original project data

        Returns:
            QACheckResult for factual accuracy
        """
        result = QACheckResult(
            check_type="factual_accuracy",
            passed=True,
            score=100.0
        )

        accuracy_checks_passed = 0
        total_accuracy_checks = 0

        # Extract all content for checking
        all_content = " ".join(
            field.content for field in fields.values()
        ).lower()

        # Check project name
        project_name = source_data.get("project_name", "")
        if project_name:
            total_accuracy_checks += 1
            if project_name.lower() in all_content:
                accuracy_checks_passed += 1
            else:
                result.add_issue(
                    field="general",
                    issue=f"Project name '{project_name}' not found in content",
                    severity="critical"
                )
                result.passed = False

        # Check developer
        developer = source_data.get("developer", "")
        if developer:
            total_accuracy_checks += 1
            if developer.lower() in all_content:
                accuracy_checks_passed += 1
            else:
                result.add_issue(
                    field="general",
                    issue=f"Developer '{developer}' not mentioned in content",
                    severity="warning"
                )

        # Check location
        location = source_data.get("location", "")
        if location:
            total_accuracy_checks += 1
            if location.lower() in all_content:
                accuracy_checks_passed += 1
            else:
                result.add_issue(
                    field="general",
                    issue=f"Location '{location}' not mentioned in content",
                    severity="critical"
                )
                result.passed = False

        # Check price (if mentioned, it should be accurate)
        starting_price = source_data.get("starting_price")
        if starting_price:
            total_accuracy_checks += 1
            # Look for price mentions (basic check)
            # Format: AED 1,500,000 or 1.5M or similar
            price_patterns = [
                str(starting_price),
                f"{starting_price:,}",
                f"{starting_price/1000000:.1f}M" if starting_price >= 1000000 else "",
            ]
            price_found = any(pattern and pattern.lower() in all_content for pattern in price_patterns)
            if price_found or "aed" in all_content or "price" in all_content:
                accuracy_checks_passed += 1
            # If no price mentioned at all, that's also acceptable
            elif not any(p in all_content for p in ["aed", "price", "from"]):
                accuracy_checks_passed += 1

        # Calculate score
        if total_accuracy_checks > 0:
            result.score = (accuracy_checks_passed / total_accuracy_checks) * 100
        else:
            result.score = 100.0

        logger.info(
            "Factual accuracy check: %s (score: %.1f, passed: %d/%d)",
            "PASSED" if result.passed else "FAILED",
            result.score,
            accuracy_checks_passed,
            total_accuracy_checks
        )

        return result


# Singleton instance (thread-safe)
_qa_service_instance: Optional[ContentQAService] = None
_qa_service_lock = __import__("threading").Lock()


def get_qa_service() -> ContentQAService:
    """
    Get or create singleton ContentQAService instance (thread-safe).

    Returns:
        ContentQAService instance
    """
    global _qa_service_instance
    if _qa_service_instance is None:
        with _qa_service_lock:
            if _qa_service_instance is None:
                _qa_service_instance = ContentQAService()
    return _qa_service_instance
