import enum
import os

import fitz  # PyMuPDF
from fsspec import open
from pydantic import BaseModel

from adt_press.data.image import Image
from adt_press.data.pdf import Page
from adt_press.utils.file import write_file
from adt_press.utils.image import matplotlib_chart
from adt_press.utils.vector import render_drawings


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
        page_number = page_index + 1
        page_id = f"p{page_number}"

        page_image_upath = output_dir + os.sep + f"img_{page_id}.png"
        write_file(page_image_upath, page_image.tobytes(output="png"))

        images = []
        image_index = 0

        # extract all raster images
        for img in fitz_page.get_images(full=True):
            pix = fitz.Pixmap(doc, img[0])
            pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
            img_id = f"img_{page_id}_r{image_index}"
            img_bytes = pix_rgb.tobytes(output="png")

            # write image out
            image_upath = output_dir + os.sep + f"{img_id}.png"
            write_file(image_upath, img_bytes)

            # also write out our chart image
            chart_upath = write_file(image_upath, matplotlib_chart(img_bytes), "chart")

            images.append(
                Image(
                    image_id=img_id,
                    page_id=page_id,
                    index=image_index,
                    upath=str(image_upath),
                    chart_upath=str(chart_upath),
                    width=pix_rgb.width,
                    height=pix_rgb.height,
                )
            )

            image_index += 1

        # also extract vector drawings
        drawings = fitz_page.get_drawings()
        vector_images = render_drawings(drawings, margin_allowance=2, overlap_threshold=400)
        for img in vector_images:
            img_id = f"img_{page_id}_v{image_index}"
            vector_upath = output_dir + os.sep + f"{img_id}.png"
            image_upath = write_file(vector_upath, img.image)
            chart_upath = write_file(image_upath, matplotlib_chart(img.image), "chart")
            images.append(
                Image(
                    image_id=img_id,
                    page_id=page_id,
                    index=image_index,
                    upath=str(image_upath),
                    chart_upath=str(chart_upath),
                    width=img.width,
                    height=img.height,
                )
            )
            image_index += 1

        pages.append(
            Page(
                page_id=page_id,
                page_number=page_number,
                image_upath=page_image_upath,
                text=fitz_page.get_text(),
                images=images,
            )
        )

    return pages
