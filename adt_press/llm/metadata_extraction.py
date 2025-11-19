from banks import Prompt

from adt_press.models.config import MetadataPromptConfig
from adt_press.models.metadata import BookMetadata
from adt_press.models.pdf import Page
from adt_press.llm import get_instructor_client
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file


class MetadataResponse(CleanTextBaseModel):
    title: str | None
    authors: list[str]
    publisher: str | None
    cover_page_id: str | None
    reasoning: str


async def get_metadata(config: MetadataPromptConfig, pages: list[Page], pdf_metadata: dict[str, object]) -> BookMetadata:
    """
    Extract book metadata (title, author, cover page) from the first pages of a PDF.

    Args:
        config: Prompt configuration including model, template, and retry settings
        pages: List of Page objects to analyze (typically first 2-4 pages)
        pdf_metadata: PDF metadata from the PDF file's Info dictionary (may contain title, author, etc.)

    Returns:
        Metadata object with extracted information
    """
    context = dict(
        pages=pages,
        pdf_metadata=pdf_metadata,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()
    response: MetadataResponse = await client.chat.completions.create(
        model=config.model,
        response_model=MetadataResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return BookMetadata(
        title=response.title,
        authors=response.authors,
        publisher=response.publisher,
        cover_page_id=response.cover_page_id,
        reasoning=response.reasoning,
    )
