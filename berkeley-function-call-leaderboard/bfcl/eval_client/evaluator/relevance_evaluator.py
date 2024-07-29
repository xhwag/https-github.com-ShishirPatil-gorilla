from evaluator import FailedResult
from evaluator import Evaluator
from utils import is_empty_output


class IrrelevanceEvaluator(Evaluator):

    def run(self):
        for i in range(len(self.model_response)):
            entry_id = self.test_data[i]["id"]
            model_response_item_raw = self.model_response[i]["result"]
            prompt_item = self.test_data[i]["question"]

            success = False  # success is True if the model response is irrelevant, meaning decoder should fail
            model_response_item_decoded = None

            try:
                model_response_item_decoded = self.handler.decode_ast(
                    model_response_item_raw, language=self.language
                )
                success = False
                if is_empty_output(model_response_item_decoded):
                    success = True

            except Exception as e:
                success = True

            if success:
                self.correct_count += 1
            else:
                self.failure_record.append(
                    FailedResult(
                        id=entry_id,
                        test_category=self.test_category,
                        model_name=self.model_name,
                        is_valid=False,
                        error_type="relevance_error:decoder_success",
                        error_message="Valid syntax. Successfully decode model response when it should not.",
                        question=prompt_item,
                        model_response_raw=model_response_item_raw,
                        model_response_decoded=model_response_item_decoded,
                    )
                )
