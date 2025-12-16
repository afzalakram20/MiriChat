from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    conlist,
)
from typing import Literal, List, Optional
from pydantic import AliasChoices

PROJECT_TYPE_ENUMS = [
    {"id": 3, "name": "Capital with or without Expense"},
    {"id": 5, "name": "Sustainability & Green Initiatives"},
    {"id": 6, "name": "Technology & Digital Transformation"},
    {"id": 7, "name": "Compliance & Regulatory"},
    {"id": 9, "name": "Capital Expenditure (CAPEX)"},
    {"id": 10, "name": "Planned Preventive Maintenance (PPM)"},
]

DISCIPLINE_ENUMS = [
    {"id": 17, "name": "Mechanical"},
    {"id": 18, "name": "Plumbing"},
    {"id": 19, "name": "Civil Works / Structural"},
    {"id": 20, "name": "ICT / Low Current"},
    {"id": 21, "name": "Other"},
    {"id": 22, "name": "Electrical"},
    {"id": 23, "name": "Life Safety System"},
    {"id": 24, "name": "Consultancy"},
    {"id": 25, "name": "Environmental / Sustainability"},
    {"id": 26, "name": "Whitespace Turnkey"},
]

LUMSUM_TYPE_ENUMS = [
    {"id": 2, "name": "Cost-Plus Offer"},
    {"id": 1, "name": "Fixed Offer"},
]

PROJECT_CHECKLIST_ENUMS = [
    {"id": 1, "name": "As Builts"},
    {"id": 2, "name": "EANS/CMMS Update"},
    {"id": 3, "name": "O&M Manuals"},
    {"id": 7, "name": "Job Punch List"},
    {"id": 5, "name": "Health & Safety Form (EPIC Form)"},
    {"id": 6, "name": "Single Source Approval"},
    {"id": 4, "name": "Close-Out Checklist"},
    {"id": 24, "name": "EBVO Needed ?"},
]

QUOTATION_TYPE_ENUMS = [
    {"id": 1, "name": "Kyndrl Offer"},
    {"id": 5, "name": "General Offer"},
]


class ChecklistItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(
        ..., description="ID of checklist item from PROJECT_CHECKLIST_ENUMS"
    )
    label: str = Field(
        ...,
        description="Name of checklist item from PROJECT_CHECKLIST_ENUMS",
    )
    is_applicable: bool = Field(
        ...,
        description="true if this checklist item applies to this project, otherwise false",
    )

    @field_validator("id")
    def id_must_be_in_project_checklist_enums(cls, v: int) -> int:
        allowed_ids = {e["id"] for e in PROJECT_CHECKLIST_ENUMS}
        if v not in allowed_ids:
            raise ValueError(f"Checklist id must be one of: {sorted(allowed_ids)}")
        return v

    @field_validator("label")
    def label_must_be_in_project_checklist_enums(cls, v: str) -> str:
        allowed = [e["name"] for e in PROJECT_CHECKLIST_ENUMS]
        if v not in allowed:
            raise ValueError(
                f"Checklist label must be one of PROJECT_CHECKLIST_ENUMS: {', '.join(allowed)}"
            )
        return v


class WorkRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_title: str = Field(
        ...,
        description="Short project title (max ~12 words) summarizing the work request",
    )

    # Optional site name (proper noun). If not clearly provided, keep as null.
    site_name: Optional[str] = Field(
        None,
        description=(
            "Extracted proper-noun site name (e.g., 'Witting Group'). "
            "If not clearly provided, leave as null."
        ),
    )

    discipline_name: str = Field(
        ...,
        description="Discipline name EXACTLY as one of the provided discipline enums DISCIPLINE_ENUMS",
    )
    discipline_id: int = Field(
        ...,
        description="ID of the selected discipline from the provided discipline enums DISCIPLINE_ENUMS",
    )

    # Request type is numeric and appears to be fixed for this flow
    quotation_type_id: int = Field(
        1,
        description="ID of the selected quotation type from the provided quotation enums QUOTATION_TYPE_ENUMS",
    )

    contract_name: str = Field(
        "",
        description="Contract name, if unknown keep empty string",
    )

    request_type_name: Literal[
        "Capital with or without Expense",
        "Sustainability & Green Initiatives",
        "Technology & Digital Transformation",
        "Compliance & Regulatory",
        "Capital Expenditure (CAPEX)",
        "Planned Preventive Maintenance (PPM)",
    ] = Field(
        ...,
        description="Label from project type enums PROJECT_TYPE_ENUMS",
    )

    request_type_id: int = Field(
        ...,
        description="ID from project type enums PROJECT_TYPE_ENUMS corresponding to request_type_name",
    )

    lumsum_type_name: Literal[
        "Cost-Plus Offer",
        "Fixed Offer",
    ] = Field(
        ...,
        description="Label from lumsum type enums LUMSUM_TYPE_ENUMS",
    )
    lumsum_type_id: int = Field(
        ...,
        description="ID from lumsum type enums LUMSUM_TYPE_ENUMS corresponding to lumsum_type_name",
    )

    is_user_funded: bool = Field(
        False,
        description=(
            "true if user-funded / BU-funded can be clearly inferred from context, "
            "otherwise false"
        ),
    )

    appro_number: str = Field(
        "",
        description="Approval number if provided, else keep empty string",
    )

    # Long text fields (150-200 words)
    problem_statement: str = Field(
        ...,
        alias="Problem Statement",
        description="150-200 words. Describe the core problem and background context",
    )
    scope_of_works: str = Field(
        ...,
        alias="Scope of Works",
        validation_alias=AliasChoices("Scope of Works", "Scope Of Works"),
        description="150-200 words. Describe detailed scope of works to be executed",
    )
    justifications: str = Field(
        ...,
        alias="Justifications",
        description="150-200 words. Explain why this work is needed and benefits",
    )
    effect_of_non_approval: str = Field(
        ...,
        alias="Effect of Non-Approval",
        validation_alias=AliasChoices("Effect of Non-Approval", "Effect Of Non-Approval"),
        description="150-200 words. Consequences and risks if the work is not approved",
    )

    project_checklists: List[ChecklistItem] = Field(
        ...,
        description=(
            "Array of checklist items with id, label, and is_applicable true/false. "
            "You MUST include EXACTLY one entry for every item in PROJECT_CHECKLIST_ENUMS."
        ),
    )

    # Enforce exact size and id-label mapping
    @model_validator(mode="after")
    def validate_project_checklists_complete_and_matching(self):
        items: List[ChecklistItem] = getattr(self, "project_checklists", []) or []
        enum_ids = sorted(e["id"] for e in PROJECT_CHECKLIST_ENUMS)
        provided_ids = sorted({item.id for item in items})
        if provided_ids != enum_ids or len(items) != len(enum_ids):
            raise ValueError(
                "project_checklists must include exactly one entry for every PROJECT_CHECKLIST_ENUMS id "
                f"(expected ids {enum_ids}, got {provided_ids})"
            )
        id_to_name = {e["id"]: e["name"] for e in PROJECT_CHECKLIST_ENUMS}
        for item in items:
            expected_label = id_to_name.get(item.id)
            if item.label != expected_label:
                raise ValueError(
                    f"Checklist item id {item.id} label mismatch: expected '{expected_label}', got '{item.label}'"
                )
        return self

    # Ensure request_type_id matches request_type_name (auto-correct if needed)
    @model_validator(mode="after")
    def ensure_request_type_id_matches(self):
        name = getattr(self, "request_type_name", None)
        id_map = {e["name"]: e["id"] for e in PROJECT_TYPE_ENUMS}
        expected = id_map.get(name)
        if expected is not None and getattr(self, "request_type_id", None) != expected:
            try:
                object.__setattr__(self, "request_type_id", expected)
            except Exception:
                # Fallback assignment if needed
                self.request_type_id = expected  # type: ignore[attr-defined]
        return self

    # Normalize/validate site_name to avoid generic placeholders
    @field_validator("site_name")
    def normalize_site_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        candidate = (v or "").strip()
        if not candidate:
            return None
        lower = candidate.lower()
        generic_phrases = {
            "site",
            "the site",
            "specific site",
            "site mentioned",
            "any site",
        }
        if lower in generic_phrases:
            return None
        # Heuristic: prefer names with at least one capitalized word
        words = candidate.split()
        has_capitalized = any(w[:1].isupper() for w in words if w)
        if not has_capitalized:
            return None
        return candidate
