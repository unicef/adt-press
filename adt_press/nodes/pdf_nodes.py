from fsspec import open
from upath import UPath

from adt_press.llm.image_caption import get_image_caption
from adt_press.llm.image_crop import get_image_crop_coordinates
from adt_press.llm.image_meaningfulness import get_image_meaningfulness
from adt_press.llm.prompt import PromptConfig
from adt_press.nodes.config_nodes import BlankImageFilterConfig, ImageSizeFilterConfig, PageRangeConfig
from adt_press.utils.image import (
    Image,
    ImageCaption,
    ImageCrop,
    ImageMeaningfulness,
    ProcessedImage,
    crop_image,
    image_bytes,
    is_blank_image,
    matplotlib_chart,
    write_image,
)
from adt_press.utils.pdf import Page, pages_for_pdf


def pdf_pages(
    output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig
) -> list[Page]:
    return pages_for_pdf(output_dir_config, pdf_path_config, page_range_config.start, page_range_config.end)


def pdf_raster_images(pdf_pages: list[Page]) -> list[Image]:
    pdf_raster_images = []
    for page in pdf_pages:
        pdf_raster_images.extend(page.images)
    return pdf_raster_images


def pdf_image_charts(pdf_raster_images: list[Image]) -> list[Image]:
    image_charts = []
    for img in pdf_raster_images:
        chart_bytes = matplotlib_chart(image_bytes(img.upath))

        # build a new path for the chart image based on our img upath
        chart_upath = UPath(img.upath).parent / f"{img.image_id}_chart.png"
        with open(chart_upath, "wb") as f:
            f.write(chart_bytes)

        img.chart_upath = str(chart_upath)
        image_charts.append(img)
    return image_charts


def pdf_size_filter_results(
    pdf_raster_images: list[Image], image_size_filter_config: ImageSizeFilterConfig
) -> list[list]:
    results = []
    for img in pdf_raster_images:
        failed = []
        if img.width < image_size_filter_config.min_side or img.height < image_size_filter_config.min_side:
            failed.append("min_side")
        if img.width > image_size_filter_config.max_side or img.height > image_size_filter_config.max_side:
            failed.append("max_side")

        results.append(failed)

    return results


def pdf_blank_filter_results(
    pdf_raster_images: list[Image], blank_image_filter_config: BlankImageFilterConfig
) -> list[list]:
    results = []
    for img in pdf_raster_images:
        failed = []
        img_bytes = image_bytes(img.upath)
        if is_blank_image(img_bytes, blank_image_filter_config.threshold):
            failed.append("blank")
        results.append(failed)

    return results


def pdf_image_captions(
    output_language_config: str, caption_prompt_config: PromptConfig, pdf_pages: list[Page]
) -> list[ImageCaption]:
    captions = []
    for page in pdf_pages:
        for image in page.images:
            captions.append(get_image_caption(caption_prompt_config, page, image, output_language_config))

    return captions


def pdf_image_meaningfulness(
    meaningfulness_prompt_config: PromptConfig, pdf_pages: list[Page]
) -> list[ImageMeaningfulness]:
    meaningfulness = []
    for page in pdf_pages:
        for image in page.images:
            meaningfulness.append(get_image_meaningfulness(meaningfulness_prompt_config, page, image))

    return meaningfulness


def pdf_image_crops(crop_prompt_config: PromptConfig, pdf_pages: list[Page]) -> list[ImageCrop]:
    crops = []
    for page in pdf_pages:
        for img in page.images:
            coordinates = get_image_crop_coordinates(crop_prompt_config, page, img)

            # create a cropped version of the image
            cropped = crop_image(image_bytes(img.upath), coordinates)

            # add the coordinates to the image path so that we don't cache different crops of the same image
            cropped_path = write_image(
                img.upath,
                cropped,
                f"cropped_{coordinates.top_left_x}_{coordinates.top_left_y}_{coordinates.bottom_right_x}_{coordinates.bottom_right_y}",
            )

            crops.append(
                ImageCrop(
                    image_id=img.image_id,
                    crop_coordinates=coordinates,
                    upath=str(cropped_path),
                )
            )

    return crops


def pdf_processed_images(
    pdf_raster_images: list[Image],
    pdf_size_filter_results: list[list],
    pdf_blank_filter_results: list[list],
    pdf_image_captions: list[ImageCaption],
    pdf_image_crops: list[ImageCrop],
    pdf_image_meaningfulness: list[ImageMeaningfulness],
) -> list[Image]:
    processed_images = []
    for img, size_failures, blank_failures, caption, crop, meaningfulness in zip(
        pdf_raster_images,
        pdf_size_filter_results,
        pdf_blank_filter_results,
        pdf_image_captions,
        pdf_image_crops,
        pdf_image_meaningfulness,
    ):
        image_args = img.model_dump()
        image_args["caption"] = caption
        image_args["meaningfulness"] = meaningfulness
        image_args["crop"] = crop
        image_args["failed_filters"] = [*size_failures, *blank_failures]
        processed_images.append(ProcessedImage(**image_args))

    return processed_images
