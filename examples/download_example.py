"""Download the public example document used in the README demo.

Fetches "Attention Is All You Need" (Vaswani et al., 2017) from arXiv so the demo
runs against a real, public document rather than fabricated data (CLAUDE.md §5).

The PDF is intentionally NOT committed to the repository (it is git-ignored to
avoid redistributing a third-party paper) — run this script to fetch it locally.
"""

import urllib.request
from pathlib import Path

URL = "https://arxiv.org/pdf/1706.03762"
DEST = Path(__file__).parent / "attention-is-all-you-need.pdf"


def main() -> None:
    print(f"Downloading {URL} ...")
    urllib.request.urlretrieve(URL, DEST)  # noqa: S310 (trusted arXiv URL)
    print(f"Saved to {DEST} ({DEST.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
