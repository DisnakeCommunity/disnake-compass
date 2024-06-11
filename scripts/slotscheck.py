"""Wrapper around slotscheck to convert filenames to modules.

This is guaranteed to not be best practice or anything of the sort, but with
the wacky file structure and the way ext-components is installed into the
disnake namespace, `slotscheck -m <module>` is the only way I could get
slotscheck to run properly.

Since pre-commit passes filepaths (relative to cwd), this wrapper was written
to turn those filepaths into module identifiers to be passed to slotscheck.
Note that this is NOT a generalised script that works for any lib with any
setup, but 99% of libs should not have this problem in the first place.
"""

import argparse
import pathlib
import subprocess
import sys

_PROJECT_ROOT = (pathlib.Path.cwd() / "src").resolve()


def _main() -> None:
    # Parse command-line args into pathlib.Path objects...
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=pathlib.Path)
    result = parser.parse_args()
    input_paths: list[pathlib.Path] = result.files

    # Setup command list for the actual call to slotscheck:
    # > python -m slotscheck -v --require-subclass -m <module1> -m <module2> ...
    #
    # - sys.executable: path to python executable used to run this script,
    # - "-m": Run an installed python module,
    # - "slotscheck": Run the slotscheck module,
    # - "-v": Verbose output,
    # - "--require-subclass": Require subclasses of slotted classes to also be slotted.

    args: list[str] = [sys.executable, "-m", "slotscheck", "-v", "--require-subclass"]

    for path in input_paths:
        try:
            # Try to get path relative to cwd.
            relative_path = path.resolve().relative_to(_PROJECT_ROOT)
        except ValueError:
            # Path probably not on "src/", therefore safe to ignore.
            continue

        # Shouldn't happen as we run slotscheck with `- files: [python]`
        # but a little checking never hurt anyone.
        if relative_path.suffix != ".py":
            continue

        # Get the module identifier; in case of __init__.py, we just use the
        # folder as module, otherwise the python file will be the module.
        filename = relative_path.stem
        module = ".".join(relative_path.parts[:-1])
        if filename != "__init__":
            module += f".{filename}"

        # Add the module to the argument list.
        args.append("-m")
        args.append(module)

    # Open a new subprocess that calls our new argument list.
    process = subprocess.run(args, capture_output=True, cwd=_PROJECT_ROOT, check=False)
    if process.returncode != 0:
        print("", process.stdout.decode(), process.stderr.decode(), sep="\n")
    else:
        print(process.stdout.decode())

    # And finally, propagate slotscheck's return code.
    sys.exit(process.returncode)


if __name__ == "__main__":
    _main()
