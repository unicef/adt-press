from typing import Any, Dict, Iterable, List, Tuple


def build_eval_translations(
    page_text_list: Iterable[Tuple[str, str, str]],
    page_text_translations: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Join translations to base text by text_id.

    Raises:
        ValueError: If any translation text_id is missing from page_text_list.
    """
    base_text_by_id = {text_id: base_text for text_id, _text_type, base_text in page_text_list}

    eval_items: List[Dict[str, Any]] = []
    missing_ids: List[str] = []

    for translation in page_text_translations:
        text_id = translation.get("text_id")
        base_text = base_text_by_id.get(text_id)
        if base_text is None:
            missing_ids.append(text_id)
            continue
        eval_items.append(
            {"text_id": text_id, "base_text": base_text, "translation": translation.get("text"), "reasoning": translation.get("reasoning")}
        )

    if missing_ids:
        missing_ids_display = ", ".join(str(i) for i in missing_ids)
        raise ValueError(f"Missing base text for text_id(s): {missing_ids_display}")

    return eval_items


def build_eval_translations_with_scores(
    page_text_scorer_scores_list: List[Dict[str, Any]],
    page_text_translations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    for translation in page_text_translations:
        text_id = translation.get("text_id")

        if not text_id:
            continue

        for entry in page_text_scorer_scores_list:
            if entry.get("text_id") == text_id:
                translation["is_translation_acceptable"] = entry.get("is_translation_acceptable")
                translation["rationale"] = entry.get("rationale")
                break

    return page_text_translations
