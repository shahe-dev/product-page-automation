"""
Cross-Validation Reconciliation Service

Compares extraction results from multiple sources (regex, LLM, table)
and produces a reconciled value with confidence scoring.

Priority order for numeric fields: table > regex > LLM
Priority order for semantic fields: LLM > regex
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Fields where regex/table values should override LLM
NUMERIC_FIELDS = {
    "price_min", "price_max", "price_per_sqft",
    "total_units", "floors",
    "total_sqft", "balcony_sqft", "builtup_sqft",
    "bedrooms_count", "bathrooms_count",
}

# Fields where LLM is preferred (semantic understanding needed)
SEMANTIC_FIELDS = {
    "description", "amenities", "key_features",
    "property_type", "community", "sub_community",
}


@dataclass
class ReconciliationResult:
    """Result of reconciling a single field."""

    field: str
    final_value: Any
    source: str  # "regex", "llm", "table", "agreement", "none"
    confidence: float
    flagged: bool = False
    details: str = ""


class CrossValidator:
    """Reconciles extraction results from multiple sources."""

    def reconcile(
        self,
        field: str,
        regex_value: Any = None,
        llm_value: Any = None,
        table_value: Any = None,
    ) -> ReconciliationResult:
        """Reconcile a single field from multiple sources."""

        # Table values are highest priority (exact from PDF data stream)
        if table_value is not None:
            flagged = (
                llm_value is not None
                and llm_value != table_value
                and field in NUMERIC_FIELDS
            )
            return ReconciliationResult(
                field=field,
                final_value=table_value,
                source="table",
                confidence=0.99,
                flagged=flagged,
                details=(
                    f"table={table_value}, llm={llm_value}" if flagged else ""
                ),
            )

        is_numeric = field in NUMERIC_FIELDS

        # Both sources agree
        if regex_value is not None and llm_value is not None:
            if self._values_match(regex_value, llm_value, is_numeric):
                return ReconciliationResult(
                    field=field,
                    final_value=regex_value,
                    source="agreement",
                    confidence=0.98,
                )

            # Disagreement
            if is_numeric:
                return ReconciliationResult(
                    field=field,
                    final_value=regex_value,
                    source="regex",
                    confidence=0.85,
                    flagged=True,
                    details=f"regex={regex_value}, llm={llm_value}",
                )
            else:
                return ReconciliationResult(
                    field=field,
                    final_value=llm_value,
                    source="llm",
                    confidence=0.80,
                    flagged=True,
                    details=f"regex={regex_value}, llm={llm_value}",
                )

        # Only one source has a value
        if regex_value is not None:
            return ReconciliationResult(
                field=field,
                final_value=regex_value,
                source="regex",
                confidence=0.80,
            )
        if llm_value is not None:
            return ReconciliationResult(
                field=field,
                final_value=llm_value,
                source="llm",
                confidence=0.70,
            )

        # Neither source has a value
        return ReconciliationResult(
            field=field,
            final_value=None,
            source="none",
            confidence=0.0,
        )

    def reconcile_project(
        self,
        structured,  # StructuredProject
        regex_hints: dict,
        table_hints: dict,
    ) -> tuple:
        """Reconcile all fields of a StructuredProject.

        Returns (reconciled_project, list_of_flags).
        """
        flags = []

        field_mapping = {
            "price_min": "price_min",
            "price_max": "price_max",
            "price_per_sqft": "price_per_sqft",
            "developer": "developer",
            "emirate": "emirate",
            "community": "community",
            "project_name": "project_name",
        }

        for field_name, attr_name in field_mapping.items():
            llm_value = getattr(structured, attr_name, None)
            regex_value = regex_hints.get(field_name)
            table_value = table_hints.get(field_name)

            result = self.reconcile(
                field=field_name,
                regex_value=regex_value,
                llm_value=llm_value,
                table_value=table_value,
            )

            if result.final_value is not None:
                setattr(structured, attr_name, result.final_value)
            if result.flagged:
                flags.append(result)

        return structured, flags

    @staticmethod
    def _values_match(a: Any, b: Any, is_numeric: bool) -> bool:
        """Check if two values match (with tolerance for numbers)."""
        if a == b:
            return True
        if is_numeric:
            try:
                return abs(float(a) - float(b)) < 1.0
            except (ValueError, TypeError):
                return False
        if isinstance(a, str) and isinstance(b, str):
            return a.strip().lower() == b.strip().lower()
        return False
