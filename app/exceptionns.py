from fastapi import HTTPException

class TaskNotFoundError(HTTPException):
    def __init__(self, identifier: str):
        super().__init__(status_code=404, detail=f"Task not found: {identifier}")

class TaskStatusInvalidError(HTTPException):
    def __init__(self, task_id: str):
        super().__init__(status_code=400, detail=f"Task {task_id} is not in pending state")

class PermissionDeniedError(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Permission denied")

class ProductNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="No matching products found")

class TaskCreationError(HTTPException):
    def __init__(self, msg: str = "Failed to create task"):
        super().__init__(status_code=500, detail=msg)
