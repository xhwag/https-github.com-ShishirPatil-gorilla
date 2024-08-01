# from bfcl.model_handler.oss_model import OSS_MODEL_TO_HANDLER_CLS
from bfcl.model_handler.proprietary_model import PRPPRIETARY_MODEL_TO_HANDLER_CLS

# MODEL_TO_HANDLER_CLS = OSS_MODEL_TO_HANDLER_CLS.update(PRPPRIETARY_MODEL_TO_HANDLER_CLS)
MODEL_TO_HANDLER_CLS = PRPPRIETARY_MODEL_TO_HANDLER_CLS

def get_model_handler(model_name: str):
    handler_cls = MODEL_TO_HANDLER_CLS.get(model_name)
    assert (
        handler_cls
    ), f'Invalid model name "{model_name}"! Please select from {tuple(MODEL_TO_HANDLER_CLS)}'

    return handler_cls
