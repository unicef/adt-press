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

import evaluate
from mlflow.entities import Feedback
from mlflow.genai import scorer

from adt_eval.mlflow_base import MLflowEvaluatorBase
from adt_eval.utils.file import save_json
from adt_eval.utils.text_transcription.alignment import align_transcripts
from adt_eval.utils.text_transcription.metrics import jaccard
from adt_eval.utils.transcript_cleaner import standardize_transcript
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.config import TextGroupType, TextType
from adt_press.models.pdf import Page
from adt_press.models.text import PageTextGroups, Text, TextGroup
from adt_press.utils.languages import Language


@scorer
def jaccard_similarity_score(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Feedback:
    llm_texts = outputs['llm_texts']
    gs_texts = outputs['gs_texts']
    jaccard_similarity = jaccard(llm_texts, gs_texts)

    return Feedback(
        name="Jaccard similarity score",
        value=jaccard_similarity,
        rationale=""
    )

@scorer
def bleu_score(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Feedback:
    llm_texts = outputs['llm_texts']
    gs_texts = outputs['gs_texts']

    bleu = evaluate.load("bleu")
    results = bleu.compute(predictions=[" ".join(llm_texts)], references=[" ".join(gs_texts)])
    bleu_score = results['bleu']

    return Feedback(
        name="BLEU score",
        value=bleu_score,
        rationale=""
    )

class TextTranscriptionEvaluator(MLflowEvaluatorBase):
    """Evaluator for text transcription accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

        # Build text_types_config from global config
        self.text_types_config = {}
        for name, text_type in global_config.get("text_types", {}).items():
            params = dict(text_type)
            params["name"] = name
            self.text_types_config[name] = TextType.model_validate(params)

        # Build text_group_types_config from global config
        self.text_group_types_config = {}
        for name, text_group_type in global_config.get("text_group_types", {}).items():
            params = dict(text_group_type)
            params["name"] = name
            self.text_group_types_config[name] = TextGroupType.model_validate(params)

    async def process_case(self, step: int, test_case: Dict[str, Any], use_cached_llm_results) -> Dict[str, Any]:
        """Legacy path: TextTypeEvaluator runs via mlflow.genai.evaluate."""
        raise NotImplementedError("TextTypeEvaluator uses mlflow.genai.evaluate.")

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

            records.append(
                {
                    "inputs": {
                        "case_id": tc["id"],
                        "step": step,
                        "page_text": test["page_text_all"],
                        "page_image_path": str(page_image_path),
                        "book_title": test["book_name"],
                        "page_number": test["page_id"],
                        "label_studio_project": tc["project"],
                        "truth": truth,
                    },
                    "expectations": {},
                }
            )
        return records

    def predict_fn(self, **inputs: Any) -> Dict[str, Any]:
        page_text = inputs["page_text"]
        page_image_path = inputs["page_image_path"]

        page = Page(
            page_id=f"p{inputs['page_number']}",
            page_number=inputs["page_number"],
            text=page_text,
            page_image_path=str(page_image_path),
            images=[],
        )

        input_language_code = self.global_config.get("input_language", "en")
        language = Language.from_code(input_language_code)

        use_cached_llm_results = self.global_config["eval"]["use_cached_llm_results"]
        cache_path = f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{inputs['case_id']}.json"
        if use_cached_llm_results and os.path.exists(cache_path):
            page_texts = self.build_page_texts_from_log(Path(cache_path))
            print(f"Skipping LLM call for case {inputs['case_id']} and using cached results from the logs.")
        else:
            page_texts = self._run_coro(
                get_page_text(
                    str(self.output_dir),
                    f"eval_{inputs['case_id']}",
                    self.prompt_config,
                    self.text_types_config,
                    self.text_group_types_config,
                    page,
                    language,
                )
            )

            # save to cache
            save_json(cache_path, page_texts.model_dump())

        page_texts = page_texts.model_dump()
    
        #get llm transcript lines
        llm_texts = []
        for group in page_texts['groups']:
            for text_item in group['texts']:
                llm_texts.append(standardize_transcript(text_item['text']))

        truth = inputs['truth']
        #get gold strandard trancsript lines
        tt = [i for i in truth if i["from_name"] == "page_text_all_corrected"][0]
        text_content = tt["value"]["text"][0]
        gs_texts = [standardize_transcript(t) for t in text_content.split("\n\n")]

        return {
            "case_id": inputs["case_id"],
            "step": inputs["step"],
            "book_title": inputs["book_title"],
            "page_number": inputs["page_number"],
            "label_studio_url": (
                f"https://{self.label_studio_config.host}/projects/{inputs['label_studio_project']}/data?task={inputs['case_id']}"
            ),
            "page_image_path": str(Path(page_image_path).relative_to(self.output_dir)),
            "page_texts": page_texts,
            "llm_texts": llm_texts,
            "gs_texts": gs_texts,
        }

    def get_scorers(self) -> List[Any]:
        return [jaccard_similarity_score, bleu_score]

    def get_report_results_and_metrics(self, eval_results):
        result_df = eval_results.result_df.copy()
        results = []
        for index, row in result_df.iterrows():
            output = row.get("response", {})
            assessments = row.get("assessments", {})

            page_texts =output['page_texts']
            llm_texts = output['llm_texts']
            gs_texts = output['gs_texts']

            ####### Align LLM transcript to Gold Standard transcript
            alignment = align_transcripts(llm_texts=llm_texts, gs_texts=gs_texts, threshold=0.5)
            matches = alignment["matches"]

            #get metrics
            eval_metrics =[]
            for assessment in assessments:
                eval_metrics.append({
                    "name": assessment['assessment_name'],
                    "value": round(assessment['feedback']['value'], 2)
                })

            results.append({
                "id": output.get("case_id"),
                'step': index+1,
                'page_number': output['page_number'],
                'book_title': output['book_title'],
                'page_image_path': output['page_image_path'],
                'score': 0,
                'page_texts': page_texts,
                'matches': matches,
                'metrics': eval_metrics,
            })

        metrics = {
            "score": eval_metrics[0]['value'] ,
        }
        return results, metrics
