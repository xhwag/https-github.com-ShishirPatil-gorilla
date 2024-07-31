REAL_TIME_MATCH_ALLOWED_DIFFERENCE = 0.2

TEST_COLLECTION_MAPPING = {
    "ast": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "java",
        "javascript",
        "relevance",
    ],
    "executable": [
        "executable_simple",
        "executable_multiple_function",
        "executable_parallel_function",
        "executable_parallel_multiple_function",
        "rest",
    ],
    "all": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "java",
        "javascript",
        "relevance",
        "executable_simple",
        "executable_multiple_function",
        "executable_parallel_function",
        "executable_parallel_multiple_function",
        "rest",
    ],
    "non-python": [
        "java",
        "javascript",
    ],
    "python": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "relevance",
        "executable_simple",
        "executable_multiple_function",
        "executable_parallel_function",
        "executable_parallel_multiple_function",
        "rest",
    ],
    "python-ast": [
        "simple",
        "multiple_function",
        "parallel_function",
        "parallel_multiple_function",
        "relevance",
    ],
}