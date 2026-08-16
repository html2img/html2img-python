# Publishing `html2img-client` to PyPI

A step-by-step guide written for someone who has published to Packagist and npm
but not to PyPI. If you only want the short version, jump to
[the release checklist](#the-release-checklist).

## How PyPI differs from Packagist and npm

| | Packagist | npm | PyPI |
| --- | --- | --- | --- |
| What you push | nothing — it reads your git tags | a tarball built by `npm publish` | build artefacts you upload (`.whl` + `.tar.gz`) |
| Where the version lives | `git` tag | `package.json` | your project metadata (here: `src/html2img/_version.py`) |
| Name registration | on first submit | on first publish | on first upload |
| Can you delete a release? | yes, it just re-reads git | within 72 hours | no — you can only *yank* it |
| Can you re-upload the same version? | n/a | no | no, and not even the same *filename* |

Three consequences worth internalising:

1. **A version number is spent the moment you upload it.** If `1.0.0` has a
   broken README, you publish `1.0.1`. There is no `--force`.
2. **Nothing is derived from git.** Tagging alone publishes nothing. The version
   in `_version.py` is the version, and the tag is only a convention.
3. **Use TestPyPI first.** It is a completely separate site with separate
   accounts, and it is the only safe place to rehearse.

## The package name

Two names matter and they are deliberately different:

- **Distribution name** — `html2img-client`. This is what people `pip install`,
  and what is reserved on PyPI. It mirrors `@html2img/client` on npm.
- **Import name** — `html2img`. This is what people write in their code.

> **One thing to decide before the first upload.** The bare name `html2img` on
> PyPI is already taken by an unrelated, abandoned 0.1.0 package (a Playwright
> wrapper published in June 2025), which is why the distribution is
> `html2img-client`. That package almost certainly also installs a top-level
> `html2img` module, so the two cannot be installed side by side. In practice
> this is very unlikely to bite anyone, and taking the obvious import name is
> worth it for the brand. If you would rather avoid the collision entirely,
> rename the import package before the first release: `git mv
> src/html2img src/html2img_client`, update the imports, and change
> `packages = ["src/html2img"]` and `html2img = "html2img.cli:_entrypoint"` in
> `pyproject.toml`. It is a one-line-per-file change now and a breaking change
> later, so decide before `1.0.0` goes out.

## One-time setup

### 1. Create the accounts

Register **one account for the brand, not for yourself**. PyPI has no vendor
namespace — unlike the `@html2img` scope on npm or the `html2img/` vendor on
Packagist — so the account is the only place the brand identity lives, and it
keeps the asset separable if html2img is ever sold. Nothing in PyPI's Terms of
Use restricts accounts to individuals.

At [pypi.org/account/register](https://pypi.org/account/register/):

| Field | Use |
| --- | --- |
| Username | `html2img` |
| Email | `pypi@html2img.com` — a mailbox on the domain, so it moves with the business |
| 2FA | Mandatory. Put the authenticator seed in the company password manager, not only on a phone |
| Recovery codes | Store them with the other company credentials |

The email matters more than it looks. PyPI's
[name-retention policy](https://docs.pypi.org/project-management/name-retention/)
makes the owner "solely responsible for being reachable", and a project name can
be reassigned if they cannot reach you. A brand mailbox survives staff changes;
a personal address does not.

Then register a second account on
[test.pypi.org](https://test.pypi.org/account/register/) — a completely separate
site, used only for rehearsals.

Once a project exists, optionally add a colleague's personal account as a
**Maintainer** under its Collaborators settings. It is additive, free, and means
you are not the only person who can ship.

**Do you need a PyPI organisation?** No.
[Organisations](https://docs.pypi.org/organization-accounts/) cost
[$5 per member per month](https://docs.pypi.org/organization-accounts/pricing-and-payments/)
for commercial projects (community projects are free, but a commercial product
will be assessed as corporate), and they buy a listing page and team management
you do not need at this size. The one feature worth having — reserving the
`html2img-` prefix under [PEP 752](https://peps.python.org/pep-0752/), accepted
in June 2026 — is not implemented on PyPI yet. You can create an organisation
later and transfer these projects into it, so nothing here forecloses it.

### 2. Install the build tools

```bash
python -m pip install --upgrade build twine
```

`build` produces the artefacts, `twine` validates and uploads them.

### 3. Choose how you will upload

**Trusted Publishing (recommended).** GitHub Actions authenticates to PyPI over
OIDC, so there is no long-lived token anywhere. `.github/workflows/publish.yml`
in this repo is already written for it. Configure it once, after the first
manual upload has created the project (see below).

**API token (needed for the very first upload).** Trusted publishing can only be
configured against an existing project *or* as a "pending publisher". The
simplest path for a first release is: upload once with a token, then switch to
trusted publishing for every release after that.

## Your first release

### Step 1 — check the metadata

Open `pyproject.toml` and confirm:

- `name = "html2img-client"`
- `version` comes from `src/html2img/_version.py` (currently `1.0.0`)
- the `[project.urls]` block points at the real GitHub repo

### Step 2 — build

```bash
rm -rf dist/
python -m build
```

You get two files in `dist/`:

```
dist/html2img_client-1.0.0-py3-none-any.whl   # the wheel, what pip installs
dist/html2img_client-1.0.0.tar.gz             # the sdist, the source archive
```

### Step 3 — validate

```bash
twine check dist/*
```

This is mostly a README check: PyPI renders your Markdown, and a README that
fails to render is the most common first-release disappointment. It should print
`PASSED` for both files.

### Step 4 — rehearse on TestPyPI

Create a TestPyPI API token at
[test.pypi.org/manage/account/token](https://test.pypi.org/manage/account/token/)
(scope: "Entire account" for the first upload), then:

```bash
twine upload --repository testpypi dist/*
```

Username is `__token__` (literally), password is the token including its
`pypi-` prefix.

Now install it somewhere clean and make sure it actually works:

```bash
python -m venv /tmp/h2i && source /tmp/h2i/bin/activate
pip install --index-url https://test.pypi.org/simple/ html2img-client
python -c "from html2img import Html2img; print(Html2img.DEFAULT_BASE_URL)"
HTML2IMG_API_KEY=your-key html2img test
deactivate
```

Check the rendered page at `https://test.pypi.org/project/html2img-client/`:
badges, headings, tables and links should all look right.

### Step 5 — publish for real

Create a PyPI API token at
[pypi.org/manage/account/token](https://pypi.org/manage/account/token/) (scope:
"Entire account", since the project does not exist yet), then:

```bash
twine upload dist/*
```

Username `__token__`, password the token. The project is now live at
[pypi.org/project/html2img-client](https://pypi.org/project/html2img-client/).

### Step 6 — lock the token down and switch to trusted publishing

1. Go to
   `https://pypi.org/manage/project/html2img-client/settings/publishing/`.
2. Add a GitHub publisher:
   - **Owner**: `html2img`
   - **Repository**: `html2img-python`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
3. In the GitHub repo, create an environment named `pypi` under
   **Settings → Environments**. No secrets needed.
4. Delete the account-scoped token you used in step 5, and create a
   project-scoped one only if you still want a manual fallback.

From now on, publishing a GitHub release runs `.github/workflows/publish.yml`,
which builds and uploads with no token involved.

## Every release after the first

1. Make your changes and get CI green.
2. Bump the version in `src/html2img/_version.py`. Semantic versioning: a bug fix
   is a patch, a new option is a minor, a changed signature is a major.
3. Move the `Unreleased` entries in `CHANGELOG.md` under the new version, with
   today's date, and update the link definitions at the bottom.
4. Commit, tag and push:

   ```bash
   git commit -am "Release 1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```

5. Create the GitHub release from the tag (`gh release create v1.1.0 --generate-notes`).
   Publishing the release triggers the workflow, which builds and uploads to PyPI.
6. Confirm: `pip index versions html2img-client`, and check the project page.

## The release checklist

```
[ ] CI green on main
[ ] Version bumped in src/html2img/_version.py
[ ] CHANGELOG.md updated with the new version and date
[ ] rm -rf dist/ && python -m build
[ ] twine check dist/*
[ ] git tag vX.Y.Z && git push --tags
[ ] GitHub release published (this uploads to PyPI)
[ ] pip install html2img-client in a clean venv and run `html2img test`
[ ] Project page renders correctly on pypi.org
```

## If something goes wrong

- **"File already exists"** — that version is spent. Bump and re-release.
- **A broken release is live** — *yank* it from the release's page on PyPI.
  Yanking leaves it installable for anyone who pins it exactly, but hides it from
  new resolutions. Then publish a fixed version. Deleting is possible but
  strongly discouraged, and it does not free the version number.
- **The README does not render** — PyPI is stricter than GitHub. Raw HTML is
  stripped, and relative image paths do not resolve. Use absolute URLs (this
  README already does).
- **Trusted publishing fails with a permissions error** — the job needs
  `permissions: id-token: write` and the `environment: name: pypi` block, and
  the environment name must match what you configured on PyPI exactly.

## If html2img changes hands

Publishing rights live in two places, and both transfer cleanly:

1. **The GitHub org.** Trusted publishing is bound to the repository
   `html2img/html2img-python`, not to a person, so the new owner can publish the
   moment the org transfers. For the same reason, keep 2FA enforced on that org.
2. **The PyPI account.** Hand over the `html2img` login, its 2FA seed and its
   recovery codes. The `pypi@html2img.com` mailbox travels with the domain.

```
[ ] Domain transferred (takes the pypi@ mailbox with it)
[ ] GitHub org transferred, 2FA still enforced
[ ] npm org (@html2img) transferred
[ ] PyPI account credentials, 2FA seed and recovery codes handed over
[ ] Any personal accounts removed from each project's Collaborators
[ ] Buyer rotates the PyPI password, 2FA and any API tokens
```

If you would rather not hand over the account itself, there is a per-project
alternative that needs no credential exchange: add the buyer's account as
**Owner** on each project, then remove yours.

## Related

- The Django integration publishes to PyPI the same way; see
  `PUBLISHING.md` in [html2img-django](https://github.com/html2img/html2img-django).
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
