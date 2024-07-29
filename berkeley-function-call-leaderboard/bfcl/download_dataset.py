from huggingface_hub import hf_hub_download
from bfcl.types import TestCategory


for test_category in TestCategory:
    hf_hub_download(
        repo_id="gorilla-llm/Berkeley-Function-Calling-Leaderboard",
        filename=test_category.get_file_path(),
        repo_type="dataset",
        local_dir="./dataset",
    )