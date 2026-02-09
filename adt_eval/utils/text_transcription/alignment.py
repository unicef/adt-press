from typing import Any


def _char_jaccard_similarity(text1: str, text2: str) -> float:
    """Compute character-level Jaccard similarity between two strings."""
    s1 = set(text1)
    s2 = set(text2)
    union = s1.union(s2)
    if not union:
        return 1.0
    return len(s1.intersection(s2)) / len(union)


def align_transcripts(
    llm_texts: list[str],
    gs_texts: list[str],
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Greedily align LLM transcript lines to gold-standard lines."""
    matches: list[dict[str, str | None]] = []
    n_matched = 0
    n_mismatched = 0

    remaining_llm = llm_texts.copy()
    remaining_gs = gs_texts.copy()

    exact_matched_gs: list[str] = []
    for expected in remaining_gs:
        if expected in remaining_llm:
            matches.append({"expected": expected, "actual": expected})
            remaining_llm.remove(expected)
            exact_matched_gs.append(expected)
            n_matched += 1

    for expected in exact_matched_gs:
        remaining_gs.remove(expected)

    for expected in remaining_gs:
        best_match = None
        best_similarity = 0.0

        for actual in remaining_llm:
            similarity_score = _char_jaccard_similarity(actual, expected)
            if similarity_score > best_similarity:
                best_similarity = similarity_score
                best_match = actual

        if best_match is not None and best_similarity >= threshold:
            matches.append({"expected": expected, "actual": best_match})
            remaining_llm.remove(best_match)
            n_matched += 1
        else:
            matches.append({"expected": expected, "actual": None})
            n_mismatched += 1

    for actual in remaining_llm:
        matches.append({"expected": None, "actual": actual})
        n_mismatched += 1

    return {
        "matches": matches,
        "n_matched": n_matched,
        "n_mismatched": n_mismatched,
    }
