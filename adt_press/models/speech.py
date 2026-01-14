from pydantic import BaseModel

from adt_press.models.ids import SpeechID, TextID


class SpeechFile(BaseModel):
    speech_id: SpeechID
    text_id: TextID
    speech_path: str
    language_code: str
    provider: str
    voice: str
    model: str
