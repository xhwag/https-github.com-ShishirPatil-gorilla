import argparse
import os

from typing import List
from bfcl.eval_client.leaderboard import Leaderboard
from bfcl.model_handler.base import BaseHandler
from bfcl.constants import RESULT_FILE_DIR
from bfcl.utils import get_model_handler
from bfcl.eval_client.checker.executable.api_status_check import APIStatusChecker
from bfcl.types import TestCategory, EvaluationMethod
from bfcl.eval_client.evaluator.ast_evaluator import ASTEvaluator
from bfcl.eval_client.evaluator.relevance_evaluator import IrrelevanceEvaluator


class EvalClient:
    def __init__(self, args: argparse.Namespace):
        self.leaderboard = Leaderboard()
        self.args = args
        self.test_category: List[TestCategory] = args.test_category
        self.test_category = TestCategory.sort_categories(self.test_category)
        self.perform_api_sanity_check = args.perform_api_sanity_check
        self.model_handlers: List[BaseHandler] = []
        self.api_status_checker = APIStatusChecker()

        if args.model is None:
            # Scan the result file directory for all available folders
            entries = os.scandir(RESULT_FILE_DIR)
            subdirs = [entry.path for entry in entries if entry.is_dir()]
            for subdir in subdirs:
                model_name_dir = subdir.split(RESULT_FILE_DIR)[1]
                model_name = model_name_dir.replace("_", "/")
                self.model_handlers.append(get_model_handler(model_name))

        else:
            for model_name in args.model:
                self.model_handlers.append(get_model_handler(model_name))

    def run(self):
        if self.perform_api_sanity_check:
            self.api_status_checker.check()
            self.api_status_checker.display_api_status(display_success=True)

        for test_category in self.test_category:
            if test_category.evaluation_method == EvaluationMethod.AST:
                evaluator = ASTEvaluator(test_category, self.leaderboard)
            elif test_category.evaluation_method == EvaluationMethod.EXECUTABLE:
                evaluator = ASTEvaluator(test_category, self.leaderboard)
            elif test_category.evaluation_method == EvaluationMethod.IRRELEVANCE:
                evaluator = IrrelevanceEvaluator(test_category, self.leaderboard)
            else:
                raise NotImplementedError(
                    f"Unsupported evaluation method: {test_category.evaluation_method}"
                )

            for model_handler in self.model_handlers:
                evaluator.pre_run_process(model_handler)
                evaluator.run()
                evaluator.compute_score()

        if self.perform_api_sanity_check:
            self.api_status_checker.display_api_status(display_success=False)

    def get_results(self):
        self.leaderboard.get_results()
