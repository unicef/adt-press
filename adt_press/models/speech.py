from pydantic import BaseModel

from adt_press.models.ids import TextID, SpeechID

class SpeechFile(BaseModel):
    speech_id: SpeechID
    speech_path: str
    language_code: str
    text_id: TextID
    provider: str
    voice: str
    model: str
