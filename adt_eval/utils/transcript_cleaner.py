import re

def normalize_transcript(text:str) -> str:
    """
    Normalizes a transcript by removing punctuation/special characters and converting to lowercase.
    This normalization is not useful for producing an ADT, but rather only for matching content between the Gold Standard and the raw LLM output.
    """
    

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)

    return text


def standardize_transcript(text:str, strip_whitespace:bool=True) -> str:
    """
    Apply standard cleaning steps to the transcript text.
    This could be useful for producing an ADT, but is not currently applied in the core ADT pipeline.

    Args:
        text (str): The transcript text to standardize.
        strip_whitespace (bool): Whether to strip excess whitespace. Default is True.
    """

    # Remove directional punctuation
    text = text.replace("’", "'")
    text = text.replace("”", '"')
    text = text.replace("‘", "'")
    text = text.replace("“", '"')

    # Remove excess whitespace
    if strip_whitespace==True:
        text = re.sub(r'\s+', ' ', text).strip()

    return text
