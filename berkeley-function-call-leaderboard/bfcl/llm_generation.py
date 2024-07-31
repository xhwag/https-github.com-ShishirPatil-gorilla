import argparse
from tqdm import tqdm

from bfcl.types import TestCategory, ModelType
from bfcl.model_handler.base import BaseHandler
from bfcl.utils.utils import get_model_handler
from typing import List, Dict, Tuple


def _collect_test_cases(
    test_categories: List[TestCategory], model_handler: BaseHandler
) -> List[Dict]:
    test_cases_total = []
    for test_category in test_categories:
        test_cases = test_category.load_test_data()
        existing_results = model_handler.load_result_file(test_category)
        missing_entries = set([test_case["id"] for test_case in test_cases]) - set(
            [result["id"] for result in existing_results]
        )
        test_cases_total.extend(
            [
                test_case
                for test_case in test_cases
                if test_case["id"] in missing_entries
            ]
        )

    return test_cases_total


def _generate_results(args, model_handler: BaseHandler, test_cases_total):

    if model_handler.model_style == ModelType.OSS:
        result, metadata = model_handler.inference(
            test_question=test_cases_total,
            num_gpus=args.num_gpus,
            gpu_memory_utilization=args.gpu_memory_utilization,
        )
        # result.sort(key=lambda x: sort_index_key(x['id']))
        for test_case, res in zip(test_cases_total, result):
            result_to_write = {"id": test_case["id"], "result": res}
            model_handler.write_result(result_to_write)

    else:
        for test_case in tqdm(test_cases_total):

            user_question, functions, test_category = (
                test_case["question"],
                test_case["function"],
                test_case["id"].rsplit("_", 1)[0],
            )
            if type(functions) is dict or type(functions) is str:
                functions = [functions]

            result, metadata = model_handler.inference(
                user_question, functions, test_category
            )
            result_to_write = {
                "id": test_case["id"],
                "result": result,
                "input_token_count": metadata["input_tokens"],
                "output_token_count": metadata["output_tokens"],
                "latency": metadata["latency"],
            }
            model_handler.write_result(result_to_write)


# TODO: Support sorting in write_result for parallel processing
# def sort_index_key(s: str) -> Tuple[str, int]:
#     # Split the string by the last underscore to separate text and number
#     text, num = s.rsplit('_', 1)
#     # Convert the numeric part to an integer for proper sorting
#     return (text, int(num))


def collect_model_responses(args: argparse.Namespace) -> None:
    for model_name in args.model:
        model_handler_cls = get_model_handler(model_name)
        model_handler = model_handler_cls(
            model_name=model_name,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
        )

        test_cases_total = _collect_test_cases(args.test_category, model_handler)
        # test_cases_total.sort(key=lambda x: sort_index_key(x['id']))

        _generate_results(args, model_handler, test_cases_total)
