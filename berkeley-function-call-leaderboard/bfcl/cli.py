import argparse

from dotenv import load_dotenv

from bfcl.evaluation import EvalClient
from bfcl.llm_generation import collect_model_responses
from bfcl.types import (
    TestCategory,
    TestCategoryGroup,
    TEST_CATEGORY_GROUP_MAPPING,
    LeaderboardVersion,
)
from bfcl.utils.apply_function_credential import apply_api_credential

load_dotenv()


def main():
    args = _get_args()
    apply_api_credential()
    
    if args.command == "llm_generation":
        collect_model_responses(args)

    elif args.command == "evaluation":
        eval_client = EvalClient(args)
        eval_client.run()
        eval_client.get_results()


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bfcl", description="Berkeley Function Calling Leaderboard (BFCL)"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Sub-command to run"
    )

    # Common arguments for both benchmark and evaluation
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--model",
        type=str,
        nargs="+",
        help="One or more LLLM model names. (default: 'gorilla-openfunctions-v2' when running 'llm_generation' and None when running 'evaluation')",
    )
    common_parser.add_argument(
        "--test-category",
        type=str,
        nargs="+",
        choices=[cat.value for cat in TestCategory]
        + [cat_group.value for cat_group in TestCategoryGroup],
        help=(
            "One or more test categories. "
            "Available test categories: "
            f"{', '.join(cat.value for cat in TestCategory)}. "
            "You can also specify test category groups: "
            f"{', '.join(cat_group.value for cat_group in TestCategoryGroup)}. "
            "(default: 'all')"
        ),
    )
    common_parser.add_argument(
        "--version",
        type=LeaderboardVersion,
        default=LeaderboardVersion.V1.value,
        choices=[category.value for category in LeaderboardVersion],
        help="Leaderboard version. (default: 'v1')",
    )

    _add_llm_generation_args(subparsers, common_parser)
    _add_evaluation_args(subparsers, common_parser)

    args = parser.parse_args()
    args = _process_model_name_args(args)
    args = _process_test_category_args(args)
    return args


def _add_llm_generation_args(subparsers, common_parser):
    """Add LLM generation specific arguments."""

    benchmark_parser = subparsers.add_parser(
        "llm_generation", parents=[common_parser], help="Generate LLM responses"
    )
    benchmark_parser.add_argument(
        "--temperature", type=float, default=0.01, help="Temperature (default: 0.01)"
    )
    benchmark_parser.add_argument(
        "--top-p", type=float, default=1, help="Top-p (default: 1)"
    )
    benchmark_parser.add_argument(
        "--max-tokens", type=int, default=1200, help="Max tokens (default: 1200)"
    )
    benchmark_parser.add_argument(
        "--num-gpus",
        default=1,
        type=int,
        help="No. of GPUs; only used for locally-hosted model (default: 1)",
    )
    benchmark_parser.add_argument(
        "--gpu-memory-utilization",
        default=0.9,
        type=float,
        help="GPU memory utilization; only used for locally-hosted model (default: 0.9)",
    )


def _add_evaluation_args(subparsers, common_parser):
    """Add evaluation-specific arguments."""

    evaluator_parser = subparsers.add_parser(
        "evaluation", parents=[common_parser], help="Run benchmark evaluation"
    )
    evaluator_parser.add_argument(
        "--perform-api-sanity-check",
        action="store_true",
        default=False,
        help="Perform the REST API status sanity check before running the evaluation. False means the check will be skipped. (default: False)",
    )


def _process_model_name_args(args):
    if args.model is None:
        if args.command == "llm_generation":
            args.model = ["gorilla-openfunctions-v2"]
        elif args.command == "evaluation":
            args.model = None

    if not isinstance(args.model, list):
        args.model = [args.model]

    return args


def _process_test_category_args(args):
    if args.test_category is None:
        args.test_category = TestCategoryGroup.ALL.value

    if not isinstance(args.test_category, list):
        args.test_category = [args.test_category]

    test_category_total = set()
    for test_category in args.test_category:
        if test_category in TestCategoryGroup._value2member_map_:
            test_category_total.update(TEST_CATEGORY_GROUP_MAPPING[test_category])
        elif test_category in TestCategory._value2member_map_:
            test_category_total.add(TestCategory._value2member_map_[test_category])
    args.test_category = list(test_category_total)

    return args


if __name__ == "__main__":
    main()
