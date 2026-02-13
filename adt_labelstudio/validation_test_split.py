
from typing import Dict, List
import pandas as pd
from adt_labelstudio.base import BaseTask
from adt_eval.utils.transcript_cleaner import standardize_transcript, normalize_transcript

class ValidationTestSplitTask(BaseTask):

    def get_single_annotation(self, gs_annotations:pd.DataFrame, book_id:str, page_id:int) -> Dict:
        '''Retrieve a single annotation from a dataframe of annotations.
        In this case lookup is done by book ID and page ID as this defines the annotation task.'''
        
        gs_annotation = gs_annotations[(gs_annotations['book_id'] == book_id) & (gs_annotations['page_id'] == page_id)]
 
        if gs_annotation.shape[0] == 0:
            raise ValueError(f"No annotation found for book '{book_id}', page ID {page_id}")
        if gs_annotation.shape[0] > 1:
            raise ValueError(f"Multiple annotations found for book '{book_id}', page ID {page_id}")
        
        return gs_annotation.iloc[0].to_dict()
    
    def populate_task_data(self, page_dict:Dict) -> Dict:
        ''' Define the data used to render the task in LabelStudio '''

        data = {
                    "book_id": page_dict['book_id'],
                    "book_title": page_dict['book_title'],
                    "page_id": page_dict['page_id'],
                    "page_image": f"azure-blob://adt-pipeline/evaluation/gold_standard/pages/{page_dict['book_id']}__page_{page_dict['page_id']}.png",
                }
        
        return data
    
    def load_llm_log_to_df(self, llm_log:Dict) -> pd.DataFrame:
        # We don't use LLM output for this
        pass

    def load_gs_annotation_to_df(self, gs_annotation:Dict) -> pd.DataFrame:
        # We don't use previous annotations for this
        pass

    def merge_gs_with_llm(self, gs_df: pd.DataFrame, llm_df: pd.DataFrame) -> pd.DataFrame:
        # We don't need to merge these for this 
        pass

    def populate_task_predictions(self, page_dict: Dict) -> List[Dict]:
        ''' Define the predictions (pre-annotations) used to render the task in LabelStudio '''
    
        result = [
                    {
                        "type": "choices",
                        "value": {
                            "choices": [page_dict['split']]
                        },
                        "to_name": "page_image",
                        "from_name": "split"
                        },
                        {
                        "type": "choices",
                        "value": {
                            "choices": ["Yes"]
                        },
                        "to_name": "page_image",
                        "from_name": "include"
                    }
                ]
        predictions = [{"result": result}]
        return predictions