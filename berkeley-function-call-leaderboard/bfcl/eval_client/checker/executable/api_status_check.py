from pathlib import Path
from bfcl.eval_client.checker.types import APIStatusObject
from bfcl.utils import load_json_file
from bfcl.evaluator.checker.executable.executable_checker import executable_checker_simple, executable_checker_rest
from tqdm import tqdm


class APIStatusChecker:
    
    def __init__(self):
        self.rest_error = None
        self.executable_error = None


    def check(self):
        self.api_status_sanity_check_executable()
        self.api_status_sanity_check_rest()
            
    
    def api_status_sanity_check_executable(self):
        EXECTUABLE_API_GROUND_TRUTH_FILE_PATH = Path(__file__).parent.joinpath("../../../data/api_status_check_data/api_status_check_ground_truth_executable.json").resolve()

        ground_truth = load_json_file(EXECTUABLE_API_GROUND_TRUTH_FILE_PATH)
        correct_count = 0
        errors = []
        for data in tqdm(
            ground_truth, total=len(ground_truth), desc="API Status Test (Non-REST)"
        ):
            status = executable_checker_simple(
                data["ground_truth"][0],
                data["execution_result"][0],
                data["execution_result_type"][0],
                True,
            )
            if status["valid"]:
                correct_count += 1
            else:
                errors.append((data, status))

        if correct_count != len(ground_truth):
            self.executable_error = APIStatusObject(errors, f"{len(ground_truth) - correct_count} / {len(ground_truth)}")


    def api_status_sanity_check_rest(self):
        REST_API_GROUND_TRUTH_FILE_PATH = Path(__file__).parent.joinpath("../../../data/api_status_check_data/api_status_check_ground_truth_REST.json").resolve()
        ground_truth_dummy = load_json_file(REST_API_GROUND_TRUTH_FILE_PATH)

        # Use the ground truth data to make sure the API is working correctly
        command = f"cd .. ; python apply_function_credential_config.py --input-path ./eval_checker/{REST_API_GROUND_TRUTH_FILE_PATH};"
        try:
            subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            write_list_of_dicts_to_file(REST_API_GROUND_TRUTH_FILE_PATH, ground_truth_dummy)
            raise RuntimeError(e.stderr) from e

        ground_truth_replaced = load_file(REST_API_GROUND_TRUTH_FILE_PATH)
        write_list_of_dicts_to_file(REST_API_GROUND_TRUTH_FILE_PATH, ground_truth_dummy)

        correct_count = 0
        errors = []
        for idx, data in tqdm(
            enumerate(ground_truth_replaced),
            total=len(ground_truth_replaced),
            desc="API Status Test (REST)",
        ):
            status = executable_checker_rest(data["ground_truth"], idx)
            if status["valid"]:
                correct_count += 1
            else:
                errors.append((data, status))

        if correct_count != len(ground_truth_replaced):
            self.rest_error = APIStatusObject(errors, f"{len(ground_truth_replaced) - correct_count} / {len(ground_truth_replaced)}")



    def display_api_status(self, display_success=False):
        if not self.rest_error and not self.executable_error:
            if display_success:
                print("🟢 All API Status Test Passed!")
            return None

        RED_FONT = "\033[91m"
        RESET = "\033[0m"

        print(f"\n{RED_FONT}{'-' * 18} Executable Categories' Error Bounds Based on API Health Status {'-' * 18}{RESET}\n")

        if self.rest_error:
            print(f"❗️ Warning: Unable to verify health of executable APIs used in executable test category (REST). Please contact API provider.\n")
            print(f"{self.rest_error.error_rate} APIs affected:\n")
            for data, status in self.rest_error.errors:
                print(f"  - Test Case: {data['ground_truth']}")
                print(f"    Error Type: {status['error_type']}\n")

        if self.executable_error:
            print(f"❗️ Warning: Unable to verify health of executable APIs used in executable test categories (Non-REST). Please contact API provider.\n")
            print(f"{self.executable_error.error_rate} APIs affected:\n")
            for data, status in self.executable_error.errors:
                print(f"  - Test Case: {data['ground_truth'][0]}")
                print(f"    Error Type: {status['error_type']}\n")

        print(f"{RED_FONT}{'-' * 100}\n{RESET}")
    