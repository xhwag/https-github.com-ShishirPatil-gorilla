from evaluator import FailedResult
from bfcl.utils.evaluator_utils import is_function_calling_format_output
from bfcl.eval_client.checker.ast.ast_checker import AstChecker
from evaluator import Evaluator


class ASTEvaluator(Evaluator):

    def run(self):
        for i in range(len(self.test_data)):
            entry_id = self.test_data[i]["id"]
            model_response_item_raw = self.model_response[i]["result"]
            question_item = self.test_data[i]["question"]
            func_doc_item = self.test_data[i]["function"]
            possible_answer_item = self.possible_answer_data[i]["ground_truth"]

            try:
                model_response_item_decoded = self.handler.decode_ast(
                    model_response_item_raw, self.language
                )
            except Exception as e:
                self.failure_record.append(
                    FailedResult(
                        id=entry_id,
                        test_category=self.test_category,
                        model_name=self.model_name,
                        valid=False,
                        error_type="ast_decoder:decoder_failed",
                        error_message=f"Invalid syntax. Failed to decode AST. {str(e)}",
                        question=question_item,
                        func_doc=func_doc_item,
                        model_response_raw=model_response_item_raw,
                        possible_answer=possible_answer_item,
                    )
                )
                continue

            decoder_output_valid = is_function_calling_format_output(
                model_response_item_decoded
            )
            if not decoder_output_valid:
                self.failure_record.append(
                    FailedResult(
                        id=entry_id,
                        test_category=self.test_category,
                        model_name=self.model_name,
                        valid=False,
                        error_type="ast_decoder:decoder_wrong_output_format",
                        error_message="Did not output in the specified format. Note: the model_response is wrapped in a string to ensure json serializability.",
                        question=question_item,
                        func_doc=func_doc_item,
                        model_response_raw=model_response_item_raw,
                        model_response_decoded=model_response_item_decoded,
                        possible_answer=possible_answer_item,
                    )
                )
                continue

            checker = AstChecker(
                func_doc_item,
                model_response_item_decoded,
                possible_answer_item,
                self.test_category,
                self.model_name,
            )
            checker_result = checker.run()

            if checker_result["valid"]:
                self.correct_count += 1
            else:
                self.failure_record.append(
                    FailedResult(
                        id=entry_id,
                        test_category=self.test_category,
                        model_name=self.model_name,
                        valid=False,
                        error_type=checker_result.error_type,
                        error_message=checker_result.error_message,
                        question=question_item,
                        func_doc=func_doc_item,
                        model_response_raw=model_response_item_raw,
                        model_response_decoded=model_response_item_decoded,
                        possible_answer=possible_answer_item,
                    )
                )
