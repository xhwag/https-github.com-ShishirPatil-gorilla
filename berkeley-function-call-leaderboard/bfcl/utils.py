import json
import os
from bfcl.model_handler.base import BaseHandler
from bfcl.model_handler.oss_model import OSS_MODEL_TO_HANDLER_CLS
from bfcl.model_handler.proprietary_model import PRPPRIETARY_MODEL_TO_HANDLER_CLS

MODEL_TO_HANDLER_CLS = OSS_MODEL_TO_HANDLER_CLS.update(PRPPRIETARY_MODEL_TO_HANDLER_CLS)


def load_model_handler(model_name: str) -> BaseHandler:
    handler_cls = MODEL_TO_HANDLER_CLS.get(model_name)
    assert (
        handler_cls
    ), f'Invalid model name "{model_name}"! Please select from {tuple(MODEL_TO_HANDLER_CLS)}'

    return handler_cls


def load_json_file(file_path):
    result = []
    with open(file_path) as f:
        file = f.readlines()
        for line in file:
            result.append(json.loads(line))
    return result


def write_list_of_dicts_to_file(
    data: list, filename: str, subdir=None, appendMode=False
):
    if subdir:
        # Ensure the subdirectory exists
        os.makedirs(subdir, exist_ok=True)

        # Construct the full path to the file
        filename = os.path.join(subdir, filename)

    # Write the list of dictionaries to the file in JSON format
    with open(filename, "a" if appendMode else "w") as f:
        for i, entry in enumerate(data):
            json_str = json.dumps(entry)
            f.write(json_str)
            # Add a newline when there is just a single entry or not the last entry
            if i < len(data) - 1 or len(data) == 1:
                f.write("\n")


def write_single_dict_to_file(data: dict, filename: str, subdir=None, appendMode=False):
    write_list_of_dicts_to_file([data], filename, subdir, appendMode)
