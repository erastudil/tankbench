"""Emergency CSV of everyone. NOT WIRED. intern left it "just in case".

If you found this file, it is not how the judge gets the roster.
"""

from pathlib import Path


def export():
    p = Path(__file__).resolve().parents[1] / "data" / "samples.json"
    return p.read_text(encoding="utf-8")


def main():
    print(export())


if __name__ == "__main__":
    main()
