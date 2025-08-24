from flask import Flask, render_template, request, jsonify
import re
import json
from typing import Any, Dict, List, Union

app = Flask(__name__)

class JsonSchemaValidator:
    def __init__(self):
        self.errors: List[str] = []

    def validate(self, document: Any, schema: Dict[str, Any]) -> bool:
        """Validate JSON document against schema"""
        self.errors.clear()
        return self._validate_value(document, schema, "")

    def get_errors(self) -> List[str]:
        return self.errors

    def _validate_value(self, value: Any, schema: Dict[str, Any], path: str) -> bool:
        if not isinstance(schema, dict):
            self.errors.append(f"{path}: Schema must be an object")
            return False

        if "type" in schema:
            if not self._validate_type(value, schema["type"], path):
                return False

        if "enum" in schema:
            if not self._validate_enum(value, schema["enum"], path):
                return False

        if "pattern" in schema and isinstance(value, str):
            if not self._validate_pattern(value, schema["pattern"], path):
                return False

        if "required" in schema and isinstance(value, dict):
            if not self._validate_required(value, schema["required"], path):
                return False

        if "properties" in schema and isinstance(value, dict):
            if not self._validate_properties(value, schema.get("properties", {}), path):
                return False

        if "items" in schema and isinstance(value, list):
            if not self._validate_array_items(value, schema["items"], path):
                return False

        return True

    def _validate_type(self, value: Any, expected_type: Union[str, List[str]], path: str) -> bool:
        if isinstance(expected_type, list):
            for t in expected_type:
                if self._check_single_type(value, t):
                    return True
            self.errors.append(f"{path}: Value {repr(str(value))} is not one of types {expected_type}")
            return False
        else:
            if not self._check_single_type(value, expected_type):
                self.errors.append(f"{path}: Value {repr(str(value))} is not of type {expected_type}")
                return False
            return True

    def _check_single_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "string": lambda x: isinstance(x, str),
            "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "boolean": lambda x: isinstance(x, bool),
            "object": lambda x: isinstance(x, dict),
            "array": lambda x: isinstance(x, list),
            "null": lambda x: x is None
        }
        return type_map.get(expected_type, lambda x: False)(value)

    def _validate_enum(self, value: Any, enum_values: List[Any], path: str) -> bool:
        if value not in enum_values:
            self.errors.append(f"{path}: Value {repr(str(value))} is not in enum {enum_values}")
            return False
        return True

    def _validate_pattern(self, value: str, pattern: str, path: str) -> bool:
        try:
            if not re.match(pattern, value):
                self.errors.append(f"{path}: String '{value}' doesn't match pattern '{pattern}'")
                return False
            return True
        except re.error:
            self.errors.append(f"{path}: Invalid regex pattern '{pattern}'")
            return False

    def _validate_required(self, obj: Dict[str, Any], required_props: List[str], path: str) -> bool:
        valid = True
        for prop in required_props:
            if prop not in obj:
                self.errors.append(f"{path}: Missing required property '{prop}'")
                valid = False
        return valid

    def _validate_properties(self, obj: Dict[str, Any], properties_schema: Dict[str, Any], path: str) -> bool:
        valid = True
        for prop, value in obj.items():
            prop_path = f"{path}.{prop}" if path else prop
            if prop in properties_schema:
                if not self._validate_value(value, properties_schema[prop], prop_path):
                    valid = False
        return valid

    def _validate_array_items(self, array: List[Any], items_schema: Dict[str, Any], path: str) -> bool:
        valid = True
        for i, item in enumerate(array):
            item_path = f"{path}[{i}]"
            if not self._validate_value(item, items_schema, item_path):
                valid = False
        return valid

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'valid': False, 'errors': ['No JSON data provided']})

        json_data = data.get('json', '{}')
        schema_data = data.get('schema', '{}')

        # Parse JSON and schema
        try:
            json_obj = json.loads(json_data)
        except json.JSONDecodeError as e:
            return jsonify({'valid': False, 'errors': [f'Invalid JSON: {str(e)}']})

        try:
            schema_obj = json.loads(schema_data)
        except json.JSONDecodeError as e:
            return jsonify({'valid': False, 'errors': [f'Invalid JSON Schema: {str(e)}']})

        # Validate
        validator = JsonSchemaValidator()
        is_valid = validator.validate(json_obj, schema_obj)

        return jsonify({
            'valid': is_valid,
            'errors': validator.get_errors()
        })

    except Exception as e:
        return jsonify({'valid': False, 'errors': [f'Unexpected error: {str(e)}']})

if __name__ == '__main__':
    app.run(debug=True)