from typing import List, Dict


MOCK_ROWS = [
{"id": 101, "name": "HQ Chiller Replacement", "status": "Active", "budget": 125000, "priority": "P1"},
{"id": 102, "name": "Data Center UPS Upgrade", "status": "Planned", "budget": 200000, "priority": "P0"},
{"id": 103, "name": "Office LED Retrofit", "status": "Active", "budget": 45000, "priority": "P2"},
]


def list_top_projects(tenant: str, limit: int = 10) -> List[Dict]:
# Ignore tenant in mock; slice rows
    return MOCK_ROWS[:limit]