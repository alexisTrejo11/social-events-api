import json
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, success: bool, data: Optional[T] = None, error_message: Optional[str] = None):
        self.success = success
        self.data = data
        self.error_message = error_message

    @classmethod
    def success(cls, data: Optional[T] = None) -> 'Result[T]':
        return cls(True, data, None)

    @classmethod
    def failure(cls, error_message: str) -> 'Result':
        return cls(False, None, error_message)

    def to_json(self) -> str:
        return json.dumps({
            'success': self.success,
            'data': self.data,
            'error': self.error_message
        })

    @staticmethod
    def from_json(json_str: str) -> 'Result':
        data = json.loads(json_str)
        return Result(success=data['success'], data=data.get('data'), error_message=data.get('error'))
