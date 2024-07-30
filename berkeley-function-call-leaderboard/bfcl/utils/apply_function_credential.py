import glob
import json
import os

from dotenv import load_dotenv

from bfcl.utils.utils import load_json_file, write_list_of_dicts_to_file

load_dotenv()

# Make sure the env variables are populated
ENV_VARS = ("GEOCODE_API_KEY", "RAPID_API_KEY", "OMDB_API_KEY", "EXCHANGERATE_API_KEY")
api_key = {}
for var in ENV_VARS:
    assert os.getenv(var), f"Please provide your {var} in the `.env` file."
    api_key[var] = os.getenv(var)

PLACEHOLDERS = {
    "YOUR-GEOCODE-API-KEY": api_key["GEOCODE-API-KEY"],
    "YOUR-RAPID-API-KEY": api_key["RAPID-API-KEY"],
    "YOUR-OMDB-API-KEY": api_key["OMDB-API-KEY"],
    "YOUR-EXCHANGERATE-API-KEY": api_key["EXCHANGERATE-API-KEY"],
}


def _replace_placeholders(data):
    """
    Recursively replace placeholders in a nested dictionary or list using string.replace.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                _replace_placeholders(value)
            elif isinstance(value, str):
                for placeholder, actual_value in PLACEHOLDERS.items():
                    if placeholder in value:  # Check if placeholder is in the string
                        data[key] = value.replace(placeholder, actual_value)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, list)):
                _replace_placeholders(item)
            elif isinstance(item, str):
                for placeholder, actual_value in PLACEHOLDERS.items():
                    if placeholder in item:  # Check if placeholder is in the string
                        data[idx] = item.replace(placeholder, actual_value)
    return data


def _process_file(input_file_path, output_file_path):
    file_content = load_json_file(input_file_path)
    modified_data = [_replace_placeholders(line) for line in file_content]

    # Write the modified data to the output file
    write_list_of_dicts_to_file(modified_data, output_file_path)
    
    print(f"All placeholders have been replaced for {input_file_path} 🦍.")


def _process_dir(input_dir, output_dir):
    # This function does support nested directories
    print(f"Input directory: {input_dir}")

    # Get a list of all entries in the folder
    entries = os.scandir(input_dir)

    json_files_pattern = os.path.join(input_dir, "*.json")
    for input_file_path in glob.glob(json_files_pattern):
        file_name = os.path.basename(input_file_path)
        output_file_path = os.path.join(output_dir, file_name)
        _process_file(input_file_path, output_file_path)

    # Process each subdirectory
    subdirs = [entry.path for entry in entries if entry.is_dir()]
    for subdir in subdirs:
        _process_dir(subdir, subdir)


def apply_credential(input_path, output_path=None):

    if output_path is None:
        output_path = input_path

    if os.path.isdir(input_path):
        _process_dir(input_path, output_path)
    else:
        _process_file(input_path, output_path)
