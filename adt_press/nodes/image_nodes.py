from adt_press.llm.image_caption import get_image_caption
from adt_press.llm.image_crop import CropPromptConfig, get_image_crop_coordinates
from adt_press.llm.image_meaningfulness import get_image_meaningfulness
from adt_press.llm.prompt import PromptConfig
from adt_press.nodes.config_nodes import BlankImageFilterConfig, ImageSizeFilterConfig
from adt_press.utils.file import write_file
from adt_press.utils.image import (
    Image,
    ImageCaption,
    ImageCrop,
    ImageFilterFailure,
    ImageMeaningfulness,
    ProcessedImage,
    PrunedImage,
    crop_image,
    image_bytes,
    is_blank_image,
)
from adt_press.utils.pdf import Page
from adt_press.utils.sync import gather_with_limit, run_async_task


def image_size_filter_failures(pdf_images: list[Image], image_size_filter_config: ImageSizeFilterConfig) -> dict[str, ImageFilterFailure]:
    failures = {}
    for img in pdf_images:
        failed = []
        if img.width < image_size_filter_config.min_side or img.height < image_size_filter_config.min_side:
            failed.append(f"side < {image_size_filter_config.min_side} pixels")
        if img.width > image_size_filter_config.max_side or img.height > image_size_filter_config.max_side:  # pragma: no cover
            failed.append(f"side > {image_size_filter_config.max_side} pixels")

        if failed:
            failures[img.image_id] = ImageFilterFailure(
                image_id=img.image_id, filter="size", reasoning=", ".join(failed),
            )
    return failures


def image_blank_filter_failures(
    pdf_images: list[Image], blank_image_filter_config: BlankImageFilterConfig
) -> dict[str, ImageFilterFailure]:
    failures = {}
    for img in pdf_images:
        img_bytes = image_bytes(img.upath)
        if is_blank_image(img_bytes, blank_image_filter_config.threshold):
            failures[img.image_id] = ImageFilterFailure(image_id=img.image_id, filter="blank", reasoning="image is blank")

    return failures


def image_meaningfulness(
    meaningfulness_prompt_config: PromptConfig,
    pdf_pages: list[Page],
    image_blank_filter_failures: dict[str, ImageFilterFailure],
    image_size_filter_failures: dict[str, ImageFilterFailure],
) -> dict[str, ImageMeaningfulness]:
    async def generate_meaningfulness():
        meaningfulness = []
        for page in pdf_pages:
            for image in page.images:
                # skip images that have already been filtered out
                if image.image_id not in image_blank_filter_failures and image.image_id not in image_size_filter_failures:
                    meaningfulness.append(get_image_meaningfulness(meaningfulness_prompt_config, page, image))

        return await gather_with_limit(meaningfulness, meaningfulness_prompt_config.rate_limit)

    return {m.image_id: m for m in run_async_task(generate_meaningfulness)}


def image_meaningfulness_failures(image_meaningfulness: dict[str, ImageMeaningfulness]) -> dict[str, ImageFilterFailure]:
    failures = {}

    # map our list back to a dict of failures
    for k, m in image_meaningfulness.items():
        if not m.is_meaningful:  # pragma: no cover
            failures[k] = ImageFilterFailure(
                image_id=m.image_id,
                filter="meaningfulness",
                reasoning=m.reasoning,
            )

    return failures


def pruned_images(
    pdf_images: list[Image],
    image_size_filter_failures: dict[str, ImageFilterFailure],
    image_blank_filter_failures: dict[str, ImageFilterFailure],
    image_meaningfulness_failures: dict[str, ImageFilterFailure],
) -> list[PrunedImage]:
    pruned_images = []
    for img in pdf_images:
        failed_filters = []
        if img.image_id in image_size_filter_failures:
            failed_filters.append(image_size_filter_failures[img.image_id])
        if img.image_id in image_blank_filter_failures:
            failed_filters.append(image_blank_filter_failures[img.image_id])
        if img.image_id in image_meaningfulness_failures:  # pragma: no cover
            failed_filters.append(image_meaningfulness_failures[img.image_id])

        if failed_filters:
            pruned_images.append(PrunedImage(**img.model_dump(), failed_filters=failed_filters))

    return pruned_images


def pruned_image_ids(pruned_images: list[PrunedImage]) -> set[str]:
    return {img.image_id for img in pruned_images}


def filtered_images(pdf_images: list[Image], pruned_image_ids: set[str]) -> list[Image]:
    return [img for img in pdf_images if img.image_id not in pruned_image_ids]


def image_captions(
    output_language_config: str, caption_prompt_config: PromptConfig, pdf_pages: list[Page], pruned_image_ids: set[str]
) -> dict[str, ImageCaption]:
    async def generate_captions():
        captions = []
        for page in pdf_pages:
            for image in page.images:
                if image.image_id not in pruned_image_ids:
                    captions.append(get_image_caption(caption_prompt_config, page, image, output_language_config))

        return await gather_with_limit(captions, caption_prompt_config.rate_limit)

    return {c.image_id: c for c in run_async_task(generate_captions)}


def image_crops(crop_prompt_config: CropPromptConfig, pdf_pages: list[Page], pruned_image_ids: set[str]) -> dict[str, ImageCrop]:
    async def generate_crop(page: Page, img: Image) -> ImageCrop:
        coord = await get_image_crop_coordinates(crop_prompt_config, page, img)

        # create a cropped version of the image
        cropped = crop_image(image_bytes(img.upath), coord)

        # add the coordinates to the image path so that we don't cache different crops of the same image
        cropped_path = write_file(
            img.upath,
            cropped,
            f"cropped_{coord.top_left_x}_{coord.top_left_y}_{coord.bottom_right_x}_{coord.bottom_right_y}",
        )

        return ImageCrop(image_id=img.image_id, crop_coordinates=coord, upath=str(cropped_path))

    async def generate_crops():
        crops = []
        for page in pdf_pages:
            for img in page.images:
                if img.image_id not in pruned_image_ids:
                    crops.append(generate_crop(page, img))

        return await gather_with_limit(crops, crop_prompt_config.rate_limit)

    return {c.image_id: c for c in run_async_task(generate_crops)}


def processed_images(
    filtered_images: list[Image],
    image_captions: dict[str, ImageCaption],
    image_crops: dict[str, ImageCrop],
    image_meaningfulness: dict[str, ImageMeaningfulness],
) -> list[ProcessedImage]:
    processed_images = []
    for img in filtered_images:
        image_args = img.model_dump()
        image_args["caption"] = image_captions.get(img.image_id)
        image_args["meaningfulness"] = image_meaningfulness.get(img.image_id)
        image_args["crop"] = image_crops.get(img.image_id)
        processed_images.append(ProcessedImage(**image_args))

    return processed_images
