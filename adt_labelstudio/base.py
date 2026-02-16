
from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List, Optional
import pandas as pd

class BaseTask(ABC):
    # Read input from log
    # Pass to next task

    def get_llm_log(self, f):
        ''' Returns the LLM log and its corresponding book name / page number '''

        # Read json log
        with open(f) as json_file:
            llm_log = json.load(json_file)
        
        book_id = llm_log['inputs']['page']['book_id']
        page_number = llm_log['inputs']['page']['page_number']

        return llm_log, book_id, page_number
    
    @abstractmethod
    def get_single_annotation(self, gs_annotations: pd.DataFrame, book_id: str, page_id: int) -> Dict:
        '''Retrieve a single annotation from a dataframe of annotations'''
        raise NotImplementedError

    @abstractmethod
    def populate_task_data(self, gs_annotation: Dict) -> Dict:
        ''' Define the data used to render the task in LabelStudio '''
        raise NotImplementedError

    @abstractmethod
    def load_llm_log_to_df(self, llm_log: Dict) -> pd.DataFrame:
        ''' Converts json log from an LLM run to a dataframe that can be used'''
        raise NotImplementedError
    
    @abstractmethod
    def load_gs_annotation_to_df(self, gs_annotation: Dict) -> pd.DataFrame:
        ''' Converts Gold Standard annotation from LabelStudio to a dataframe that can be used '''
        raise NotImplementedError
    
    @abstractmethod
    def merge_gs_with_llm(self, gs_df: pd.DataFrame, llm_df: pd.DataFrame) -> pd.DataFrame:
        ''' Merge Gold Standard dataframe with LLM dataframe based on exact text matches after normalization '''
        raise NotImplementedError

    @abstractmethod
    def populate_task_predictions(self, matched_df: pd.DataFrame) -> List[Dict]:
        ''' Define the predictions (pre-annotations) used to render the task in LabelStudio '''
        raise NotImplementedError
    
    def create_one_task(self, task_data: Dict, task_predictions: List[Dict]) -> Dict:
        ''' Create dictionary representing a single task in LabelStudio, and save to file '''
        
        task = {"data": task_data, "predictions": task_predictions}

        return task
    
