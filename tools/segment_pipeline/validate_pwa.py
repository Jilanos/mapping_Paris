from __future__ import annotations

from pathlib import Path


REQUIRED_FILES = [
    Path("pwa/index.html"),
    Path("pwa/app.js"),
    Path("pwa/styles.css"),
    Path("pwa/manifest.webmanifest"),
    Path("pwa/service-worker.js"),
    Path("data/generated/paris_segments.geojson"),
]


def main() -> int:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        print("Missing PWA files:")
        for path in missing:
            print(f"- {path}")
        return 1

    app_js = Path("pwa/app.js").read_text(encoding="utf-8")
    index_html = Path("pwa/index.html").read_text(encoding="utf-8")
    required_tokens = [
        "paris_segments.geojson",
        "localStorage",
        "toggleValidation",
        "L.geoJSON",
        "preferCanvas",
    ]
    missing_tokens = [token for token in required_tokens if token not in app_js + index_html]
    if missing_tokens:
        print("Missing expected PWA behavior tokens:")
        for token in missing_tokens:
            print(f"- {token}")
        return 1

    print("PWA static validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
