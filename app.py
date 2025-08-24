from flask import Flask, render_template, request
import json
import jsonschema
from jsonschema import Draft7Validator

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    errors = []

    if request.method == "POST":
        schema_file = request.files["schema_file"]
        data_file = request.files["data_file"]

        # ✅ Prevent user from uploading same file for both
        if schema_file.filename == data_file.filename:
            result = "❌ Schema file and Data file cannot be the same. Please upload different files."
            return render_template("index.html", result=result, errors=errors)

        try:
            schema = json.load(schema_file)
            data = json.load(data_file)

            # ✅ Prevent identical contents
            if schema == data:
                result = "❌ Schema and Data contents are identical. Please upload different files."
                return render_template("index.html", result=result, errors=errors)

            # ✅ Validate using Draft7Validator to collect all errors
            validator = Draft7Validator(schema)
            errors = [f"{error.message} (at path: {list(error.path)})" for error in validator.iter_errors(data)]

            if errors:
                result = "❌ JSON data is invalid!"
            else:
                result = "✅ JSON data is valid according to the schema!"

        except jsonschema.exceptions.SchemaError as se:
            result = f"❌ Invalid schema: {str(se)}"
        except json.decoder.JSONDecodeError:
            result = "❌ One of the files is not a valid JSON file."
        except Exception as e:
            result = f"❌ Error: {str(e)}"

    return render_template("index.html", result=result, errors=errors)

if __name__ == "__main__":
    app.run(debug=True)
