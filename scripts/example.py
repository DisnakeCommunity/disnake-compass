"""A simple CLI command to run example files with a bot token from env."""

import argparse
import importlib.util
import os
import subprocess
import sys
import typing

import dotenv

_KEY: typing.Final[str] = "EXAMPLE_TOKEN"


def _main() -> typing.NoReturn:
    # First, get the token from dotenv.
    dotenv.load_dotenv()

    token = os.getenv(_KEY)
    if not token:
        print("Token not found! Please set 'EXAMPLE_TOKEN' in .env.")
        sys.exit(1)

    choices = [
        file[:-3]
        for file in os.listdir(os.path.realpath("examples"))
        if file.endswith(".py")
    ]

    # Get the passed example using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("example", type=str, choices=choices)

    result = parser.parse_args()
    example: str = f"examples.{result.example}"

    # Check if example module exists:
    if not importlib.util.find_spec(example):
        print(f"Cound not find example {example!r}.")
        sys.exit(1)

    # Run example with unbuffered (-u) python.
    args = ["poetry", "run", "python", "-u", "-m", example]

    # Open a subprocess that runs our args list.
    print(f"Running example {example!r}...")

    try:
        with subprocess.Popen(
            args,
            # Pipe all output to stdout...
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            # Ensure proper cwd...
            cwd=os.getcwd(),
            # Set buffer mode to line-buffered...
            bufsize=1,
            # Set stdout mode to text...
            text=True,
            # Provide bot token environment variable...
            env={**os.environ, _KEY: token},
        ) as process:
            if not process.stdout:
                print("Failed to open stdout.")
                sys.exit(1)

            for line in process.stdout:
                print(line, end="")

    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, stopping example.")
        sys.exit(0)

    # And finally, propagate the return code.
    sys.exit(process.returncode)


if __name__ == "__main__":
    _main()
