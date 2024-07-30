from bfcl.types import TestCategory
from evaluator import FailedResult
from evaluator import Evaluator
from tqdm import tqdm
from utils import is_rest_format_output, is_executable_format_output
from bfcl.eval_client.checker.types import ExecutableCheckerResult
from bfcl.eval_client.leaderboard import Leaderboard
from bfcl.eval_client.checker.executable.exec_python_functions import *


class ExecutableEvaluator(Evaluator):
    
    def __init__(self, test_category: TestCategory, leaderboard: Leaderboard):
        super().__init__(test_category, leaderboard)
        if self.test_category != TestCategory.REST:
            self.get_real_time_exec_result()

    def run(self):
        for i in tqdm(range(len(self.model_response)), desc="Running tests"):
            entry_id = self.test_data[i]["id"]
            model_response_item_raw = self.model_response[i]["result"]
            question_item = self.test_data[i]["question"]
            func_doc_item = self.test_data[i]["function"]
            try:
                model_response_item_decoded = self.handler.decode_execute(
                    model_response_item_raw
                )
            except Exception as e:
                self.failure_record.append(
                    FailedResult(
                        id=entry_id,
                        test_category=self.test_category,
                        model_name=self.model_name,
                        is_valid=False,
                        error_type="executable_decoder:decoder_failed",
                        error_message=f"Failed to decode executable. {str(e)}",
                        question=question_item,
                        func_doc=func_doc_item,
                        model_response_raw=model_response_item_raw,
                    )
                )
                continue

            if self.test_category == TestCategory.REST:
                # REST is always single-functioned. Therefore we take the first one and pass it to the REST checker.
                if not is_rest_format_output(model_response_item_decoded):
                    self.failure_record.append(
                        FailedResult(
                            id=entry_id,
                            test_category=self.test_category,
                            model_name=self.model_name,
                            is_valid=False,
                            error_type="executable_decoder:rest_wrong_output_format",
                            error_message="Did not output in the specified format. Note: the model_result is wrapped in a string to ensure json serializability.",
                            question=question_item,
                            func_doc=func_doc_item,
                            model_response_raw=str(model_response_item_raw),
                            model_response_decoded=str(model_response_item_decoded),
                        )
                    )
                    continue
                checker = ExecutableChecker_REST(
                    func_doc_item,
                    model_response_item_decoded,
                    possible_answer_item,
                    self.test_category,
                    self.model_name,
                )
                checker_result: ExecutableCheckerResult = checker.run()

                # checker_result = executable_checker_rest(decoded_result[0], i)

            else:
                # This is for non-REST cases
                if not is_executable_format_output(model_response_item_decoded):
                    self.failure_record.append(
                        FailedResult(
                            id=entry_id,
                            test_category=self.test_category,
                            model_name=self.model_name,
                            is_valid=False,
                            error_type="executable_decoder:wrong_output_format",
                            error_message="Did not output in the specified format. Note: the model_result is wrapped in a string to ensure json serializability.",
                            question=question_item,
                            func_doc=func_doc_item,
                            model_response_raw=str(model_response_item_raw),
                            model_response_decoded=str(model_response_item_decoded),
                        )
                    )
                    continue

                checker = ExecutableChecker_Non_REST(
                    func_doc_item,
                    model_response_item_decoded,
                    possible_answer_item,
                    self.test_category,
                    self.model_name,
                )
                checker_result: ExecutableCheckerResult = checker.run()
                # checker_result = exec_checker(decoded_result, prompt_item, test_category)

            if checker_result.is_valid:
                self.correct_count += 1
            else:
                self.failure_record.append(
                    FailedResult(
                        id=entry_id,
                        test_category=self.test_category,
                        model_name=self.model_name,
                        is_valid=False,
                        error_type=checker_result.error_type,
                        error_message=checker_result.error_message,
                        question=question_item,
                        func_doc=func_doc_item,
                        model_response_raw=model_response_item_raw,
                        model_response_decoded=model_response_item_decoded,
                        model_executed_output=checker_result.execution_output,
                    )
                )

    def get_real_time_exec_result(self) -> None:
        self.expected_exec_result = []
        for possible_answer_entry in tqdm(
            self.possible_answer_data, desc="Getting Executable Expected Output"
        ):
            execution_result = []
            for ground_truth_entry in possible_answer_entry["ground_truth"]:
                execution_result.append(eval(ground_truth_entry))
                
            self.expected_exec_result.append(execution_result)