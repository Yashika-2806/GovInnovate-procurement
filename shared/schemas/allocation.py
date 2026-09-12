from pydantic import BaseModel, Field

class Allocation(BaseModel):
    allocation_id: str
    startup_id: str
    opportunity_id: str
    status: str = "allocated"
