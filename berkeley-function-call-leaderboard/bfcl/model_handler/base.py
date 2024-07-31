import os
from typing import Union, List, Dict
from abc import ABC, abstractmethod
from bfcl.constants import *
from bfcl.utils.utils import load_json_file, write_single_dict_to_file
from bfcl.types import TestCategory


class BaseHandler(ABC):
    model_style: str

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.7,
        top_p: int = 1,
        max_tokens: int = 1000,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        self.model_name_underscore = self.model_name.replace("/", "_")
        self.result_dir = os.path.join(RESULT_FILE_DIR, self.model_name_underscore)
        self.score_dir = os.path.join(SCORE_FILE_DIR, self.model_name_underscore)

    @classmethod
    @abstractmethod
    def supported_models(cls) -> List[str]:
        pass

    @abstractmethod
    def inference(self):
        """Fetch response from the model."""
        pass

    @abstractmethod
    def decode_ast(self, result, language):
        """Takes raw model output and converts it to the standard AST checker input."""
        pass

    @abstractmethod
    def decode_execute(self, result):
        """Takes raw model output and converts it to the standard execute checker input."""
        pass

    def write_result(self, result: Union[Dict, List[Dict]]) -> None:
        """Write the model responses to the file."""

        # When writing only one result
        if isinstance(result, dict):
            result = [result]

        # FIXME better way to get file path 
        for entry in result:
            test_category = entry["id"].rsplit("_", 1)[0]
            file_to_write = f"gorilla_openfunctions_v1_test_{test_category}_result.json"
            write_single_dict_to_file(
                entry, file_to_write, subdir=self.result_dir, appendMode=True
            )

        print(f'Saved model responses at "{self.result_dir}".')

    def load_result_file(self, test_category: TestCategory) -> List[Dict]:
        """Load the model responses from the result file. Returns an empty list if the file is not found."""

        if not self.result_dir.exists():
            return []

        file_path = os.path.join(self.result_dir, test_category.get_file_path())

        if not os.path.exists(file_path):
            return []

        return load_json_file(file_path)

    def load_score_file(self, test_category: TestCategory) -> List[Dict]:
        """Load the model score from the score file. Returns an empty list if the file is not found."""

        if not self.score_dir.exists():
            return []

        file_path = os.path.join(self.score_dir, test_category.get_file_path())

        if not os.path.exists(file_path):
            return []

        return load_json_file(file_path)
