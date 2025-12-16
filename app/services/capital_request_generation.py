import logging
from app.core.config import settings
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Tuple, Optional

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field, conint, confloat, validator
from zoneinfo import ZoneInfo

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.llms.runnable.llm_provider import get_chain_llm
from app.graphs.nodes.prompts.capital_request_generation_prompt import CAPITAL_REQUEST_GENERATION_PROMPT
log = logging.getLogger("capital_planning")

# ============================================================
# ENUMS / CONSTANTS
# ============================================================


class Category(str, Enum):
    UPS_SYSTEMS = "UPS Systems"
    GENERATOR_FUEL_SYSTEMS = "Generator & Fuel Systems"
    SWITCHGEAR_DISTRIBUTION = "Switchgear & Distribution"
    CHILLERS_COOLING_PLANTS = "Chillers & Cooling Plants"
    CRAC_CRAH_UNITS = "CRAC/CRAH Units"
    FIRE_SYSTEMS = "Fire Systems"
    CABLING_CONTROLS = "Cabling & Controls"
    SUSTAINABILITY = "Sustainability"


class Priority(str, Enum):
    P0 = "P0"  # Critical
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"  # Lowest


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ImpactArea(str, Enum):
    OPERATIONS = "operations"
    FINANCE = "finance"
    SAFETY = "safety"
    CLIENT = "client"
    SUSTAINABILITY = "sustainability"
    STRATEGIC = "strategic"  # normalized spelling


# ---- enum2 data (capacity / matrix units) ----
# You can later load this from DB/config instead of hard-coding.
ENUM2_DATA = [
    {"id": 1, "matrix": "load", "name": "kW"},
    {"id": 2, "matrix": "load", "name": "MW"},
    {"id": 3, "matrix": "load", "name": "kVA"},
    {"id": 4, "matrix": "load", "name": "MVA"},
    {"id": 5, "matrix": "load", "name": "W"},
    {"id": 6, "matrix": "fuel", "name": "L"},
    {"id": 7, "matrix": "fuel", "name": "gal"},
    {"id": 8, "matrix": "fuel", "name": "m³"},
    {"id": 9, "matrix": "fuel", "name": "kg"},
    {"id": 10, "matrix": "fuel", "name": "tons"},
    {"id": 11, "matrix": "fuel", "name": "lb"},
    {"id": 12, "matrix": "power", "name": "kW"},
    {"id": 13, "matrix": "power", "name": "MW"},
    {"id": 14, "matrix": "power", "name": "HP"},
    {"id": 15, "matrix": "power", "name": "W"},
    {"id": 16, "matrix": "power", "name": "kVA"},
    {"id": 17, "matrix": "power", "name": "MVA"},
    {"id": 18, "matrix": "energy", "name": "kWh"},
    {"id": 19, "matrix": "energy", "name": "MWh"},
    {"id": 20, "matrix": "energy", "name": "GJ"},
    {"id": 21, "matrix": "energy", "name": "BTU"},
    {"id": 22, "matrix": "energy", "name": "J"},
    {"id": 23, "matrix": "energy", "name": "MJ"},
    {"id": 24, "matrix": "energy", "name": "therm"},
    {"id": 25, "matrix": "capacity", "name": "kW"},
    {"id": 26, "matrix": "capacity", "name": "MW"},
    {"id": 27, "matrix": "capacity", "name": "tons"},
    {"id": 28, "matrix": "capacity", "name": "kg"},
    {"id": 29, "matrix": "capacity", "name": "L"},
    {"id": 30, "matrix": "capacity", "name": "m³"},
    {"id": 31, "matrix": "capacity", "name": "gal"},
    {"id": 32, "matrix": "capacity", "name": "HP"},
    {"id": 33, "matrix": "cooling", "name": "tons"},
    {"id": 34, "matrix": "cooling", "name": "kW"},
    {"id": 35, "matrix": "cooling", "name": "BTU/h"},
    {"id": 36, "matrix": "cooling", "name": "W"},
    {"id": 37, "matrix": "cooling", "name": "RT"},
    {"id": 38, "matrix": "heating", "name": "kW"},
    {"id": 39, "matrix": "heating", "name": "BTU/h"},
    {"id": 40, "matrix": "heating", "name": "W"},
    {"id": 41, "matrix": "heating", "name": "MW"},
    {"id": 42, "matrix": "heating", "name": "therm/h"},
    {"id": 43, "matrix": "water", "name": "L"},
    {"id": 44, "matrix": "water", "name": "m³"},
    {"id": 45, "matrix": "water", "name": "gal"},
    {"id": 46, "matrix": "water", "name": "L/min"},
    {"id": 47, "matrix": "water", "name": "m³/h"},
    {"id": 48, "matrix": "water", "name": "gpm"},
    {"id": 49, "matrix": "water", "name": "L/h"},
    {"id": 50, "matrix": "steam", "name": "kg/h"},
    {"id": 51, "matrix": "steam", "name": "lb/h"},
    {"id": 52, "matrix": "steam", "name": "tons/h"},
    {"id": 53, "matrix": "steam", "name": "m³/h"},
    {"id": 54, "matrix": "steam", "name": "kg/s"},
    {"id": 55, "matrix": "steam", "name": "lb/s"},
    {"id": 56, "matrix": "compressed_air", "name": "m³/min"},
    {"id": 57, "matrix": "compressed_air", "name": "CFM"},
    {"id": 58, "matrix": "compressed_air", "name": "m³/h"},
    {"id": 59, "matrix": "compressed_air", "name": "L/min"},
    {"id": 60, "matrix": "compressed_air", "name": "scfm"},
    {"id": 61, "matrix": "compressed_air", "name": "Nm³/h"},
    {"id": 62, "matrix": "gas", "name": "m³"},
    {"id": 63, "matrix": "gas", "name": "L"},
    {"id": 64, "matrix": "gas", "name": "kg"},
    {"id": 65, "matrix": "gas", "name": "scf"},
    {"id": 66, "matrix": "gas", "name": "Nm³"},
    {"id": 67, "matrix": "gas", "name": "therm"},
    {"id": 68, "matrix": "gas", "name": "MMBTU"},
    {"id": 69, "matrix": "hvac", "name": "kW"},
    {"id": 70, "matrix": "hvac", "name": "tons"},
    {"id": 71, "matrix": "hvac", "name": "BTU/h"},
    {"id": 72, "matrix": "hvac", "name": "CFM"},
    {"id": 73, "matrix": "hvac", "name": "W"},
    {"id": 74, "matrix": "hvac", "name": "RT"},
]

MATRIX_UNIT_TO_ID = {
    (entry["matrix"], entry["name"]): entry["id"] for entry in ENUM2_DATA
}

PRIORITY_TO_START_OFFSET_DAYS = {
    Priority.P0: 1,  # Critical
    Priority.P1: 7,
    Priority.P2: 30,
    Priority.P3: 90,
    Priority.P4: 120,
    Priority.P5: 180,  # ~6 months
}


# ============================================================
# Pydantic MODELS
# ============================================================


class RequiredCapacity(BaseModel):
    matrix_type: str = Field(
        ...,
        description=(
            "One of: load, fuel, power, energy, capacity, cooling, heating, "
            "water, steam, compressed_air, gas, hvac"
        ),
    )
    unit_name: str = Field(
        ...,
        description="Must match the 'name' field from enum2 (e.g. 'kW', 'tons', 'm³').",
    )
    value: confloat(ge=0) = Field(
        ..., description="Numeric value for required capacity in the chosen unit."
    )


class ProjectIntentLLM(BaseModel):
    category: Category
    required_capacity: RequiredCapacity

    priority: Priority
    scope_of_works: str = Field(
        ...,
        description="Short enhanced description of the scope of works, ~150-200 words.",
    )

    risk_level: RiskLevel
    impact_areas: List[ImpactArea]

    equipment_survivability_days: conint(ge=0) = Field(
        ...,
        description="Number of days the existing system can survive without this project.",
    )

    expected_project_duration_days: conint(ge=1, le=3650) = Field(
        ...,
        description="Estimated number of days to complete the project once started.",
    )

    @validator("impact_areas")
    def unique_impact_areas(cls, v):
        # dedupe while preserving order
        seen = set()
        result = []
        for item in v:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    # Optional site name; prefer proper nouns only, else null
    site_name: Optional[str] = Field(
        default=None,
        description=(
            "Proper-noun site name if clearly mentioned (e.g., 'Riyad', 'Witting Group'); otherwise null."
        ),
    )


class ProjectAutoGenerated(BaseModel):
    # LLM-derived (semantic)
    category: Category
    required_capacity_matrix_type: str
    required_capacity_unit_name: str
    required_capacity_value: float
    required_capacity_enum2_id: int

    priority: Priority
    scope_of_works: str
    risk_level: RiskLevel
    impact_areas: List[ImpactArea]

    equipment_survivability_days: int
    expected_project_duration_days: int

    # System-derived
    project_start: datetime
    project_end: datetime


class AutoProjectRequest(BaseModel):
    user_command: str


# ============================================================
# DOMAIN HELPERS (capacity, dates)
# ============================================================


def resolve_capacity_enum2_id(matrix_type: str, unit_name: str) -> int:
    key = (matrix_type, unit_name)
    if key not in MATRIX_UNIT_TO_ID:
        raise ValueError(
            f"Invalid capacity pair: matrix_type={matrix_type!r}, unit_name={unit_name!r}"
        )
    return MATRIX_UNIT_TO_ID[key]


def compute_project_dates(
    priority: Priority,
    expected_duration_days: int,
    today: datetime,
) -> Tuple[datetime, datetime]:
    offset_days = PRIORITY_TO_START_OFFSET_DAYS[priority]
    project_start = today + timedelta(days=offset_days)
    project_end = project_start + timedelta(days=expected_duration_days)
    return project_start, project_end


# ============================================================
# LLM CHAIN (LangChain + PydanticOutputParser)
# ============================================================


def create_project_intent_chain(model_key: Optional[str] = None, model_id: Optional[str] = None):
    parser = PydanticOutputParser[ProjectIntentLLM](pydantic_object=ProjectIntentLLM)

    log.info("before LLM CALL")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CAPITAL_REQUEST_GENERATION_PROMPT),
            ("human", "User command:\n{user_command}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    llm = get_chain_llm(model_key, model_id)

    chain = prompt | llm | parser
    return chain


# Create chain once at import time
PROJECT_INTENT_CHAIN = create_project_intent_chain()


# ============================================================
# SERVICE FUNCTION
# ============================================================


# def analyze_project_command(user_command: str) -> ProjectAutoGenerated:
#     """
#     Core service function:
#     - Calls LLM chain
#     - Resolves enum2 id
#     - Computes project dates
#     - Returns final DTO
#     """
#     # 1) LLM structured output
#     intent: ProjectIntentLLM = PROJECT_INTENT_CHAIN.invoke(
#         {"user_command": user_command}
#     )

#     # 2) Capacity enum2 mapping
#     enum2_id = resolve_capacity_enum2_id(
#         intent.required_capacity.matrix_type,
#         intent.required_capacity.unit_name,
#     )

#     # 3) Compute start/end dates
#     today = datetime.now(tz=ZoneInfo("Asia/Karachi"))
#     project_start, project_end = compute_project_dates(
#         priority=intent.priority,
#         expected_duration_days=intent.expected_project_duration_days,
#         today=today,
#     )

#     # 4) Final DTO
#     return ProjectAutoGenerated(
#         category=intent.category,
#         required_capacity_matrix_type=intent.required_capacity.matrix_type,
#         required_capacity_unit_name=intent.required_capacity.unit_name,
#         required_capacity_value=float(intent.required_capacity.value),
#         required_capacity_enum2_id=enum2_id,
#         priority=intent.priority,
#         scope_of_works=intent.scope_of_works,
#         risk_level=intent.risk_level,
#         impact_areas=intent.impact_areas,
#         equipment_survivability_days=intent.equipment_survivability_days,
#         expected_project_duration_days=intent.expected_project_duration_days,
#         project_start=project_start,
#         project_end=project_end,
#     )
