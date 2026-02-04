from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, conint, confloat

class TranslationEvalOutput(BaseModel):
    text_id: str
    base_text: str
    translation: str
    is_translation_acceptable: bool
    rationale: str

class TranslationEvalOutputs(BaseModel):
    base_language: str
    target_language: str
    outputs: List[TranslationEvalOutput]