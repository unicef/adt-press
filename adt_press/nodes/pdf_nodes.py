from adt_press.nodes.config_nodes import PageRangeConfig
from adt_press.utils.image import Image
from adt_press.utils.pdf import Page, pages_for_pdf


def pdf_images(pdf_pages: list[Page]) -> list[Image]:
    pdf_images = []
    for page in pdf_pages:
        pdf_images.extend(page.images)
    return pdf_images


def pdf_pages(output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig) -> list[Page]:
    return pages_for_pdf(output_dir_config, pdf_path_config, page_range_config.start, page_range_config.end)
