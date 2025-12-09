from pydantic import BaseModel, Field
from typing import Literal, List


class SchemaArgsModel(BaseModel):
    modules: List[
        Literal[
            "projects_module",
            "project_labours_module",
            "project_vendors_module",
            "scope_and_approvals_module",
        ]
    ] = Field(
        ...,
        description=(
            "Minimal list of schema modules required to answer the user's data question. "
            "Allowed values: 'projects_module', 'project_labours_module', "
            "'project_vendors_module', 'scope_and_approvals_module'."
        ),
    )
