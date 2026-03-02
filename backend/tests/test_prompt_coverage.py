"""Validate prompt coverage: every GENERATED/HYBRID field must have a prompt defined."""
import pytest

from app.services.prompt_manager import PromptManager
from app.services.template_fields import TEMPLATE_FIELD_REGISTRY, FieldType


@pytest.mark.unit
class TestPromptCoverage:
    """Ensure prompt_manager defines prompts for all generatable fields."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.pm = PromptManager()
        self.defaults = self.pm.get_default_prompts()

    @pytest.mark.parametrize("template_type", [
        "aggregators", "opr", "mpp", "adop", "adre", "commercial"
    ])
    def test_all_generated_hybrid_fields_have_prompts(self, template_type):
        """Every GENERATED/HYBRID field must have a matching prompt."""
        fields = TEMPLATE_FIELD_REGISTRY[template_type]
        missing = []

        for field_name, field_def in fields.items():
            if field_def.field_type not in (FieldType.GENERATED, FieldType.HYBRID):
                continue

            template_key = f"{template_type}:{field_name}"
            if template_key not in self.defaults and field_name not in self.defaults:
                missing.append(field_name)

        assert missing == [], (
            f"{template_type}: {len(missing)} GENERATED/HYBRID fields missing prompts: "
            f"{', '.join(sorted(missing))}"
        )

    @pytest.mark.parametrize("template_type", [
        "aggregators", "opr", "mpp", "adop", "adre", "commercial"
    ])
    def test_no_orphaned_prompt_keys(self, template_type):
        """Every prompt key should correspond to a field in the registry."""
        fields = TEMPLATE_FIELD_REGISTRY[template_type]
        prefix = f"{template_type}:"
        prompt_keys = [
            k.replace(prefix, "") for k in self.defaults if k.startswith(prefix)
        ]
        orphaned = [k for k in prompt_keys if k not in fields]

        assert orphaned == [], (
            f"{template_type}: {len(orphaned)} prompt keys with no matching field: "
            f"{', '.join(sorted(orphaned))}"
        )
