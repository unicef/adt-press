from bs4 import BeautifulSoup

from adt_press.utils.image import ProcessedImage


def replace_images(html_content: str, image_replacements: dict[str, ProcessedImage]) -> str:
    """
    Replace all images with ids that match the keys in image_replacements with their corresponding paths.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup.find_all("img"):
        if tag.get("data-id") in image_replacements:
            img = image_replacements[tag["data-id"]]
            tag["src"] = f"./images/{img.image_id}.png"
            tag["alt"] = img.caption.caption
            tag["aria-label"] = img.caption.caption

    return str(soup)


def replace_texts(html_content: str, text_replacements: dict[str, str]) -> str:
    """
    Replace all text elements with ids that match the keys in text_replacements with their corresponding texts.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # TODO: is this the right set of tags to replace?
    for tag in soup.find_all(["h1", "h2", "p", "span"]):
        if tag.get("data-id") in text_replacements:
            tag.string = text_replacements[tag["data-id"]]

    return str(soup)
