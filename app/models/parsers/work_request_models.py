from pydantic import BaseModel, Field 
from typing import Literal, List


class ChecklistItem(BaseModel):
    label: str = Field(
        ...,
        description="Short checklist label describing a verification or approval step",
    )
    is_applicable: bool = Field(
        ...,
        description="true if this checklist item applies to this project, otherwise false",
    )



class WorkRequestModel(BaseModel): 
    project_title: str = Field(
        ...,
        description="Short project title (max ~12 words) summarizing the work request",
    )

    discipline_name: str = Field(
        ...,
        description="Discipline name EXACTLY as one of the provided discipline enums",
    )
    discipline_id: int = Field(
        ...,
        description="ID of the selected discipline from the provided discipline enums",
    )

    # Request type is numeric and appears to be fixed for this flow
    quotation_type_id: int = Field(
        5,
        description="Numeric request type, use 5 for standard work request generation",
    )

    contract_name: str = Field(
        "",
        description="Contract name, if unknown keep empty string",
    )

    request_type_name: Literal[
        "Capital Expenditure (CAPEX)",
        "Capital with or without Expense",
        "Compliance & Regulatory",
        "OFC - Repair & Corrective Maintenance",
        "Planned Preventive Maintenance (PPM)",
        "OFC - BU/GRE Requested",
        "Sustainability & Green Initiatives",
        "Technology & Digital Transformation",
        "DC - BU/GRE Requested",
    ] = Field(
        ...,
        description="Label from project type enums (enum1)",
    )

    request_type_id: int = Field(
        ...,
        description="ID from project type enums (enum1) corresponding to request_type_name",
    )

    lumsum_type_name: Literal[
        "Cost-Plus Offer",
        "Fixed Offer",
    ] = Field(
        ...,
        description="Label from lumsum type enums (enum3)",
    )
    lumsum_type_id: int = Field(
        ...,
        description="ID from lumsum type enums (enum3) corresponding to lumsum_type_name",
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
        description="150-200 words. Consequences and risks if the work is not approved",
    )

    project_checklists: List[ChecklistItem] = Field(
        ...,
        description=(
            "Array of checklist items with label and is_applicable true/false. "
            "At least 5 items, max 15."
        ),
    )


 


PROJECT_TYPE_ENUMS = [
    {"id": 1, "name": "Capital Expenditure (CAPEX)"},
    {"id": 2, "name": "Capital with or without Expense"},
    {"id": 3, "name": "Compliance & Regulatory"},
    {"id": 4, "name": "OFC - Repair & Corrective Maintenance"},
    {"id": 5, "name": "Planned Preventive Maintenance (PPM)"},
    {"id": 6, "name": "OFC - BU/GRE Requested"},
    {"id": 7, "name": "Sustainability & Green Initiatives"},
    {"id": 8, "name": "Technology & Digital Transformation"},
    {"id": 9, "name": "DC - BU/GRE Requested"},
]

DISCIPLINE_ENUMS = [
    {"id": 26, "name": "Whitespace Turnkey"},
    {"id": 25, "name": "Environmental / Sustainability"},
    {"id": 24, "name": "Consultancy"},
    {"id": 23, "name": "Life Safety System"},
    {"id": 22, "name": "Electrical"},
    {"id": 21, "name": "Other"},
    {"id": 20, "name": "ICT / Low Current"},
    {"id": 19, "name": "Civil Works / Structural"},
    {"id": 18, "name": "Plumbing"},
    {"id": 17, "name": "Mechanical"},
    {"id": 11, "name": "M&E>>Medium Voltage"},
    {"id": 10, "name": "M&E>>HVAC Systems"},
    {"id": 9, "name": "M&E>>Generators"},
    {"id": 8, "name": "M&E>>Electrical Systems"},
    {"id": 7, "name": "M&E>>PMS"},
]

LUMSUM_TYPE_ENUMS = [
    {"id": 2, "name": "Cost-Plus Offer"},
    {"id": 1, "name": "Fixed Offer"},
]
