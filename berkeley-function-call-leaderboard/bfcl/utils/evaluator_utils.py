
def is_function_calling_format_output(decoded_output):
    # Ensure the output is a list of dictionaries
    if type(decoded_output) == list:
        for item in decoded_output:
            if type(item) != dict:
                return False
        return True
    return False


def is_executable_format_output(decoded_output):
    # Ensure the output is a list of strings (one or more strings)
    if type(decoded_output) == list:
        if len(decoded_output) == 0:
            return False
        for item in decoded_output:
            if type(item) != str:
                return False
        return True
    return False


def is_rest_format_output(decoded_output):
    # Ensure the output is a list of one string
    if type(decoded_output) == list:
        if len(decoded_output) == 1 and type(decoded_output[0]) == str:
            return True
    return False


def is_empty_output(decoded_output):
    # This function is a patch to the ast decoder for relevance detection
    # Sometimes the ast decoder will parse successfully, but the input doens't really have a function call
    # [], [{}], and anything that is not in function calling format is considered empty (and thus should be marked as correct)
    if not is_function_calling_format_output(decoded_output):
        return True
    if len(decoded_output) == 0:
        return True
    if len(decoded_output) == 1 and len(decoded_output[0]) == 0:
        return True


def calculate_weighted_accuracy(accuracy_dict_list):
    total_count = 0
    total_accuracy = 0
    for accuracy_dict in accuracy_dict_list:
        total_count += accuracy_dict["total_count"]
        total_accuracy += accuracy_dict["accuracy"] * accuracy_dict["total_count"]

    if total_count == 0:
        return {"accuracy": 0, "total_count": 0}

    return {"accuracy": total_accuracy / total_count, "total_count": total_count}


def calculate_unweighted_accuracy(accuracy_dict_list):
    total_accuracy = 0
    for accuracy_dict in accuracy_dict_list:
        total_accuracy += accuracy_dict["accuracy"]

    if len(accuracy_dict_list) == 0:
        return {"accuracy": 0, "total_count": 0}

    return {"accuracy": total_accuracy / len(accuracy_dict_list), "total_count": 0}

