# Changelog

All notable changes to `html2img-client` are documented here. This project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## [Unreleased]

## [1.0.1] - 2026-08-16

### Fixed

- Declare the licence as an SPDX expression (`license = "MIT"` plus
  `license-files`) instead of a file reference, so PyPI shows "MIT" in the
  project sidebar rather than the full licence text. Packaging metadata only;
  the code is identical to 1.0.0.

## [1.0.0] - 2026-08-16

Initial release of the official Python client for the
[HTML to Image API](https://html2img.com).

### Added

- `Html2img` synchronous client with `html()`, `screenshot()` and `template()`.
- `AsyncHtml2img` asyncio client mirroring the synchronous API.
- `HtmlRequest` and `ScreenshotRequest` dataclasses, with local range checks
  that mirror the server-side validation rules.
- `RenderResponse` covering both the synchronous and the async acceptance
  envelopes, with `is_processing`, `is_pdf` and the full `raw` payload.
- PDF output through `format="pdf"`, including `scale_to_fit`, via the
  [HTML to PDF API](https://html2img.com/html-to-pdf/).
- `download()` and `save()` for keeping a copy of a render.
- Typed exception hierarchy rooted at `Html2imgError`, mapped from the API's
  status codes and `code` field.
- Pluggable transports: the default is built on the standard library, and any
  callable with the same signature can replace it.
- An `html2img` command line interface with `test`, `html`, `screenshot` and
  `template` commands.
- Inline type hints and a `py.typed` marker.

[Unreleased]: https://github.com/html2img/html2img-python/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/html2img/html2img-python/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/html2img/html2img-python/releases/tag/v1.0.0
