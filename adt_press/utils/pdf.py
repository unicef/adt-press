import os

import fitz  # PyMuPDF
from fsspec import open
from pydantic import BaseModel

from adt_press.utils.image import Image, matplotlib_chart, write_image


class Page(BaseModel):
    page_index: int
    image_upath: str

    images: list[Image] = []


# We need to set this zoom for PyMuPDF or the image is pixelated.
FITZ_ZOOM = 2
FITZ_MAT = fitz.Matrix(FITZ_ZOOM, FITZ_ZOOM)


def pages_for_pdf(output_dir: str, pdf_path: str, start_page: int, end_page: int) -> list[Page]:
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    end_page = end_page if end_page > 0 else min(len(doc), end_page if end_page else len(doc))

    for page_index in range(start_page, end_page):
        fitz_page = doc[page_index]
        page_image = fitz_page.get_pixmap(matrix=FITZ_MAT)
        page_image_upath = output_dir + os.sep + f"img_p{page_index}.png"
        write_image(page_image_upath, page_image.tobytes(output="png"))

        page = Page(page_index=page_index, image_upath=page_image_upath)

        for image_index, img in enumerate(fitz_page.get_images(full=True)):
            pix = fitz.Pixmap(doc, img[0])
            pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
            img_id = f"img_p{page_index}_i{image_index}"
            img_bytes = pix_rgb.tobytes(output="png")

            # write image out
            image_upath = output_dir + os.sep + f"{img_id}.png"
            write_image(image_upath, img_bytes)

            # also write out our chart image
            chart_upath = write_image(image_upath, matplotlib_chart(img_bytes), "chart")

            page.images.append(
                Image(
                    image_id=img_id,
                    page=page_index,
                    index=image_index,
                    upath=str(image_upath),
                    chart_upath=str(chart_upath),
                    width=pix_rgb.width,
                    height=pix_rgb.height,
                )
            )

        pages.append(page)

    return pages
