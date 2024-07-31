from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from bfcl.types import TestCategory
from bfcl.utils.utils import write_list_of_dicts_to_file
from bfcl.eval_client.leaderboard import Leaderboard
from bfcl.model_handler.base import BaseHandler


class FailedResult(BaseModel):
    id: str
    test_category: str
    model_name: str
    is_valid: bool
    error_type: str
    error_message: str
    question: str
    func_doc: List[Dict]
    model_response_raw: str
    model_response_decoded: Optional[Any] = None
    possible_answer: Optional[Any] = None

    class Config:
        extra = "allow"


class Evaluator(ABC):
    def __init__(self, test_category: TestCategory, leaderboard: Leaderboard):
        self.test_category = test_category
        self.leaderboard = leaderboard
        self.test_data = self.test_category.load_test_data()
        self.possible_answer_data = self.test_category.load_possible_answer_data()
        self.language = self.test_category.test_language

    def pre_run_process(self, handler: BaseHandler):
        self.handler = handler
        self.model_name = handler.model_name
        self.model_response = self.handler.load_result_file(self.test_category)
        self.failure_record = []
        self.correct_count = 0

        assert (
            len(self.model_response)
            == len(self.test_data)
            == len(self.possible_answer_data)
        ), f"The length of the model result ({len(self.model_response)}) does not match the length of the prompt ({len(self.test_data)}) or possible answer ({len(self.possible_answer_data)}). Please check the input files for completeness. Model: {self.model_name}, Test Category: {self.test_category}"

        self.leaderboard.record_cost_latency(
            self.model_name, self.model_response
        )

    @abstractmethod
    def run(self):
        raise NotImplementedError

    def compute_score(self):
        accuracy = (
            self.correct_count / len(self.model_response)
            if len(self.model_response) > 0
            else 0
        )
        score_to_write = [
            {
                "accuracy": accuracy,
                "correct_count": self.correct_count,
                "total_count": len(self.model_response),
            }
        ]
        score_to_write.extend(
            [entry.dict(exclude_unset=True) for entry in self.failure_record]
        )
        score_file_path = self.test_category.get_score_file_path()

        write_list_of_dicts_to_file(
            score_to_write,
            score_file_path,
            subdir=self.handler.score_dir,
            appendMode=False,
        )

        self.leaderboard.record_score(
            self.model_name, self.test_category, accuracy, len(self.model_response)
        )
