"""CLI for safely exporting reviewed Aeryvex characters to a standalone Godot project."""
import argparse
import json
from .character_pack import export_character


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--character", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(export_character(args.project_path, args.character, args.output), indent=2))


if __name__ == "__main__":
    main()
