"""Export JSON Schema for UI/editor tooling from the same Python contract."""

import json
from pathlib import Path

from app.schemas.content import ContentBundle


def main():
    path = Path(__file__).resolve().parents[1] / "data/schemas/content_bundle.schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(ContentBundle.model_json_schema(), indent=2) + "\n").encode())
    print(path)


if __name__ == "__main__":
    main()
