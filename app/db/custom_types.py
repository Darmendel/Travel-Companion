import json
from sqlalchemy.types import TypeDecorator, TEXT

class StringList(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        # Convert Python list → JSON string before storing
        if value is None:
            return "[]"
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        # Convert JSON string → Python list when reading
        if value is None:
            return []
        return json.loads(value)
