[![HTML to Image (html2img): HTML to image API, rendered in real Chrome](https://html2img.com/og-image.png)](https://html2img.com)

# HTML to Image (html2img) for Python

[![PyPI Version](https://img.shields.io/pypi/v/html2img-client)](https://pypi.org/project/html2img-client/)
[![Python Versions](https://img.shields.io/pypi/pyversions/html2img-client)](https://pypi.org/project/html2img-client/)
[![Downloads](https://img.shields.io/pypi/dm/html2img-client)](https://pypi.org/project/html2img-client/)
[![License](https://img.shields.io/pypi/l/html2img-client)](LICENSE)

The official Python client for the [HTML to Image API](https://html2img.com) at html2img.com. Turn HTML and CSS into images, capture screenshots of live URLs, render named templates, and export A4 PDFs, all returning a typed response object.

Every render runs in real Chrome, so flexbox, grid, custom properties, web fonts and inline JavaScript behave exactly as they do in the browser. The package has **zero runtime dependencies** — it is built on the standard library — ships with full type hints and a `py.typed` marker, and works anywhere Python does: Django and Flask apps, Celery workers, AWS Lambda, Jupyter notebooks and one-off scripts. The full API reference lives in the [documentation](https://html2img.com/docs), with a Python-specific guide at [html2img.com/integrations/python](https://html2img.com/integrations/python/).

Three things this package does, each with its own worked guide:

- **[HTML to Image API](https://html2img.com/)** — render a document you control into a PNG.
- **[Screenshot API](https://html2img.com/screenshot-api/)** — capture any public URL, full page or cropped to one element.
- **[HTML to PDF API](https://html2img.com/html-to-pdf/)** — the same markup as a vector A4 PDF with selectable text.

## Contents

- [What you can build](#what-you-can-build)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Render HTML](#render-html)
  - [Capture a screenshot](#capture-a-screenshot)
  - [Generate a PDF](#generate-a-pdf)
  - [Render a template](#render-a-template)
- [Saving renders](#saving-renders)
- [Async](#async)
- [Framework recipes](#framework-recipes)
- [Render options](#render-options)
- [The response](#the-response)
- [Asynchronous delivery](#asynchronous-delivery)
- [Error handling](#error-handling)
- [Custom transports](#custom-transports)
- [Command line](#command-line)
- [Verifying your setup](#verifying-your-setup)
- [Type checking](#type-checking)
- [Other languages and frameworks](#other-languages-and-frameworks)
- [Development](#development)
- [Links](#links)

## What you can build

- **Open Graph and social images**, generated per page or post. See the [Open Graph image template](https://html2img.com/templates/open-graph-image) and [Twitter/X post template](https://html2img.com/templates/twitter-post).
- **Business documents** such as [invoices](https://html2img.com/templates/invoice-image), [receipts](https://html2img.com/templates/receipt-image), [event tickets](https://html2img.com/templates/event-ticket) and [certificates](https://html2img.com/templates/certificate-of-completion) — as PNGs, or as PDFs through the [HTML to PDF API](https://html2img.com/html-to-pdf/).
- **Developer assets** such as [code screenshots](https://html2img.com/templates/code-screenshot) and [GitHub social previews](https://html2img.com/templates/github-social-preview).
- **URL screenshots** through the [Screenshot API](https://html2img.com/screenshot-api/), full page or cropped to a single element, with CSS injection to hide cookie banners and chat widgets before capture.

Browse the [full template library](https://html2img.com/templates), or try the no-signup [browser tools](https://html2img.com/tools) to see the output before you write any code.

## Requirements

- Python 3.9 or newer
- An html2img API key, issued per account from your [dashboard](https://app.html2img.com/register)

Every account starts with 50 free credits and no card is needed to get started. Free-tier renders are hosted for seven days; on any paid [plan](https://html2img.com/pricing) they are hosted permanently, including everything you rendered before upgrading.

> **Keep your API key on the server.** This client is designed for server-side use: web applications, background workers, serverless functions and scripts. Shipping your key in client-side code would let anyone spend your credits.

## Installation

```bash
pip install html2img-client
```

The distribution is named `html2img-client`; the import name is `html2img`:

```python
from html2img import Html2img
```

Set your API key in the environment. The client reads it automatically:

```dotenv
HTML2IMG_API_KEY=your-api-key
```

See the [authentication docs](https://html2img.com/docs/authentication) for issuing and rotating keys, and the [getting started guide](https://html2img.com/docs/getting-started) for a tour of the API.

## Quick start

```python
from html2img import Html2img

client = Html2img()  # reads HTML2IMG_API_KEY from the environment

response = client.html(
    "<h1 style='font: 700 64px system-ui'>Hello from Python</h1>",
    width=1200,
    height=630,
    dpi=2,
)

print(response.url)  # https://i.html2img.com/abc123def456.png
```

## Configuration

Pass configuration to the constructor, or leave it to the environment:

```python
from html2img import Html2img

client = Html2img(
    api_key="your-api-key",  # default: $HTML2IMG_API_KEY
    base_url="https://app.html2img.com",  # default: $HTML2IMG_BASE_URI, then this
    timeout=35.0,  # seconds
)
```

| Variable            | Default                    | Purpose                                                    |
| ------------------- | -------------------------- | ---------------------------------------------------------- |
| `HTML2IMG_API_KEY`  | none                       | Your key, sent as the `X-API-Key` header on every request. |
| `HTML2IMG_BASE_URI` | `https://app.html2img.com` | API base URL. You rarely need to change this.              |

The default timeout of 35 seconds sits just over the 30 second synchronous render budget. For captures likely to exceed it, pass a `webhook_url` on the request rather than raising the timeout — see [asynchronous delivery](#asynchronous-delivery).

A client is cheap to construct and safe to share across threads, so building one at import time and reusing it is fine.

## Usage

Every render method returns a `RenderResponse`. Options can be passed as keyword arguments, or as a request object (`HtmlRequest`, `ScreenshotRequest`) when you would rather build the request up separately.

### Render HTML

`POST /api/html`. Send a complete HTML document and get back an image of the rendered result. Inline your CSS in a `<style>` block, or reference remote stylesheets and web fonts with `<link>` tags in the document head. This is the [HTML to Image API](https://html2img.com/); see the [`html` parameter docs](https://html2img.com/docs/parameters/html).

```python
from html2img import Html2img

client = Html2img()

response = client.html(
    document,  # a complete HTML document
    css="body { background: #0f172a; color: #fff; }",  # injected after load
    width=1200,
    height=630,
    dpi=2,  # retina
)

response.url  # https://i.html2img.com/abc123def456.png
```

Or build the request first, which keeps a long list of options readable and lets you reuse a base configuration:

```python
from html2img import Html2img, HtmlRequest

request = HtmlRequest(
    html=document,
    width=1200,
    height=630,
    dpi=2,
    wait_for_selector="#chart-ready",
)

response = Html2img().html(request)
```

### Capture a screenshot

`POST /api/screenshot`. Fetch a public URL in real Chrome and capture it. Use `selector` to crop to a single element, and `css` to hide cookie banners or chat widgets before the capture. This is the [Screenshot API](https://html2img.com/screenshot-api/); see the [`url` parameter docs](https://html2img.com/docs/parameters/url) and the [`selector` docs](https://html2img.com/docs/parameters/selector).

```python
response = client.screenshot(
    "https://example.com",
    width=1200,
    height=630,
    selector="#hero",
    css=".cookie-banner, .intercom-launcher { display: none !important; }",
    dpi=2,
)
```

Full-page captures grow to the whole scroll length of the document:

```python
response = client.screenshot("https://example.com/pricing", fullpage=True)
```

### Generate a PDF

Set `format="pdf"` on either render and the result comes back as an A4 portrait vector PDF instead of a PNG: text stays selectable and searchable, web fonts are embedded, and long content paginates automatically. The API ignores `width`, `height`, `dpi`, `fullpage` and `selector` in PDF mode, and the response `url` points at a `.pdf` file. One credit, the same as an image. This is the [HTML to PDF API](https://html2img.com/html-to-pdf/); see the [`format` parameter docs](https://html2img.com/docs/parameters/format).

```python
from html2img import Format, Html2img

client = Html2img()

response = client.html(invoice_html, format=Format.PDF)

# Wide content, such as a data table, can be scaled down to the page width
response = client.html(report_html, format="pdf", scale_to_fit=True)

client.save(response, f"invoices/{invoice.number}.pdf")
```

`Format` is a plain string enum, so `format="pdf"` and `format=Format.PDF` are interchangeable.

### Render a template

`POST /api/v1/templates/{slug}`. Render one of the built-in [templates](https://html2img.com/templates) from a data payload, with no markup of your own. The data is validated server-side per template. Templates output PNG only; `format` is not available on template renders.

```python
response = client.template(
    "invoice-image",
    {
        "number": 1042,
        "amount": "£240.00",
        "due_date": "2026-07-01",
    },
)

# Keyword arguments work too, and merge over the mapping
response = client.template("invoice-image", number=1042, amount="£240.00")
```

## Saving renders

The API returns the CDN URL of the render rather than the raw bytes, so you can cache and re-serve it from your own infrastructure. When you would rather keep a copy, `download()` gives you the bytes and `save()` writes them to a path, creating parent directories as needed:

```python
response = client.html(document, width=1200, height=630)

data = client.download(response)  # bytes
path = client.save(response, "og/post-42.png")  # pathlib.Path
```

Both accept a URL string as well as a response, so you can re-download an earlier render:

```python
client.save("https://i.html2img.com/abc123.png", "thumbnails/abc123.png")
```

To store somewhere other than the local filesystem, hand the bytes to whatever storage library you already use:

```python
import boto3

boto3.client("s3").put_object(
    Bucket="my-bucket",
    Key=f"og/{post.id}.png",
    Body=client.download(response),
    ContentType="image/png",
)
```

## Async

`AsyncHtml2img` mirrors the synchronous client method for method:

```python
import asyncio
from html2img import AsyncHtml2img


async def main():
    async with AsyncHtml2img() as client:
        response = await client.html(document, width=1200, height=630)
        print(response.url)


asyncio.run(main())
```

Rendering a batch concurrently is then just `asyncio.gather`:

```python
async with AsyncHtml2img() as client:
    responses = await asyncio.gather(
        *(client.html(render_card(post), width=1200, height=630) for post in posts)
    )
```

Requests run on the default thread pool executor, which keeps the package dependency-free while leaving the event loop free during a render. A render is a single request, so the thread pool is rarely the bottleneck; if you want renders to share your application's own connection pool, pass an `httpx`- or `aiohttp`-backed [custom transport](#custom-transports).

## Framework recipes

### Django

For Open Graph images across a Django site, use the dedicated [html2img Django package](https://github.com/html2img/html2img-django) (`pip install html2img-django`), which adds a model mixin, template tags, an admin action and a management command on top of this client. For one-off renders, this client is enough:

```python
from django.template.loader import render_to_string
from html2img import Html2img


def build_og_image(post):
    html = render_to_string("og/post.html", {"post": post})

    return Html2img().html(html, width=1200, height=630, dpi=2).url
```

### Flask

```python
from flask import Flask, jsonify, render_template
from html2img import Html2img

app = Flask(__name__)
client = Html2img()


@app.get("/posts/<int:post_id>/og-image")
def og_image(post_id: int):
    html = render_template("og.html", post=get_post(post_id))

    return jsonify(url=client.html(html, width=1200, height=630).url)
```

### FastAPI

```python
from fastapi import FastAPI
from html2img import AsyncHtml2img

app = FastAPI()
client = AsyncHtml2img()


@app.get("/og-image")
async def og_image(title: str):
    response = await client.html(f"<h1>{title}</h1>", width=1200, height=630)

    return {"url": response.url}
```

### Celery

Renders are a natural fit for a background task, especially full-page captures:

```python
from celery import shared_task
from html2img import Html2img


@shared_task
def generate_og_image(post_id: int) -> str:
    post = Post.objects.get(pk=post_id)
    client = Html2img()
    response = client.html(render_card(post), width=1200, height=630)

    Post.objects.filter(pk=post_id).update(og_image_url=response.url)

    return response.url
```

For very large captures, prefer [asynchronous delivery](#asynchronous-delivery) over a long-running task.

## Render options

Both renders accept the following. Any option left as `None` is omitted from the request, so the server applies its own default. The complete reference is in the [parameter docs](https://html2img.com/docs/parameters).

| Option              | Type          | Docs                                                                                    |
| ------------------- | ------------- | --------------------------------------------------------------------------------------- |
| `css`               | `str`         | [css](https://html2img.com/docs/parameters/css)                                          |
| `width`             | `int`         | [dimensions](https://html2img.com/docs/parameters/dimensions) (1 to 5000)                |
| `height`            | `int`         | [dimensions](https://html2img.com/docs/parameters/dimensions) (ignored when `fullpage`)  |
| `fullpage`          | `bool`        | [fullpage](https://html2img.com/docs/parameters/fullpage)                                |
| `dpi`               | `int`         | [dpi](https://html2img.com/docs/parameters/dpi) (1 to 4, use 2 for retina)               |
| `webhook_url`       | `str`         | [webhook_url](https://html2img.com/docs/parameters/webhook-url)                          |
| `ms_delay`          | `int`         | [ms_delay](https://html2img.com/docs/parameters/ms_delay) (1 to 5000)                    |
| `wait_for_selector` | `str`         | [wait_for_selector](https://html2img.com/docs/parameters/wait_for_selector)              |
| `format`            | `Format\|str` | [format](https://html2img.com/docs/parameters/format): `"png"` (default) or `"pdf"`      |
| `scale_to_fit`      | `bool`        | PDF only. Scale wide content down to the page width instead of clipping it.              |

`screenshot()` also accepts [`selector`](https://html2img.com/docs/parameters/selector) to crop the capture to a single element. `html()` does not, since you control the markup.

Values are range-checked locally before a request is sent, so an out-of-range `width` raises a `ValueError` immediately rather than spending a credit on a rejected render.

Custom fonts are loaded by referencing them with `<link>` tags in your HTML document head, or by linking a web font from the page you capture. Everything referenced by your markup — fonts, images, stylesheets — is fetched by the renderer over the public internet, so `localhost` URLs will not resolve.

## The response

Every render returns a frozen `RenderResponse` dataclass:

```python
response.success  # bool
response.id  # str | None, the render id
response.url  # str | None, the CDN URL of the render
response.expires_at  # str | None, ISO 8601; None on paid plans
response.credits_remaining  # int | None, credits left after this call
response.status  # str | None, "processing" for async jobs
response.message  # str | None
response.template  # str | None, the template slug, when applicable
response.is_processing  # bool
response.is_pdf  # bool
response.raw  # dict, the full decoded JSON payload
```

`str(response)` is the URL, so a response drops straight into an f-string or a template context.

## Asynchronous delivery

Synchronous requests have a 30 second budget. For captures likely to exceed it, pass a `webhook_url`. The API responds immediately with `status: "processing"` and `url: None`, then POSTs the final URL to your endpoint once rendering finishes. See the [`webhook_url` docs](https://html2img.com/docs/parameters/webhook-url).

```python
response = client.screenshot(
    "https://example.com/long-report",
    fullpage=True,
    webhook_url="https://example.com/hooks/html2img",
)

if response.is_processing:
    ...  # the final URL will arrive at your webhook, not on this response
```

## Error handling

Every request-time failure raises an `Html2imgError` or one of its subclasses. Catch that single type to handle any error, or catch a specific subclass. No raw `urllib` error escapes the package. Invalid arguments are reported before any request is sent, as a plain `ValueError` or `TypeError`.

```python
from html2img import (
    Html2img,
    Html2imgError,
    InsufficientCreditsError,
    ValidationError,
)

try:
    response = Html2img().html(document)
except ValidationError as error:
    # 400 or 422: inspect the per-field messages
    for field, messages in error.details.items():
        print(field, messages)
except InsufficientCreditsError as error:
    print("Out of credits:", error.credits_remaining)
except Html2imgError as error:
    error.status_code  # int | None
    error.error_code  # str | None, the API "code" field
    error.payload  # dict, the decoded body
```

| Exception                  | When                                                            |
| -------------------------- | --------------------------------------------------------------- |
| `AuthenticationError`      | 401, missing or invalid API key.                                 |
| `InsufficientCreditsError` | 402, no credits remaining. Exposes `credits_remaining`.          |
| `NotSubscribedError`       | 403, no active subscription.                                     |
| `NotFoundError`            | 404, for example an unknown template slug.                       |
| `ValidationError`          | 400 or 422, with `details` per field.                            |
| `RateLimitError`           | 429, rate or quota exceeded. Exposes `retry_after`.              |
| `TimeoutError`             | 408 or 504, or the local timeout elapsed.                        |
| `ServerError`              | 5xx, an unexpected renderer error.                               |
| `ConnectionError`          | the request never reached a response.                            |
| `Html2imgError`            | base type for all of the above.                                  |

`TimeoutError` and `ConnectionError` share a name with the built-ins, and are strict subclasses of them, so existing `except TimeoutError:` code keeps working either way.

Retries are left to you, so that a retry policy fits your application rather than the other way round. A 5xx or a `ConnectionError` is worth retrying; a 4xx is not.

## Custom transports

All HTTP goes through a single callable, which is the seam for retry middleware, proxies, connection pooling and tests. The default is `UrllibTransport`, built on the standard library. To use `requests` instead:

```python
import requests
from html2img import Html2img

session = requests.Session()


def requests_transport(*, method, url, headers, body, timeout):
    response = session.request(method, url, headers=headers, data=body, timeout=timeout)

    return response.status_code, response.content


client = Html2img(transport=requests_transport)
```

The client still sends the `X-API-Key`, `Accept` and `Content-Type` headers on every request, and still maps every status onto the same typed exceptions.

In tests, a transport is the simplest way to avoid the network entirely:

```python
def fake_transport(*, method, url, headers, body, timeout):
    return 200, b'{"success": true, "url": "https://i.html2img.com/test.png"}'


client = Html2img("test-key", transport=fake_transport)
assert client.html("<h1>Hi</h1>").url == "https://i.html2img.com/test.png"
```

## Command line

Installing the package also installs an `html2img` command:

```bash
html2img test                                              # verify your setup
html2img html card.html --width 1200 --height 630 -o card.png
html2img html - --format pdf -o report.pdf < report.html   # read stdin
html2img screenshot https://example.com --fullpage -o shot.png
html2img screenshot https://example.com --selector "#hero" -o hero.png
html2img template invoice-image --data '{"number": 1042}'
```

Every command prints the resulting URL, and `--out/-o` also saves the render locally. Run `html2img --help` for the full list.

## Verifying your setup

Confirm your key and configuration by rendering a small test image:

```bash
html2img test
```

It prints the resulting image URL and your remaining credits, or a clear error if the key is missing or rejected. The check uses one credit. There is also a [testing guide](https://html2img.com/docs/testing) for the API itself.

## Type checking

The package ships inline type hints and a `py.typed` marker, so mypy and Pyright type-check your calls with no stubs to install:

```python
from html2img import Html2img, RenderResponse


def og_image_url(document: str) -> str | None:
    response: RenderResponse = Html2img().html(document, width=1200, height=630)

    return response.url
```

## Other languages and frameworks

The same API has official packages for other languages and platforms, all available now:

- **SDKs:** [PHP](https://github.com/html2img/html2img-php) · [JavaScript and TypeScript](https://github.com/html2img/html2img-js) · [Ruby](https://github.com/html2img/html2img-ruby)
- **Frameworks:** [Laravel](https://github.com/html2img/html2img-laravel) · [Django](https://github.com/html2img/html2img-django)
- **CMS plugins:** [WordPress](https://wordpress.org/plugins/html2img/) · [Statamic](https://github.com/html2img/statamic-og-images) · [Craft CMS](https://plugins.craftcms.com/og-images)
- **Automation and AI:** [GitHub Action](https://github.com/marketplace/actions/html-to-image) · [MCP server](https://html2img.com/mcp/) (every plan, free included)

There are also worked guides for [React](https://html2img.com/integrations/javascript/#react-and-nextjs) and [Vue](https://html2img.com/integrations/javascript/#vue-and-nuxt), and anything that can make an HTTP request works with the API. Every integration is listed on the [integrations hub](https://html2img.com/integrations/).

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

pytest              # tests, no network and no credits spent
ruff check .        # lint
ruff format .       # format
mypy                # static analysis
```

Publishing to PyPI is covered in [PUBLISHING.md](PUBLISHING.md).

## Links

[HTML to Image API](https://html2img.com) · [Screenshot API](https://html2img.com/screenshot-api/) · [HTML to PDF API](https://html2img.com/html-to-pdf/) · [Documentation](https://html2img.com/docs) · [Python guide](https://html2img.com/integrations/python/) · [Templates](https://html2img.com/templates) · [Tools](https://html2img.com/tools) · [Features](https://html2img.com/features) · [Comparisons](https://html2img.com/compare) · [Articles](https://html2img.com/articles) · [Pricing](https://html2img.com/pricing) · [Django package](https://github.com/html2img/html2img-django)

## Licence

MIT. See [LICENSE](LICENSE).
