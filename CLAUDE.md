# aiskills Project

## Web Scraping

Always use Playwright via the `playwright_lib` venv — do NOT use `browser-use` for scraping:

```bash
playwright_lib/.venv/Scripts/python.exe your_script.py
```

Reasons to avoid `browser-use` for scraping:
- Remote mode requires a paid API key (`BROWSER_USE_API_KEY` not configured)
- Local chromium mode fails to start the session server on this machine
- The CLI is not on the bash PATH (lives in `AppData\Local\Packages\...`)

## Python Environments

| Venv | Path | Use for |
|------|------|---------|
| playwright_lib | `playwright_lib/.venv/` | Web scraping with Playwright |
| jobhunt | `jobhunt/.venv/` | Job hunt scripts, Google API, PDF generation |

## browser-use CLI (non-scraping use)

If you ever need `browser-use` for agent tasks (requires API key), use the full path:

```
/c/Users/danny/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/Scripts/browser-use.exe
```
