from typing import Optional

from ebooklib import epub

from adt_press.models.plate import Plate, PlateImage, PlateText
from adt_press.models.web import WebPage
from adt_press.utils.file import cached_read_file
from adt_press.utils.html import replace_images, replace_texts


def create_epub_file(
    output_path: str,
    title: str,
    language: str,
    authors: list[str],
    plate: Plate,
    web_pages: list[WebPage],
    plate_texts: dict[str, PlateText],
    translations: dict[str, str],
    image_dir: str,
    css_content: Optional[str] = None,
) -> str:
    """
    Generate an EPUB file from ADT content.

    Args:
        output_path: Path where the EPUB file should be saved
        title: Book title
        language: Primary language code (e.g., 'es', 'en')
        author: Book author
        plate: Plate object with book structure
        web_pages: List of generated web pages
        plate_texts: Dictionary of text elements by ID
        translations: Dictionary of translated text by text_id
        image_dir: Directory containing images
        css_content: Optional CSS styling

    Returns:
        Path to the generated EPUB file
    """
    print("writing epub to", output_path)
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f"adt-press-{title}")
    book.set_title(title)
    book.set_language(language)
    for author in authors:
        book.add_author(author)

    # Add CSS
    if css_content:
        css = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css", content=css_content)
        book.add_item(css)

    # Add images
    images_by_id: dict[str, PlateImage] = {img.image_id: img for img in plate.images}
    texts_by_id: dict[str, PlateText] = {txt.text_id: txt for txt in plate.texts}
    seen_images: dict[str, PlateImage] = {}

    if plate.cover_image_id:
        img = images_by_id[plate.cover_image_id]
        img_bytes = cached_read_file(img.image_path)
        book.set_cover(file_name="images/cover.png", content=img_bytes)

    # add all our images to the book
    for webpage in web_pages:
        for image_id in webpage.image_ids:
            img = images_by_id[image_id]
            img_bytes = cached_read_file(img.image_path)
            img_item = epub.EpubItem(uid=img.image_id, file_name=f"images/{image_id}.png", media_type="image/png", content=img_bytes)

            # save it for replacement later
            seen_images[image_id] = PlateImage(image_id=img.image_id, image_path=f"images/{image_id}.png", caption_id=img.caption_id)
            book.add_item(img_item)

    # Create chapters from web pages
    chapters = []
    for idx, webpage in enumerate(web_pages):
        content = webpage.content
        content = replace_images(content, seen_images, texts_by_id)
        content = replace_texts(content, texts_by_id)

        chapter = epub.EpubHtml(title=f"Section {idx + 1}", file_name=f"chap_{webpage.section_id}.xhtml", lang=language)
        chapter.content = f"{content}"

        if css_content:
            chapter.add_item(css)

        book.add_item(chapter)
        chapters.append(chapter)

    # Define Table of Contents
    book.toc = tuple(chapters)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = """
        body { font-family: Arial, sans-serif; }
        h1 { text-align: center; }
        img { max-width: 100%; height: auto; }
    """
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Create spine
    book.spine = ["nav"] + chapters

    # Write EPUB file
    epub.write_epub(output_path, book)

    return output_path
