from enum import Enum, auto

class ModelType(str, Enum):
    OSS = "oss"
    PROPRIETARY = "proprietary"


class ModelStyle(str, Enum):
    GORILLA = "gorilla"
    OPENAI = "openai"
    ANTHROPIC_FC = "claude"
    ANTHROPIC_PROMPT = "claude"
    MISTRAL = "mistral"
    GOOGLE = "google"
    COHERE = "cohere"
    FIREWORK_AI = "firework_ai"
    NEXUS = "nexus"
    OSS_MODEL = "oss_model"


class LeaderboardVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"


class TestCategory(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    SIMPLE = auto()
    JAVA = auto()
    JAVASCRIPT = auto()
    RELEVANCE = auto()
    MULTIPLE_FUNCTION = auto()
    PARALLEL_FUNCTION = auto()
    PARALLEL_MULTIPLE_FUNCTION = auto()
    EXECUTABLE_SIMPLE = auto()
    EXECUTABLE_PARALLEL_FUNCTION = auto()
    EXECUTABLE_MULTIPLE_FUNCTION = auto()
    EXECUTABLE_PARALLEL_MULTIPLE_FUNCTION = auto()
    REST = auto()

    def get_file_path(
        self, leaderboard_version: LeaderboardVersion = LeaderboardVersion.V1
    ) -> str:
        return (
            f"gorilla_openfunctions_{leaderboard_version.value}_test_{self.value}.json"
        )


class TestCategoryGroup(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    AST = auto()
    EXECUTABLE = auto()
    ALL = auto()
    NON_PYTHON = auto()
    PYTHON = auto()
    PYTHON_AST = auto()


TEST_CATEGORY_GROUP_MAPPING = {
    TestCategoryGroup.AST: [
        TestCategory.SIMPLE,
        TestCategory.MULTIPLE_FUNCTION,
        TestCategory.PARALLEL_FUNCTION,
        TestCategory.PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.JAVA,
        TestCategory.JAVASCRIPT,
        TestCategory.RELEVANCE,
    ],
    TestCategoryGroup.EXECUTABLE: [
        TestCategory.EXECUTABLE_SIMPLE,
        TestCategory.EXECUTABLE_MULTIPLE_FUNCTION,
        TestCategory.EXECUTABLE_PARALLEL_FUNCTION,
        TestCategory.EXECUTABLE_PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.REST,
    ],
    TestCategoryGroup.ALL: [
        TestCategory.SIMPLE,
        TestCategory.MULTIPLE_FUNCTION,
        TestCategory.PARALLEL_FUNCTION,
        TestCategory.PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.JAVA,
        TestCategory.JAVASCRIPT,
        TestCategory.RELEVANCE,
        TestCategory.EXECUTABLE_SIMPLE,
        TestCategory.EXECUTABLE_MULTIPLE_FUNCTION,
        TestCategory.EXECUTABLE_PARALLEL_FUNCTION,
        TestCategory.EXECUTABLE_PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.REST,
    ],
    TestCategoryGroup.NON_PYTHON: [
        TestCategory.JAVA,
        TestCategory.JAVASCRIPT,
    ],
    TestCategoryGroup.PYTHON: [
        TestCategory.SIMPLE,
        TestCategory.MULTIPLE_FUNCTION,
        TestCategory.PARALLEL_FUNCTION,
        TestCategory.PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.RELEVANCE,
        TestCategory.EXECUTABLE_SIMPLE,
        TestCategory.EXECUTABLE_MULTIPLE_FUNCTION,
        TestCategory.EXECUTABLE_PARALLEL_FUNCTION,
        TestCategory.EXECUTABLE_PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.REST,
    ],
    TestCategoryGroup.PYTHON_AST: [
        TestCategory.SIMPLE,
        TestCategory.MULTIPLE_FUNCTION,
        TestCategory.PARALLEL_FUNCTION,
        TestCategory.PARALLEL_MULTIPLE_FUNCTION,
        TestCategory.RELEVANCE,
    ],
}


# class Leaderboard(BaseModel):
#     test_group: TestCategoryGroup | None = None
#     test_categories: List[LeaderboardCategory] | None = None # type: ignore
#     version: LeaderboardVersion = LeaderboardVersion.V1

#     @model_validator(mode='before')
#     @classmethod
#     def check_either_field_provided(cls, values):
#         if values.get('test_group') is not None and values.get('test_categories') is not None:
#             raise ValueError("Provide either 'test_group' or 'test_categories', not both")
#         elif values.get('test_group') is None and values.get('test_categories') is None:
#             raise ValueError("Provide either 'test_group' or 'test_categories'")
#         return values
