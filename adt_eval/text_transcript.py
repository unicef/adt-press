"""Text type evaluation implementation.

Some notes on the scoring of matches:
- The LabelStudio text_type dataset sometimes had errors in the text_transcript that were later corrected. Thus, in this script, we correct some of these errors as well (for example, removing double spaces).
- Mismatches are often introduced by mismatched directional quotations, e.g. ’,”,‘,“. These are replaced by non-directional quotations in both the LLM output and the Gold Standard.
- The match strategy implemented is a greedy one.
    - For each line in the LLM output, a list of labels is created (where each item in the list is the text type corresponding to one repetition of the line in the LLM output).
    - For each line in the Gold Standard transcript, we seek a match and, if the line matches, one text type item is 'used up' from the list.
"""

from pathlib import Path
from typing import Any, Dict

import mlflow
import os
import json
import pandas as pd
import evaluate

from adt_eval.base import BaseEvaluator
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.pdf import Page
from adt_eval.utils.transcript_cleaner import normalize_transcript, standardize_transcript
from adt_eval.utils.metrics import *
from adt_press.models.text import *


class TextTranscriptEvaluator(BaseEvaluator):
    """Evaluator for text type accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

    def build_page_texts_from_log(self, fpath: Path) -> PageTexts:
                '''Build PageTexts object from logged JSON file, as an alternative to LLM call.'''
                with open(fpath, "r", encoding="utf8") as f:
                    page_texts = json.load(f)
                    output = page_texts['output']

                page_text_groups = []
                for g in output['groups']: 
                    page_texts = []
                    for t in g['texts']:
                        page_text = PageText(text_id=t['text_id'], text=t['text'], text_type=t['text_type'])
                        page_texts.append(page_text) 
                    page_text_group = PageTextGroup(group_id = g['group_id'], group_type = g['group_type'], texts=page_texts)
                    page_text_groups.append(page_text_group)
                page_texts = PageTexts(page_id=output['page_id'], groups=page_text_groups, reasoning=output['reasoning'])

                return page_texts

    async def process_case(self, step: int, tc: Dict[str, Any], use_cache: bool) -> Dict[str, Any]:
        """Process a single test case."""

        ## Get the gold standard for test case
        test = tc["data"]
        text = test["page_text_all"]
        page_image_url = test["page_image"]
        book_title = test["book_name"]
        page_number = test["page_id"]

        page_image_path = self.download_azure_image(page_image_url, f"text_extraction_page_{tc['id']}.png")

        # Get the most recent annotation
        latest_annotation = max(tc['annotations'], key=lambda x: x['updated_at'])
        truth = [i["result"] for i in tc["annotations"] if i['id']==latest_annotation['id']][0]

        result = {
            "id": tc["id"],
            "book_title": book_title,
            "page_number": page_number,
            "label_studio_url": f"https://{self.label_studio_config.host}/projects/{tc['project']}/data?task={tc['id']}",
            "page_text": text,
            "page_image_path": str(page_image_path.relative_to(self.output_dir)),
        }

        ####### Get the LLM candidate output for test case
        # Create page object for processing
        page = Page(page_id=f"p{test['page_id']}", page_number=test["page_id"], text=text, page_image_path=str(page_image_path), images=[])

        print(f"[{tc['id']:8d}] {text[:65].replace('\n', ' '):<70s}")

        # Call the LLM for text type classification
        if (use_cache==False) or (not os.path.exists(f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{tc['id']}.json")):
            page_texts = await get_page_text(str(self.output_dir), f"eval_{tc['id']}", self.prompt_config, page)
        else:
            print(f"Skipping LLM call for case {tc['id']} and using cached results from the logs.")
            page_texts = self.build_page_texts_from_log(Path(f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{tc['id']}.json"))
        
        result["page_texts"] = page_texts.model_dump()

        ## Get list of LLM transcript lines
        llm_texts = []
        for group in page_texts.groups:
            for text_item in group.texts:
                llm_texts.append(standardize_transcript(text_item.text))

        ####### Get list of Gold Standard transcript lines

        tt = [i for i in truth if i["from_name"] == "page_text_all_corrected"][0]
        text_content = tt["value"]["text"][0]
        gs_texts = [standardize_transcript(t) for t in text_content.split("\n\n")]

        ####### Calculate metrics
        
        # Calculate Jaccard
        jaccard_similarity = jaccard(gs_texts, llm_texts)
        print("Jaccard: ", jaccard_similarity)

        # Calculate Bleu
        bleu = evaluate.load("bleu")
        results = bleu.compute(predictions=[" ".join(llm_texts)], references=[" ".join(gs_texts)])
        bleu_score = results['bleu']
        print("BLEU: ", bleu_score)

        result.update(
            {
                "jaccard": jaccard_similarity,
                "bleu": bleu_score,
            }
        )

        ####### Align LLM transcript to Gold Standard transcript
        matches = []
        n_matched = 0
        n_mismatched = 0

        # Loop through GS texts, seeking matches in LLM texts
        gs_texts_copy = gs_texts.copy()
        for i in gs_texts_copy:
            if i in llm_texts:
                matches.append({"expected": i, "actual": i})
                llm_texts.remove(i)
                gs_texts_copy.remove(i)
                n_matched+=1

        #Remaing set after exact match full iteration
        for i in gs_texts_copy:
            # Find the best match among all llm_texts
            best_match = None
            best_similarity = 0.0
            for j in llm_texts:
                intersection = set(j).intersection(set(i))
                union = set(j).union(set(i))
                similarity_score = len(intersection) / len(union)
                print(f"similarity_score: {similarity_score:.3f}")
                
                if similarity_score > best_similarity:
                    best_similarity = similarity_score
                    best_match = j
            
            # Match only if best similarity is at least 50%
            if best_similarity >= 0.5:
                matches.append({"expected": i, "actual": best_match})
                llm_texts.remove(best_match)
                n_matched += 1
            else:
                matches.append({"expected": i, "actual": None})
                n_mismatched += 1

        # Add unmatched llm texts
        for i in llm_texts:
            matches.append({"expected": None, "actual": i})
            n_mismatched+=1

        # Store
        result.update(
            {
                "score": n_matched / (n_matched + n_mismatched/2), # Fraction of lines matched, no double counting of mismatches
                "score_count": len(gs_texts), # Total lines in original GS transcript
                "matches": matches,
            }
        )

        # Log to MLflow
        mlflow.log_dict(page.model_dump(), f"inputs/{step}.json")

        mlflow.log_table(pd.DataFrame(matches), f"results/{step}.json")

        mlflow.log_metric("jaccard", jaccard_similarity, step=step)
        mlflow.log_metric("bleu", bleu_score, step=step)

        return result
