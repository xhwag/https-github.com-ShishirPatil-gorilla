# from .anthropic import AnthropicFCHandler, AnthropicPromptHandler
# from .cohere import CohereHandler
# from .databricks import DatabricksHandler
# from .firework_ai import FireworkAIHandler
# from .functionary import FunctionaryHandler
# from .gemini import GeminiHandler
from .gorilla import GorillaHandler
# from .mistral import MistralHandler
# from .nexus import NexusHandler
# from .nvidia import NvidiaHandler
# from .openai import OpenAIHandler
# from .snowflake import SnowflakeHandler

__all__ = [
    # 'AnthropicFCHandler',
    # 'AnthropicPromptHandler',
    # 'CohereHandler',
    # 'DatabricksHandler',
    # 'FireworkAIHandler',
    # 'FunctionaryHandler',
    # 'GeminiHandler',
    'GorillaHandler',
    # 'MistralHandler',
    # 'NexusHandler',
    # 'NvidiaHandler',
    # 'OpenAIHandler',
    # 'SnowflakeHandler',
]

PRPPRIETARY_MODEL_TO_HANDLER_CLS = {}
for handler_name in __all__:
    handler_class = globals()[handler_name]
    for model in handler_class.supported_models():
        PRPPRIETARY_MODEL_TO_HANDLER_CLS[model] = handler_class
        
        
# import importlib
# import inspect
# import os
# from pathlib import Path

# # Directory containing the handler modules
# handlers_dir = Path(__file__).parent

# # Dictionary to store the model-to-handler class mapping
# MODEL_TO_HANDLER_CLS = {}

# def is_handler_class(cls):
#     """Check if a class is a handler class by inspecting its attributes."""
#     return hasattr(cls, 'supported_models') and callable(cls.supported_models)

# # Iterate over the files in the handlers directory
# for module_path in handlers_dir.glob('*.py'):
#     module_name = module_path.stem
#     if module_name == '__init__':
#         continue

#     # Import the module
#     module = importlib.import_module(f'.{module_name}', package=__name__)

#     # Iterate over the members of the module to find handler classes
#     for name, cls in inspect.getmembers(module, inspect.isclass):
#         if is_handler_class(cls):
#             for model in cls.supported_models():
#                 MODEL_TO_HANDLER_CLS[model] = cls

# # Print the MODEL_TO_HANDLER_CLS for verification
# print(MODEL_TO_HANDLER_CLS)
