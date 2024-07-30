import os
import time
import json
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm

import requests
from bfcl.eval_client.checker.types import ExecutableCheckerResult
from bfcl.eval_client.checker.executable.executable_checker_constants import (
    REAL_TIME_MATCH_ALLOWED_DIFFERENCE,
)
from bfcl.types import TestCategory, TestLanguage

from bfcl.eval_client.checker.executable.exec_python_functions import *


class ExecutableChecker_Non_REST:

    def __init__(
        self,
        model_response,
        expected_exec_result,
        evaluation_metric,
        test_category: TestCategory,
        is_sanity_check=False,
    ):
        self.model_response = model_response
        self.expected_exec_result = expected_exec_result
        self.evaluation_metric = evaluation_metric
        self.test_category = test_category
        self.is_sanity_check = is_sanity_check
        # self.cache_dir = cache_dir
        # self.data_dir = Path(__file__, "../../../../..").resolve() / "data"
        # self.rest_api_ground_truth_file_path = (
        #     self.data_dir / "api_status_check_ground_truth_REST.jsonl"
        # )
        # self.executable_ground_truth_file_path = (
        #     self.data_dir / "api_status_check_ground_truth_executable.jsonl"
        # )

        # self.rest_eval_response_v5_file_path = (
        #     self.data_dir / "rest-eval-response_v5.jsonl"
        # )
        # with open(self.rest_eval_response_v5_file_path, "r") as file:
        #     self.rest_eval_response_data = [json.loads(line) for line in file]

        # self._cached_exec_api_ground_truth_results = {}

    def run(self) -> ExecutableCheckerResult:
        if self.test_category == TestCategory.EXECUTABLE_SIMPLE:
            if len(self.model_response) != 1:
                return ExecutableCheckerResult(
                    is_valid=False,
                    error_type="simple_exec_checker:wrong_count",
                    error_message=f"Wrong number of functions provided. Expected 1, but got {len(self.model_response)}.",
                )
            return self._simple_executable_checker(
                self.model_response[0],
                self.expected_exec_result[0],
                self.evaluation_metric,
                self.is_sanity_check,
            )
        else:
            return self._parallel_executable_checker_no_order(
                self.model_response,
                self.expected_exec_result,
                self.evaluation_metric,
            )


    def _get_updated_rest_ground_truth_data(self) -> List[Dict]:
        output_file_path = self.cache_dir / self.rest_api_ground_truth_file_path.name
        if output_file_path.exists():
            with open(output_file_path, "r") as file:
                modified_data = [json.loads(line) for line in file]
            print(
                f'Loaded cached REST API ground truth file with replaced placeholders from "{output_file_path}" 🦍.'
            )
        else:
            placeholders = {}
            env_vars = (
                "GEOCODE_API_KEY",
                "RAPID_API_KEY",
                "OMDB_API_KEY",
                "EXCHANGERATE_API_KEY",
            )
            for var in env_vars:
                assert (
                    api_key := os.getenv(var)
                ), f"Please provide your {var} in the `.env` file."
                placeholders["YOUR-" + var.replace("_", "-")] = api_key
            print("All API keys are present.")

            def replace_placeholders(data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            replace_placeholders(value)
                        elif isinstance(value, str):
                            for placeholder, actual_value in placeholders.items():
                                if (
                                    placeholder in value
                                ):  # Check if placeholder is in the string
                                    data[key] = value.replace(placeholder, actual_value)
                elif isinstance(data, list):
                    for idx, item in enumerate(data):
                        if isinstance(item, (dict, list)):
                            replace_placeholders(item)
                        elif isinstance(item, str):
                            for placeholder, actual_value in placeholders.items():
                                if (
                                    placeholder in item
                                ):  # Check if placeholder is in the string
                                    data[idx] = item.replace(placeholder, actual_value)
                return data

            modified_data = []
            with open(self.rest_api_ground_truth_file_path, "r") as file:
                for line in file:
                    try:
                        data = replace_placeholders(json.loads(line))
                        modified_data.append(data)
                    except json.JSONDecodeError:
                        # Handle the case where a line is not a valid JSON object
                        print("Invalid JSON line!")

            with open(output_file_path, "w") as f:
                for modified_line in modified_data:
                    f.write(json.dumps(modified_line) + "\n")
            print(
                f"Saved REST API ground truth file with replaced placeholders at {output_file_path} 🦍."
            )

        return modified_data
 

    def _simple_executable_checker(
        self,
        function_call: str,
        expected_result,
        expected_result_type: str,
        is_sanity_check=False,
    ):

        try:
            exec_output = eval(function_call)
        except Exception as e:
            return ExecutableCheckerResult(
                is_valid=False,
                error_type="executable_checker:execution_error",
                error_message=f"Error in execution: {repr(function_call)}. Error: {str(e)}",
            )

        # We need to special handle the case where the execution result is a tuple and convert it to a list
        # Because when json is stored, the tuple is converted to a list, and so the expected result is a list when loaded from json
        if isinstance(exec_output, tuple):
            exec_output = list(exec_output)

        if expected_result_type == "exact_match":
            if exec_output != expected_result:
                return ExecutableCheckerResult(
                    is_valid=False,
                    error_type="executable_checker:wrong_result",
                    error_message=f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, but got: {exec_output}.",
                    model_executed_output=exec_output,
                )

        elif expected_result_type == "real_time_match":
            # Allow for 5% difference
            if (type(expected_result) == float or type(expected_result) == int) and (
                type(exec_output) == float or type(exec_output) == int
            ):
                if not (
                    expected_result * (1 - REAL_TIME_MATCH_ALLOWED_DIFFERENCE)
                    <= exec_output
                    <= expected_result * (1 + REAL_TIME_MATCH_ALLOWED_DIFFERENCE)
                ):
                    return ExecutableCheckerResult(
                        is_valid=False,
                        error_type="executable_checker:wrong_result_real_time",
                        error_message=(
                            f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, "
                            f"but got: {exec_output}. {REAL_TIME_MATCH_ALLOWED_DIFFERENCE * 100}% difference allowed."
                        ),
                        model_executed_output=exec_output,
                    )

            else:
                return ExecutableCheckerResult(
                    is_valid=False,
                    error_type="executable_checker:wrong_result_real_time",
                    error_message=(
                        f"Wrong execution result for {repr(function_call)}. Expected: {expected_result}, "
                        f"but got: {exec_output}. Type needs to be float or int for real time match criteria."
                    ),
                    model_executed_output=exec_output,
                )

        else:
            # structural match
            pattern_match_result = self._patten_matcher(
                exec_output, expected_result, function_call, is_sanity_check
            )
            if not pattern_match_result.is_valid:
                return pattern_match_result

        return ExecutableCheckerResult(is_valid=True)

    def _parallel_executable_checker_no_order(
        self,
        decoded_result: list[str],
        expected_exec_result: list,
        expected_exec_result_type: list[str],
    ):

        if len(decoded_result) != len(expected_exec_result):
            return ExecutableCheckerResult(
                is_valid=False,
                error_type="value_error:exec_result_count",
                error_message=f"Wrong number of functions provided. Expected {len(expected_exec_result)}, but got {len(decoded_result)}.",
            )

        matched_indices = []
        for i in range(len(expected_exec_result)):
            all_errors = []
            for index in range(len(decoded_result)):
                if index in matched_indices:
                    continue

                result = self._simple_executable_checker(
                    decoded_result[index],
                    expected_exec_result[i],
                    expected_exec_result_type[i],
                    False,
                )

                if result.is_valid:
                    matched_indices.append(index)
                    break
                else:
                    all_errors.append(
                        {
                            f"Model Result Index {index}": {
                                "sub_error": result.is_valid,
                                "sub_error_type": result.error_type,
                                "model_executed_output": (
                                    result.execution_output
                                    if hasattr(result, "execution_output")
                                    else None
                                ),
                            },
                        },
                    )

            if not result.is_valid:
                considered_indices = [
                    i for i in range(len(decoded_result)) if i not in matched_indices
                ]
                all_errors.insert(
                    0,
                    f"Could not find a matching function among index {considered_indices} of model output for index {i} of possible answers.",
                )
                return ExecutableCheckerResult(
                    is_valid=False,
                    error_type="executable_checker:cannot_find_match",
                    error_message=all_errors,
                )


        return ExecutableCheckerResult(is_valid=True)

    @staticmethod
    def _patten_matcher(
        exec_output, expected_result, function_call, is_sanity_check
    ) -> ExecutableCheckerResult:

        if type(exec_output) != type(expected_result):
            return ExecutableCheckerResult(
                is_valid=False,
                error_type="executable_checker:wrong_result_type",
                error_message=f"Wrong execution result type for {repr(function_call)}. Expected type: {type(expected_result)}, but got: {type(exec_output)}.",
                execution_output=exec_output,
            )

        if type(exec_output) == dict:
            # We loose the requirement for the sanity check as the expected result used in the sanity check might not be the most up-to-date one.
            # This happens when the key is a timestamp or a random number.
            if is_sanity_check:
                if len(exec_output) != len(expected_result):
                    return ExecutableCheckerResult(
                        is_valid=False,
                        error_type="executable_checker:wrong_result_type:dict_length",
                        error_message=f"Wrong execution result pattern for {repr(function_call)}. Expect type Dict, but wrong number of elements in the output. Expected length: {len(expected_result)}, but got: {len(exec_output)}.",
                        execution_output=exec_output,
                    )

                else:
                    return ExecutableCheckerResult(is_valid=True)

            for key, value in expected_result.items():
                if key not in exec_output:
                    return ExecutableCheckerResult(
                        is_valid=False,
                        error_type="executable_checker:wrong_result_type:dict_key_not_found",
                        error_message=f"Wrong execution result pattern for {repr(function_call)}. Expect type Dict, but key {repr(key)} not found in the model output.",
                        execution_output=exec_output,
                    )

            for key, value in exec_output.items():
                if key not in expected_result:
                    return ExecutableCheckerResult(
                        is_valid=False,
                        error_type="executable_checker:wrong_result_type:dict_extra_key",
                        error_message=f"Wrong execution result pattern for {repr(function_call)}. Expect type Dict, but key {repr(key)} not expected in the model output.",
                        execution_output=exec_output,
                    )

        if type(exec_output) == list:
            if len(exec_output) != len(expected_result):
                return ExecutableCheckerResult(
                    is_valid=False,
                    error_type="executable_checker:wrong_result_type:list_length",
                    error_message=f"Wrong execution result pattern for {repr(function_call)}. Expect type list, but wrong number of elements in the output. Expected length: {len(expected_result)}, but got: {len(exec_output)}.",
                    execution_output=exec_output,
                )

        return ExecutableCheckerResult(is_valid=True)


class ExecutableChecker_REST:
    
    def __init__(self, model_response, expected_exec_result):
        self.model_response = model_response
        self.expected_exec_result = expected_exec_result

    def run(self) -> ExecutableCheckerResult:
        func_call = self.model_response
        eval_GT_json = self.expected_exec_result

        if "https://geocode.maps.co" in func_call:
            time.sleep(2)
        if "requests_get" in func_call:
            func_call = func_call.replace("requests_get", "requests.get")
        try:
            response = eval(func_call)
        except Exception as e:
            return ExecutableCheckerResult(
                is_valid=False,
                error_type="executable_checker_rest:execution_error",
                error_message=f"Execution failed. {str(e)}",
            )

        try:
            if response.status_code == 200:
                try:
                    if isinstance(eval_GT_json, dict):
                        if isinstance(response.json(), dict):
                            if set(eval_GT_json.keys()) == set(response.json().keys()):
                                return ExecutableCheckerResult(is_valid=True)
                            else:
                                return ExecutableCheckerResult(
                                    is_valid=False,
                                    error_type="executable_checker_rest:wrong_key",
                                    error_message="Key inconsistency",
                                )

                        return ExecutableCheckerResult(
                            is_valid=False,
                            error_type="executable_checker_rest:wrong_type",
                            error_message=f"Expected dictionary, but got {type(response.json())}",
                        )

                    elif isinstance(eval_GT_json, list):
                        if isinstance(response.json(), list):
                            if len(eval_GT_json) != len(response.json()):
                                return ExecutableCheckerResult(
                                    is_valid=False,
                                    error_type="value_error:exec_result_rest_count",
                                    error_message="Response list length inconsistency.",
                                )

                            else:
                                for i in range(len(eval_GT_json)):
                                    if set(eval_GT_json[i].keys()) != set(
                                        response.json()[i].keys()
                                    ):
                                        return ExecutableCheckerResult(
                                            is_valid=False,
                                            error_type="executable_checker_rest:wrong_key",
                                            error_message="Key inconsistency",
                                        )

                                return ExecutableCheckerResult(is_valid=True)
                        else:
                            return ExecutableCheckerResult(
                                is_valid=False,
                                error_type="executable_checker_rest:wrong_type",
                                error_message=f"Expected list, but got {type(response.json())}",
                            )

                    return ExecutableCheckerResult(
                        is_valid=False,
                        error_type="executable_checker_rest:wrong_type",
                        error_message=f"Expected dict or list, but got {type(response.json())}",
                    )

                except Exception as e:
                    return ExecutableCheckerResult(
                        is_valid=False,
                        error_type="executable_checker_rest:response_format_error",
                        error_message=f"Error in execution and type checking. Status code: {response.status_code}. Error: {str(e)}",
                    )

            else:
                return ExecutableCheckerResult(
                    is_valid=False,
                    error_type="executable_checker_rest:wrong_status_code",
                    error_message=f"Execution result status code is not 200, got {response.status_code}",
                )

        except Exception as e:
            return ExecutableCheckerResult(
                is_valid=False,
                error_type="executable_checker_rest:cannot_get_status_code",
                error_message=f"Cannot get status code of the response. Error: {str(e)}",
            )
