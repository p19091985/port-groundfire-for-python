import sys

def report(fmt: str, *args) -> None:
    """
    Reports an error (usually a fatal one).
    Equivalent to the C++ report function.
    """
    try:
        if args:
            msg = fmt % args
        else:
            msg = fmt
        print(msg)
    except Exception as e:
        print(f"Error formatting report message: {e}")
        print(fmt)

def debug(fmt: str, *args) -> None:
    """
    Outputs debug information.
    Equivalent to the C++ debug function.
    """
    try:
        if args:
            msg = fmt % args
        else:
            msg = fmt
        print(msg)
    except Exception as e:
        print(f"Error formatting debug message: {e}")
        print(fmt)
