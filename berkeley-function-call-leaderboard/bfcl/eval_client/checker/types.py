from pydantic import BaseModel
from typing import Any, Optional

class AstCheckerResult(BaseModel):
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        extra = 'allow'
        
class ExecutableCheckerResult(BaseModel):
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    execution_output: Any
    
    class Config:
        extra = 'allow'