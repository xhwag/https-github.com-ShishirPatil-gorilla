from typing import List, Dict, Tuple

from bfcl.eval_client.checker.types import AstCheckerResult
from bfcl.types import TestCategory, TestLanguage
from bfcl.utils.ast_checker_utils import *
from bfcl.eval_client.checker.ast.type_converter.java import java_type_converter
from bfcl.eval_client.checker.ast.type_converter.javascript import js_type_converter
from bfcl.eval_client.checker.ast.ast_checker_constants import (
    PYTHON_NESTED_TYPE_CHECK_LIST,
    JAVA_TYPE_CONVERSION,
    JS_TYPE_CONVERSION,
    NESTED_CONVERSION_TYPE_LIST,
    PYTHON_TYPE_MAPPING,
)


class AstChecker:

    def __init__(
        self,
        func_doc: List[Dict],
        model_response: List[Dict],
        possible_answer: List[Dict],
        test_category: TestCategory,
        model_name: str,
    ):
        self.func_doc = func_doc
        self.model_response = model_response
        self.possible_answer = possible_answer
        self.test_category = test_category
        self.model_name = model_name
        self.test_language: TestLanguage = self.test_category.test_language

    def run(self) -> AstCheckerResult:
        if self.test_category == TestCategory.SIMPLE:
            if len(self.model_response) != 1:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:wrong_count",
                    error_message="Wrong number of functions.",
                )
            return self._simple_function_checker(
                self.func_doc[0], self.model_response[0], self.possible_answer[0]
            )
        else:
            return self._parallel_function_checker_no_order(
                self.func_doc, self.model_response, self.possible_answer
            )

    @staticmethod
    def _type_checker(
        param: str,
        value,
        possible_answer: list,
        expected_type_description: str,
        expected_type_converted,
        nested_type_converted,
    ) -> Tuple[bool, AstCheckerResult]:
        # NOTE: This type checker only supports nested type checking for one level deep.
        # We didn't implement recursive type checking for nested types, as it's not needed for the current use case and it's very complex.

        result = AstCheckerResult(is_valid=True, error_type="type_error:simple")

        is_variable = False
        # check for the case where a variable is used instead of a actual value.
        # use the type in possible_answer as the expected type
        possible_answer_type = get_possible_answer_type(possible_answer)
        # if possible_answer only contains optional parameters, we can't determine the type
        if possible_answer_type != None:
            # we are being precise here.
            # in fact, possible_answer_type should always be string, as that's how we treat varibale in possible_answer
            if possible_answer_type != expected_type_converted:
                is_variable = True

        # value is the same type as in function description
        if type(value) == expected_type_converted:
            # We don't need to do recursive check for simple types
            if nested_type_converted == None:
                return is_variable, result
            else:
                for possible_answer_item in possible_answer:
                    flag = True  # Each parameter should match to at least one possible answer type.
                    # Here, we assume that each item should be the same type. We could also relax it.
                    if type(possible_answer_item) == list:
                        for value_item in value:
                            _, checker_result = AstChecker._type_checker(
                                param,
                                value_item,
                                possible_answer_item,
                                str(nested_type_converted),
                                nested_type_converted,
                                None,
                            )
                            if not checker_result.is_valid:
                                flag = False
                                break

                    if flag:
                        return is_variable, AstCheckerResult(is_valid=True)

                result = AstCheckerResult(
                    is_valid=False,
                    error_type="type_error:nested",
                    error_message=f"Nested type checking failed for parameter {repr(param)}. Expected outer type {expected_type_description} with inner type {str(nested_type_converted)}. Parameter value: {repr(value)}.",
                )

        # value is not as expected, check for the case where a variable is used instead of a actual value
        # use the type in possible_answer as the expected type
        possible_answer_type = get_possible_answer_type(possible_answer)
        # if possible_answer only contains optional parameters, we can't determine the type
        if possible_answer_type != None:
            # we are being precise here.
            # in fact, possible_answer_type should always be string, as that's how we treat varibale in possible_answer
            if type(value) == possible_answer_type:
                is_variable = True
                return is_variable, result

        return is_variable, AstCheckerResult(
            is_valid=False,
            error_type=result["type_error:simple"],
            error_message=f"Incorrect type for parameter {repr(param)}. Expected type {expected_type_description}, got {type(value).__name__}. Parameter value: {repr(value)}.",
        )

    @staticmethod
    def _string_checker(param: str, model_output: str, possible_answer: list):
        standardize_possible_answer = []
        standardize_model_output = standardize_string(model_output)
        for i in range(len(possible_answer)):
            if type(possible_answer[i]) == str:
                standardize_possible_answer.append(
                    standardize_string(possible_answer[i])
                )

        if standardize_model_output not in standardize_possible_answer:
            return AstCheckerResult(
                is_valid=False,
                error_type="value_error:string",
                error_message=f"Invalid value for parameter {repr(param)}: {repr(model_output)}. Expected one of {possible_answer}. Case insensitive.",
            )

        return AstCheckerResult(is_valid=True)

    @staticmethod
    def _list_checker(param: str, model_output: list, possible_answer: list):
        # Convert the tuple to a list

        standardize_model_output = list(model_output)

        # If the element in the list is a string, we need to standardize it
        for i in range(len(standardize_model_output)):
            if type(standardize_model_output[i]) == str:
                standardize_model_output[i] = standardize_string(model_output[i])

        standardize_possible_answer = []
        # We also need to standardize the possible answers
        for i in range(len(possible_answer)):
            standardize_possible_answer.append([])
            for j in range(len(possible_answer[i])):
                if type(possible_answer[i][j]) == str:
                    standardize_possible_answer[i].append(
                        standardize_string(possible_answer[i][j])
                    )
                else:
                    standardize_possible_answer[i].append(possible_answer[i][j])

        if standardize_model_output not in standardize_possible_answer:
            return AstCheckerResult(
                is_valid=False,
                error_type="value_error:list/tuple",
                error_message=f"Invalid value for parameter {repr(param)}: {repr(model_output)}. Expected one of {possible_answer}.",
            )

        return AstCheckerResult(is_valid=True)

    @staticmethod
    def _dict_checker(param: str, model_output: dict, possible_answers: list):
        # This function works for simple dictionaries, as well as dictionaries with nested dictionaries

        result = AstCheckerResult(is_valid=False, error_type="dict_checker:unclear")
        for i in range(len(possible_answers)):

            if possible_answers[i] == "":
                continue

            result = AstCheckerResult(is_valid=False, error_type="dict_checker:unclear")

            flag = True

            possible_answer = possible_answers[i]
            # possible_anwer is a single dictionary
            if len(model_output.keys()) != len(possible_answer.keys()):
                result = AstCheckerResult(
                    is_valid=False,
                    error_type="value_error:dict_items",
                    error_message="Wrong number of parameters for dictionary.",
                )
                flag = False
                continue

            for key, value in model_output.items():
                if key not in possible_answer:
                    result = AstCheckerResult(
                        is_valid=False,
                        error_type="value_error:dict_key",
                        error_message=f"Unexpected parameter: '{key}'.",
                    )
                    flag = False
                    break

                expected_values = possible_answer[key]
                if isinstance(expected_values, dict):
                    result = AstChecker._dict_checker(param, value, [expected_values])
                    if not result.is_valid:
                        flag = False
                        break
                else:
                    standardize_value = value
                    # If the value is a string, we need to standardize it
                    if type(value) == str:
                        standardize_value = standardize_string(value)
                    # We also need to standardize the possible answers
                    standardize_possible_answer = []
                    for i in range(len(possible_answer[key])):
                        if type(possible_answer[key][i]) == str:
                            standardize_possible_answer.append(
                                standardize_string(possible_answer[key][i])
                            )
                        else:
                            standardize_possible_answer.append(possible_answer[key][i])

                    if standardize_value not in standardize_possible_answer:
                        result = AstCheckerResult(
                            is_valid=False,
                            error_type="value_error:dict_value",
                            error_message=f"Invalid value for parameter {repr(key)}: {repr(value)}. Expected one of {standardize_possible_answer}.",
                        )
                        flag = False
                        break
            if flag:
                return AstCheckerResult(is_valid=True)

        return result

    @staticmethod
    def _list_dict_checker(param: str, model_output: list, possible_answers: list):
        # This function takes in a list of dictionaries and checks if each dictionary is valid
        # The order of the dictionaries in the list must match the order of the possible answers

        result = AstCheckerResult(
            is_valid=False, error_type="list_dict_checker:unclear"
        )

        for answer_index in range(len(possible_answers)):
            flag = True  # True means so far, all dictionaries are valid

            # Only proceed if the number of dictionaries in the list matches the number of dictionaries in the possible answers
            if len(model_output) != len(possible_answers[answer_index]):
                result = AstCheckerResult(
                    is_valid=False,
                    error_type="value_error:list_dict_count",
                    error_message="Wrong number of dictionaries in the list.",
                )
                flag = False
                continue

            for dict_index in range(len(model_output)):
                result = AstChecker._dict_checker(
                    param,
                    model_output[dict_index],
                    [possible_answers[answer_index][dict_index]],
                )
                if not result.is_valid:
                    flag = False
                    break
            if flag:
                return AstCheckerResult(is_valid=True)

        return result

    def _simple_function_checker(
        self,
        func_description: Dict,
        model_output: Dict,
        possible_answer: Dict,
    ):
        possible_answer = list(possible_answer.values())[0]
        # Extract function name and parameters details
        func_name = func_description["name"]
        param_details = func_description["parameters"]["properties"]
        required_params = func_description["parameters"]["required"]

        # Initialize a result dictionary
        result = AstCheckerResult(is_valid=True)

        func_name = convert_func_name(func_name, self.model_name)

        # Check if function name matches
        if func_name not in model_output:
            return AstCheckerResult(
                is_valid=False,
                error_type="simple_function_checker:wrong_func_name",
                error_message=f"Function name {repr(func_name)} not found in model output.",
            )

        model_params = model_output[func_name]

        # Check for required parameters in model output
        for param in required_params:
            if param not in model_params:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:missing_required",
                    error_message=f"Missing required parameter: {repr(param)}.",
                )

        # Validate types and values for each parameter in model output
        for param, value in model_params.items():
            if param not in param_details or param not in possible_answer:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:unexpected_param",
                    error_message=f"Unexpected parameter: {repr(param)}.",
                )

            full_param_details = param_details[param]
            expected_type_description = full_param_details["type"]  # This is a string
            is_variable = False
            nested_type_converted = None

            if self.test_language == TestLanguage.JAVA:
                expected_type_converted = JAVA_TYPE_CONVERSION[
                    expected_type_description
                ]

                if expected_type_description in JAVA_TYPE_CONVERSION:
                    if type(value) != str:
                        return AstCheckerResult(
                            is_valid=False,
                            error_type="type_error:java",
                            error_message=f"Incorrect type for parameter {repr(param)}. Expected type String, got {type(value).__name__}. Parameter value: {repr(value)}.",
                        )

                    if expected_type_description in NESTED_CONVERSION_TYPE_LIST:
                        nested_type = param_details[param]["items"]["type"]
                        nested_type_converted = JAVA_TYPE_CONVERSION[nested_type]
                        value = java_type_converter(
                            value, expected_type_description, nested_type
                        )
                    else:
                        value = java_type_converter(value, expected_type_description)

            elif self.test_language == TestLanguage.JAVASCRIPT:
                expected_type_converted = JS_TYPE_CONVERSION[expected_type_description]

                if expected_type_description in JS_TYPE_CONVERSION:
                    if type(value) != str:
                        return AstCheckerResult(
                            is_valid=False,
                            error_type="type_error:js",
                            error_message=f"Incorrect type for parameter {repr(param)}. Expected type String, got {type(value).__name__}. Parameter value: {repr(value)}.",
                        )

                    if expected_type_description in NESTED_CONVERSION_TYPE_LIST:
                        nested_type = param_details[param]["items"]["type"]
                        nested_type_converted = JS_TYPE_CONVERSION[nested_type]
                        value = js_type_converter(
                            value, expected_type_description, nested_type
                        )
                    else:
                        value = js_type_converter(value, expected_type_description)

            elif self.test_language == TestLanguage.PYTHON:
                expected_type_converted = PYTHON_TYPE_MAPPING[expected_type_description]
                if expected_type_description in PYTHON_NESTED_TYPE_CHECK_LIST:
                    nested_type = param_details[param]["items"]["type"]
                    nested_type_converted = PYTHON_TYPE_MAPPING[nested_type]
            else:
                raise NotImplementedError("Unsupported language.")

            # We convert all tuple value to list when the expected type is tuple.
            # The conversion is necessary because any tuple in the possible answer would become a list after being processed through json.dump() and json.load().
            # This does introduce some false positive (eg, when the model provides a list value instead of tuple). We hope to find a better solution in the future.
            if expected_type_description == "tuple" and type(value) == tuple:
                value = list(value)

            # Allow python auto conversion from int to float
            if (
                self.test_language == TestLanguage.PYTHON
                and expected_type_description == "float"
                and type(value) == int
            ):
                value = float(value)

            # Type checking
            # In fact, we only check for Python here.
            # Type check for other languages are handled by the type converter, and so their value (after conversion) is always correct.
            is_variable, type_check_result = self._type_checker(
                param,
                value,
                possible_answer[param],
                expected_type_description,
                expected_type_converted,
                nested_type_converted,
            )
            if not type_check_result.is_valid:
                return type_check_result

            # It doesn't make sense to special handle dictionaries and list of dictionaries if the value is a variable.
            # We can just treat the variable as a string and use the normal flow.
            if not is_variable:
                # Special handle for dictionaries
                if expected_type_converted == dict:
                    result = self._dict_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

                # Special handle for list of dictionaries
                elif expected_type_converted == list and nested_type_converted == dict:
                    result = self._list_dict_checker(
                        param, value, possible_answer[param]
                    )
                    if not result.is_valid:
                        return result
                    continue

                # Special handle for strings
                elif expected_type_converted == str:
                    # We don't check for case sensitivity for string, as long as it's not a variable
                    result = self._string_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

                elif expected_type_converted == list:
                    result = self._list_checker(param, value, possible_answer[param])
                    if not result.is_valid:
                        return result
                    continue

            # Check if the value is within the possible answers
            if value not in possible_answer[param]:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="value_error:others",
                    error_message=f"Invalid value for parameter {repr(param)}: {repr(value)}. Expected one of {possible_answer[param]}.",
                )

        # Check for optional parameters not provided but allowed
        for param in possible_answer:
            if param not in model_params and "" not in possible_answer[param]:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="simple_function_checker:missing_optional",
                    error_message=f"Optional parameter {repr(param)} not provided and not marked as optional.",
                )

        return result

    def _parallel_function_checker_enforce_order(
        self,
        func_descriptions: List[Dict],
        model_output: List[Dict],
        possible_answers: List[Dict],
    ):
        if len(model_output) != len(possible_answers):
            return AstCheckerResult(
                is_valid=False,
                error_type="parallel_function_checker_enforce_order:wrong_count",
                error_message="Wrong number of functions.",
            )

        func_name_list = list(possible_answers.keys())
        possible_answers_list = []

        for key, value in possible_answers.items():
            possible_answers_list.append({key: value})

        for i in range(len(possible_answers_list)):
            func_description = find_description(func_descriptions, func_name_list[i])
            if func_description is None:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="parallel_function_checker_enforce_order:cannot_find_description",
                    error_message=f"Function doc description not found for function name: {repr(func_name_list[i])}.",
                )

            result = self._simple_function_checker(
                func_description, model_output[i], possible_answers_list[i]
            )
            if not result.is_valid:
                return result

        return AstCheckerResult(is_valid=True)

    def _parallel_function_checker_no_order(
        self,
        func_descriptions: List[Dict],
        model_output: List[Dict],
        possible_answers: List[Dict],
    ):
        if len(model_output) != len(possible_answers):
            return AstCheckerResult(
                is_valid=False,
                error_type="parallel_function_checker_no_order:wrong_count",
                error_message="Wrong number of functions.",
            )

        func_name_list = list(possible_answers.keys())
        possible_answers_list = []

        for key, value in possible_answers.items():
            possible_answers_list.append({key: value})

        matched_indices = []

        # We go throught the possible answers one by one, and eliminate the model output that matches the possible answer
        # It must be this way because we need ground truth to fetch the correct function description
        for i in range(len(possible_answers_list)):
            func_description = find_description(func_descriptions, func_name_list[i])

            # This should not happen. As possible_answers is the ground truth, and it should have the correct function name.
            if func_description is None:
                return AstCheckerResult(
                    is_valid=False,
                    error_type="parallel_function_checker_no_order:cannot_find_description",
                    error_message=f"Function doc description not found for function name: {repr(func_name_list[i])}.",
                )

            all_errors = []

            for index in range(len(model_output)):
                if index in matched_indices:
                    continue

                result = self._simple_function_checker(
                    func_description,
                    model_output[index],
                    possible_answers_list[i],
                )

                if result.is_valid:
                    matched_indices.append(index)
                    break
                else:
                    all_errors.append(
                        {
                            f"Model Result Index {index}": {
                                "sub_error": result.error_message,
                                "sub_error_type": result.error_type,
                                "model_output_item": model_output[index],
                                "possible_answer_item": possible_answers_list[i],
                            }
                        }
                    )

            if not result.is_valid:
                considered_indices = [
                    i for i in range(len(model_output)) if i not in matched_indices
                ]
                all_errors.insert(
                    0,
                    f"Could not find a matching function among index {considered_indices} of model output for index {i} of possible answers.",
                )
                return AstCheckerResult(
                    is_valid=False,
                    error_type="parallel_function_checker_no_order:cannot_find_match",
                    error_message=all_errors,
                )

        return AstCheckerResult(is_valid=True)
