from pydantic import BaseModel, Field
from typing import List, Optional

class BlueprintRequest(BaseModel):
    message: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    chat_uid: Optional[str] = None

class CodeGenerationRequest(BaseModel):
    blueprint: dict
    message: str

class code_generation_model(BaseModel):
    engineer_comments: str = Field(description="Description of the problem and approach")
    code: str = Field(description="Solution code block")

class reviewer_evaluation_model(BaseModel):
    reviewer_comments: str = Field(description="Comments from confidence from the reviewer that the code fulfill requirements and specs")
    confidence_score: int = Field(description="Confidence score from 0 to 100, 0 being 0 percent confidence and 100 being 100 percent confidence the code will work")

class BlueprintOutputClass(BaseModel):
    """ 
        Workaround for error:
        pydantic_core._pydantic_core.ValidationError: 1 validation error for BlueprintOutputClass
            blueprint
            Input should be a valid dictionary [type=dict_type, input_value='{"entities": ["Task", "U...board", "Task Detail"]}', input_type=str]
                For further information visit https://errors.pydantic.dev/2.11/v/dict_type
    """
    #blueprint: dict
    blueprint: str

