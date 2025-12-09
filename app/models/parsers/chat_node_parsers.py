from pydantic import BaseModel, Field 
 

class IntentResult(BaseModel):
    intent: str = Field(default="unknown")
    post_actions: list[str] = Field(default_factory=list)
    params: dict = Field(default_factory=dict)
    requires_multistep: bool = Field(default=False)


