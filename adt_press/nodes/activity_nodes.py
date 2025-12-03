"""Hamilton nodes for generating activity definitions from sections."""

import logging

from hamilton.function_modifiers import config

from adt_press.llm.activity_generation import generate_activity_definition
from adt_press.models.activity import Activity, ActivityType
from adt_press.models.config import ActivityTypeConfig
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSections
from adt_press.models.text import PageText, PageTextGroup
from adt_press.utils.sync import gather_with_limit, run_async_task

logger = logging.getLogger(__name__)


@config.when(activity_strategy="llm")
def activities__llm(
    pdf_pages_by_id: dict[str, Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    pdf_text_groups_by_id: dict[str, PageTextGroup],
    processed_images_by_id: dict[str, ProcessedImage],
    activity_types_config: dict[str, ActivityTypeConfig],
) -> list[Activity]:
    """
    Generate activity definitions for sections with activity types.

    This node processes all sections that match configured activity types and calls the LLM
    to generate structured activity definitions. Activity types are configured in the
    activity_types_config map which specifies section type mappings and prompt configs.

    Args:
        pdf_pages_by_id: Mapping of page IDs to Page objects
        filtered_sections_by_page_id: Mapping of page IDs to their sections
        processed_pdf_texts_by_id: Mapping of text part IDs to PageText objects
        processed_images_by_id: Mapping of image part IDs to ProcessedImage objects
        activity_types_config: Mapping of activity type names to their configurations

    Returns:
        List of Activity objects with generated definitions
    """
    # Build reverse mapping: section_type -> (activity_type, prompt_config)
    section_type_to_activity: dict[str, tuple[ActivityType, ActivityTypeConfig]] = {}

    for activity_type_name, activity_config in activity_types_config.items():
        try:
            # Convert string to ActivityType enum
            activity_type = ActivityType(activity_type_name)

            # Map each section type to this activity type and config
            for section_type in activity_config.section_types:
                if section_type in section_type_to_activity:
                    logger.warning(f"Section type '{section_type}' is mapped to multiple activity types. Using first mapping.")
                    continue
                section_type_to_activity[section_type] = (activity_type, activity_config)

        except ValueError:
            logger.warning(f"Unknown activity type '{activity_type_name}' in config, skipping")
            continue

    async def generate_activities():
        tasks = []
        # Track which activity types and configs we're using for rate limiting
        configs_in_use = {}

        for page_sections in filtered_sections_by_page_id.values():
            page = pdf_pages_by_id[page_sections.page_id]

            for section in page_sections.sections:
                # Skip pruned sections
                if section.is_pruned:
                    continue

                # Check if this section type is mapped to an activity type
                section_type_str = section.section_type.value
                if section_type_str not in section_type_to_activity:
                    continue

                # Get the activity type and config for this section
                activity_type, activity_config = section_type_to_activity[section_type_str]

                texts: list[PageText] = []
                images: list[ProcessedImage] = []

                for part_id in section.part_ids:
                    if part_id.startswith("grp_"):
                        group = pdf_text_groups_by_id[part_id]
                        texts.extend(t for t in group.texts)
                    elif part_id.startswith("img_"):
                        images.append(processed_images_by_id[part_id])

                # Track this config for later rate limit calculation
                configs_in_use[activity_type.value] = activity_config.prompt_config

                # Generate activity definition using the specific prompt config
                tasks.append(
                    generate_activity_definition(
                        activity_config.prompt_config,
                        page,
                        section,
                        texts,
                        images,
                        activity_type,
                    )
                )

        if not tasks:
            return []

        # Use the minimum rate limit from all configs in use
        rate_limit = min(cfg.rate_limit for cfg in configs_in_use.values()) if configs_in_use else 10
        return await gather_with_limit(tasks, rate_limit)

    results = run_async_task(generate_activities)
    logger.info(f"Generated {len(results)} activities")
    return results


@config.when(activity_strategy="none")
def activities__none(
    pdf_pages_by_id: dict[str, Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_pdf_texts_by_id: dict[str, PageText],
    processed_images_by_id: dict[str, ProcessedImage],
    activity_types_config: dict[str, ActivityTypeConfig],
) -> list[Activity]:
    """
    Return empty list when activity generation is disabled.

    Args:
        pdf_pages_by_id: Mapping of page IDs to Page objects (unused)
        filtered_sections_by_page_id: Mapping of page IDs to their sections (unused)
        processed_pdf_texts_by_id: Mapping of text part IDs to PageText objects (unused)
        processed_images_by_id: Mapping of image part IDs to ProcessedImage objects (unused)
        activity_types_config: Activity type configurations (unused)

    Returns:
        Empty list
    """
    logger.info("Activity generation disabled (strategy=none)")
    return []
