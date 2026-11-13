from .documents import create_document

# Every function the model is allowed to call. Nothing else can run.
TOOLS = {
    "create_document": create_document,
}
