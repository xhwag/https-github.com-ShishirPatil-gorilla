from pydantic import BaseModel
from typing import List, Any, Optional


class AstCheckerResult(BaseModel):
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str | List] = None  # It's a list for parallel case

    class Config:
        extra = "allow"


class ExecutableCheckerResult(BaseModel):
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str | List] = None  # It's a list for parallel case
    execution_output: Optional[Any] = None

    class Config:
        extra = "allow"


class APIStatusObject(BaseModel):
    errors: List[tuple]
    error_rate: str
    
