from pydantic import BaseModel


class SpeechFile(BaseModel):
    speech_id: str
    speech_upath: str
    language_code: str
    text_id: str
