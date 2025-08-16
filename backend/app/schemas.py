from pydantic import BaseModel, Field
from typing import Optional

class AuditLogEntry(BaseModel):
    ts: str
    request_id: str
    request_body: dict
    input_hash: str
    output_hash: str
    prev_hash: Optional[str] = None
    signer_id: str
    hash: str = Field(exclude=True)
    sig: str = Field(exclude=True)