"""Text type evaluation implementation.

Some notes on the scoring of matches:
- The LabelStudio text_type dataset sometimes had errors in the text_transcript that were later corrected. Thus, in this script, we correct some of these errors as well (for example, removing double spaces).
- Mismatches are often introduced by mismatched directional quotations, e.g. ’,”,‘,“. These are replaced by non-directional quotations in both the LLM output and the Gold Standard.
- The match strategy implemented is a greedy one.
    - For each line in the LLM output, a list of labels is created (where each item in the list is the text type corresponding to one repetition of the line in the LLM output).
    - For each line in the Gold Standard transcript, we seek a match and, if the line matches, one text type item is 'used up' from the list.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from mlflow.entities import Feedback
from mlflow.genai import scorer
from litellm import completion

from adt_eval.mlflow_base import MLflowEvaluatorBase
from adt_eval.utils.transcript_cleaner import normalize_transcript, standardize_transcript
from adt_press.utils.languages import Language
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import TextGroupType, TextType
from adt_press.models.pdf import Page
from adt_press.models.text import PageTextGroups, Text, TextGroup
from adt_press.models.eval.text_translation import TranslationEvalOutputs
from adt_press.utils.languages import Language
from adt_eval.utils.file import encode_image_to_base64

TRANSLATION_SCORER_SYSTEM_PROMPT = """
You are an expert multilingual translation evaluator specializing in children’s educational textbooks.
You evaluate translations with a strict editorial standard suitable for K–12 instructional materials.

Your task is NOT to translate. Your task is to STRICTLY JUDGE whether a translation is ACCEPTABLE or NOT ACCEPTABLE.

You will be provided with:
- input_language: the source language code.
- input_text: the exact source text extracted from the textbook.
- output_language: the target language code.
- output_text: the model-generated translation.
- page_image: an image of the textbook page (base64).

Use the image ONLY to understand:
- the role of the text (heading, label, instruction, paragraph, caption)
- the subject matter (math, science, literacy, etc.)
- the layout context (placement on page)

If the image is unclear or partially visible, do not assume or invent anything.
Your decision must be based primarily on input_text and output_text.

----------------------------------------------------
DEFINITION OF “ACCEPTABLE TRANSLATION”
----------------------------------------------------
A translation is ACCEPTABLE only if ALL conditions below are fully satisfied.
If you are unsure whether an error is minor or major, treat it as major.

### 1. ADEQUACY (meaning preservation — strict)
- The translation preserves the complete meaning.
- No omissions, distortions, additions, or reinterpretations.
- All quantities, names, terminology, and logical relationships are correctly preserved.
- No ambiguity introduced.

### 2. FLUENCY & NATURALNESS (strict editorial standard)
The target-language text must:
- Be grammatically correct.
- Use natural, idiomatic phrasing for children’s educational materials.
- Sound like authentic textbook language for that language and grade level.
- Avoid literal, machine-like, or awkward phrasing even if meaning is understandable.
- Use appropriate stylistic form for headings, labels, and instructions.

For ALL languages:
If the translation sounds unnatural, unidiomatic, or does not resemble real textbook phrasing,
→ NOT ACCEPTABLE.

### 3. TERMINOLOGY & SUBJECT ACCURACY
- Terminology must match grade-level norms for the target language.
- Technical and academic concepts must remain correct.
- No mistranslation that could cause misunderstanding of a concept.

### 4. CONTEXTUAL APPROPRIATENESS (image-based)
- Headings must read like headings.
- Labels must read like labels.
- Instructions must read like instructions.
- The style and tone must fit children’s textbooks.

----------------------------------------------------
ADDITIONAL LANGUAGE-PAIR GUIDELINES (ENGLISH → SPANISH)
----------------------------------------------------
If input_language = "en" and output_language = "es", apply the following STRICT rules:

### Spanish Textbook Fluency Rules
Translations resembling any of the following patterns are NOT ACCEPTABLE:
- Literal English calques (e.g., “NÚMEROS IMPACTANTES”, “PROBLEMAS DE HISTORIAS SOBRE...”)
- Machine-like verb constructions
- Unnatural noun constructions
- Awkward or non-standard academic phrasing
- Any phrasing not typically found in real Spanish K–12 textbooks

The translation must sound like a native-authored Spanish textbook, not a direct conversion.

### Non-acceptable Spanish Indicators
If the Spanish includes unnatural literal phrasing, incorrect register, awkward expressions, or machine-like style,
treat as major errors, even if meaning is technically understandable.

----------------------------------------------------
ERROR SEVERITY (STRICT INTERPRETATION)
----------------------------------------------------

### MAJOR ERRORS (→ ALWAYS NOT ACCEPTABLE)
- Any mistranslation or incorrect meaning.
- Any omitted or added content.
- Incorrect or misleading terminology.
- Any unnatural, awkward, or machine-like phrasing.
- Any grammatical error.
- Any mismatch with the text’s function (heading/label/etc.).
- Any stylistic issue that would not pass editorial review.

### MINOR ERRORS (rare, acceptable only if meaning + fluency + context are perfect)
- Very small stylistic differences that do NOT affect idiomaticity, clarity, tone, or naturalness.
- Harmless formatting differences.

If unsure, classify the issue as major.

----------------------------------------------------
EVALUATION PROCESS (INTERNAL — DO NOT OUTPUT)
----------------------------------------------------
1. Assess adequacy.
2. Assess fluency & naturalness with strict textbook standards.
3. Assess terminology accuracy.
4. Assess contextual appropriateness using the image.
5. Apply strict error classification.
6. Decide ACCEPTABLE vs NOT ACCEPTABLE.

Do NOT reveal chain-of-thought.

----------------------------------------------------
OUTPUT FORMAT
----------------------------------------------------
Return ONLY the following JSON object:

- is_translation_acceptable: boolean
- rationale: short English explanation (1–3 sentences) summarizing the key reasons.

Do NOT output anything else.
"""


@scorer
def is_acceptable_translation(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Feedback:

    page_text_list = inputs.get("page_text_list", [])
    source_language = inputs.get("base_language", "en")
    target_language = inputs.get("target_language", "es")
    page_text_translations = outputs.get("page_text_translations", [])

    if isinstance(source_language, Language):
        source_language = source_language.model_dump()

    if isinstance(target_language, Language):
        target_language = target_language.model_dump()

    #get image  
    image_path = inputs.get("image_path", "")
    image_b64 = encode_image_to_base64(image_path)

    #build eval_page_text_translations
    eval_page_text_translations = []
    for i, page_text_translation in enumerate(page_text_translations):
        _, _, base_text = page_text_list[i]
        translation_entry = {
            "text_id": page_text_translation["text_id"],
            "base_text": base_text,
            "translation": page_text_translation["text"],
        }
        eval_page_text_translations.append(translation_entry)


    if image_b64:
        user_content = [
            {
                "type": "text",
                "text": (
                    "Evaluate whether the following Translation is ACCEPTABLE, "
                    "using the criteria in the system prompt.\n\n"
                    f"source_language: {source_language}\n"
                    f"target_language: {target_language}\n"
                    f"List of translations :\n\n{eval_page_text_translations}\n\n"
                    "Below is the textbook page image in base64 format. "
                    "Use it only to understand the context and how the text is used:\n"
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_b64}"
                },
            },
        ]
    else:
        user_content = (
            "Evaluate whether the following Translation is ACCEPTABLE, "
            "using the criteria in the system prompt.\n\n"
            f"source_language: {source_language}\n"
            f"target_language: {target_language}\n"
            f"List of translations :\n\n{eval_page_text_translations}\n\n"
        )

    messages = [
        {"role": "system", "content": TRANSLATION_SCORER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    eval_output = completion(
        model="gpt-5",
        messages=messages,
        response_format=TranslationEvalOutputs,
    )

    # Align with how you're handling other response_format=Pydantic calls
    msg = eval_output.choices[0].message
    translation_eval = TranslationEvalOutputs.model_validate_json(msg.content)
    translation_output = translation_eval.model_dump()['outputs']

    #calculating the translation eval summary
    summary_of_translations = [translation['is_translation_acceptable'] for translation in translation_output]
    summary_of_failed_translations = [
        {"text_id": translation["text_id"], "rationale": translation["rationale"]}
        for translation in translation_output
        if not translation["is_translation_acceptable"]
    ]

    
    #calculating the translation eval metric
    metric= round(sum(summary_of_translations) / len(summary_of_translations), 2)
    
    #calculating the translation eval rationale
    if summary_of_failed_translations:
        combined_rationale = "The folowing translations are not acceptable:\n\n"
        for entry in summary_of_failed_translations:
            combined_rationale += f"- text_id: {entry['text_id']}\n  reason: {entry['rationale']}\n\n" 
    else:
        combined_rationale = "All translations are acceptable."
    
    return Feedback(
        name="text_translation_score",
        value=metric,
        rationale=combined_rationale,
    )


class TextTranslationEvaluator(MLflowEvaluatorBase):
    """Evaluator for text translation accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

        self.base_language = Language.from_code(global_config.get("input_language", "en"))
        self.target_language = Language.from_code("es")

    def build_page_texts_from_log(self, fpath: Path) -> PageTextGroups:
        """Build PageTextGroups object from logged JSON file, as an alternative to LLM call."""
        with open(fpath, "r", encoding="utf8") as f:
            page_texts = json.load(f)
            output = page_texts["output"]

        page_text_groups = []
        for g in output["groups"]:
            page_texts = []
            for t in g["texts"]:
                page_text = Text(text_id=t["text_id"], text=t["text"], text_type=t["text_type"])
                page_texts.append(page_text)
            page_text_group = TextGroup(group_id=g["group_id"], group_type=g["group_type"], texts=page_texts)
            page_text_groups.append(page_text_group)
        page_texts = PageTextGroups(page_id=output["page_id"], groups=page_text_groups, reasoning=output["reasoning"])

        return page_texts

    async def process_case(self, step: int, test_case: Dict[str, Any], use_cached_llm_results) -> Dict[str, Any]:
        """Legacy path: TextTypeEvaluator runs via mlflow.genai.evaluate."""
        raise NotImplementedError("TextTypeEvaluator uses mlflow.genai.evaluate.")

    def build_eval_dataset(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for step, tc in enumerate(cases):
            test = tc["data"]
            latest_annotation = max(tc["annotations"], key=lambda x: x["updated_at"])
            truth = [i["result"] for i in tc["annotations"] if i["id"] == latest_annotation["id"]][0]
            page_image_path = self.download_azure_image(
                test["page_image"],
                f"text_extraction_page_{tc['id']}.png",
            )
            
            page_text_list = [
                (
                    t["id"],
                    t["value"]["taxonomy"][0][0] if t["value"].get("taxonomy") else "",
                    t["value"]["text"]
                )
                for t in truth
            ]

            records.append(
                {
                    "inputs": {
                        "case_id": tc["id"],
                        "step": step,
                        "page_text_all": test["page_text_all"],
                        "page_image_path": str(page_image_path),
                        "book_title": test["book_name"],
                        "page_number": test["page_id"],
                        "label_studio_project": tc["project"],
                        "page_text_list": page_text_list,
                        "base_language": self.base_language,
                        "target_language": self.target_language,
                    },
                    "expectations": {},
                }
            )

        
        return records

    def predict_fn(self, **inputs: Any) -> Dict[str, Any]:
        page_text_all = inputs["page_text_all"]
        page_image_path = inputs["page_image_path"]
        page_text_list = inputs["page_text_list"]
        
        page_text_translations = []

        use_cached_llm_results = self.global_config["eval"]["use_cached_llm_results"]
        cache_path = f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{inputs['case_id']}.json"
        if use_cached_llm_results and os.path.exists(cache_path):
            #page_texts = self.build_page_texts_from_log(Path(cache_path))
            print(f"Skipping LLM call for case {inputs['case_id']} and using cached results from the logs.")
        else:
            output_page_text_translations = self._run_coro(
                get_text_translation(
                    self.prompt_config,
                    page_text_list,
                    self.base_language,
                    self.target_language,
                )
            )

            page_text_translations = [
                page_text_translation.model_dump()
                for page_text_translation in output_page_text_translations
            ]

        return {
            "case_id": inputs["case_id"],
            "step": inputs["step"],
            "book_title": inputs["book_title"],
            "page_number": inputs["page_number"],
            "label_studio_url": (
                f"https://{self.label_studio_config.host}/projects/{inputs['label_studio_project']}/data?task={inputs['case_id']}"
            ),
            "page_text_all": page_text_all,
            "page_image_path": str(Path(page_image_path).relative_to(self.output_dir)),
            "page_text_translations": page_text_translations,
        }

    def get_scorers(self) -> List[Any]:
        return [is_acceptable_translation]

    def get_report_results_and_metrics(self, eval_results):
        result_df = eval_results.result_df.copy()
        results: List[Dict[str, Any]] = []
        for _, row in result_df.iterrows():
            # inputs = row.get("request", {})
            outputs = row.get("response", {})
            assessments = row.get("assessments", {})
            rationale = assessments[0].get("rationale", {})
            matches = json.loads(rationale) if rationale else []
            score = row.get("text_type_score/value") or 0

            results.append(
                {
                    "id": outputs.get("case_id"),
                    "book_title": outputs.get("book_title"),
                    "page_number": outputs.get("page_number"),
                    "label_studio_url": outputs.get("label_studio_url"),
                    "page_text": outputs.get("page_text"),
                    "page_image_path": outputs.get("page_image_path"),
                    "page_texts": outputs.get("page_texts"),
                    "score": score,
                    "score_count": len(matches),
                    "step": outputs.get("step"),
                    "matches": matches,
                }
            )

        metrics = {key.replace("/mean", ""): value for key, value in eval_results.metrics.items()}
        metrics["score"] = metrics.get("text_type_score", 0.0)
        return results, metrics
