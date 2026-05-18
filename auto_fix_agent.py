#!/usr/bin/env python3
"""
Auto-Fix Agent for Playwright Python test suite.

Workflow:
  1. Run pytest and capture failures
  2. Send failures + source files to Claude for analysis
  3. Apply suggested code fixes
  4. Re-run tests to verify
  5. Commit changes and open a GitHub PR
"""

import json
import os
import re
import subprocess
import sys
import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, **kwargs)


def _banner(msg):
    print(f"\n{'─' * 60}")
    print(f"  {msg}")
    print('─' * 60)


# ---------------------------------------------------------------------------
# Step 1 – Run tests
# ---------------------------------------------------------------------------

def run_tests(paths=None):
    """Return (all_passed: bool, combined_output: str)."""
    cmd = [
        PYTHON, "-m", "pytest",
        "-v", "--tb=long", "--no-header",
        "-p", "no:allure",         # skip allure to keep output clean
    ]
    if paths:
        cmd.extend(paths)
    result = _run(cmd)
    output = result.stdout + "\n" + result.stderr
    return result.returncode == 0, output


# ---------------------------------------------------------------------------
# Step 2 – Parse failures from pytest output
# ---------------------------------------------------------------------------

def parse_failures(output):
    """
    Returns list of dicts:
      { test_name, file_path, error_summary, traceback_block }
    """
    failures = []

    # Collect FAILED lines:  FAILED tests/foo.py::TestClass::test_name - Error...
    failed_re = re.compile(r"^FAILED (tests/[^:]+)::(.+?) - (.+)$", re.MULTILINE)
    for m in failed_re.finditer(output):
        failures.append({
            "file_path": m.group(1),
            "test_name": m.group(2).strip(),
            "error_summary": m.group(3).strip(),
        })

    # Attach the full traceback block for each failure
    blocks_re = re.compile(r"_{10,} (.+?) _{10,}\n(.*?)(?=\n_{10,}|\Z)", re.DOTALL)
    for m in blocks_re.finditer(output):
        block_name = m.group(1).strip()
        block_body = m.group(2).strip()
        for f in failures:
            if f["test_name"] in block_name or block_name in f["test_name"]:
                f["traceback_block"] = block_body
                break

    return failures


# ---------------------------------------------------------------------------
# Claude caller – Anthropic SDK (CI) with fallback to local CLI
# ---------------------------------------------------------------------------

def _call_claude(prompt: str) -> str | None:
    """
    Send a prompt to Claude and return the text response.
    Prefers the Anthropic Python SDK (works in CI with ANTHROPIC_API_KEY).
    Falls back to the local `claude` CLI for local runs.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except ImportError:
            print("[WARN] anthropic SDK not installed, falling back to claude CLI")
        except Exception as e:
            print(f"[ERROR] Anthropic SDK call failed: {e}")
            return None

    # Local fallback – claude CLI
    result = subprocess.run(
        ["claude", "-p", "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        print(f"[ERROR] Claude CLI returned non-zero: {result.stderr[:300]}")
        return None
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Step 3 – Ask Claude to produce fixes
# ---------------------------------------------------------------------------

def _read(rel_path):
    p = PROJECT_ROOT / rel_path
    return p.read_text() if p.exists() else None


def _collect_source_files():
    files = {}
    for d, pattern in [("pages", "*.py"), ("tests", "*.py")]:
        for f in (PROJECT_ROOT / d).glob(pattern):
            rel = str(f.relative_to(PROJECT_ROOT))
            files[rel] = f.read_text()
    for rel in ("conftest.py", "data/testdata.json", "pytest.ini"):
        c = _read(rel)
        if c:
            files[rel] = c
    return files


def ask_claude_for_fixes(failures, full_output):
    """
    Send failure info + source to Claude CLI (-p / print mode).
    Returns the parsed JSON fix plan or None on failure.
    """
    source_files = _collect_source_files()
    files_section = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in source_files.items()
    )

    failure_summary = "\n".join(
        f"- {f['file_path']}::{f['test_name']}\n  Error: {f.get('error_summary','')}\n"
        + (f"  Traceback:\n{f.get('traceback_block','')}" if "traceback_block" in f else "")
        for f in failures
    )

    prompt = f"""You are an expert QA engineer working on a Playwright Python test suite
for the SauceDemo demo site (https://www.saucedemo.com).

## Source files

{files_section}

## Failing tests

{failure_summary}

## Full pytest output

```
{full_output[:6000]}
```

## Your task

Analyse each failure, find the root cause, and provide the minimal fix.

Rules:
- Fix only what is broken; do not refactor or change passing tests.
- Prefer fixing page objects when a selector/method is wrong.
- If a test references a wrong test-data key, fix the test to use the correct key.
- Do NOT change test logic unless it is genuinely wrong.
- NEVER modify base_page.py or any quality/validation method (assert_text_has_no_html,
  pytest_check soft assertions, regex content checks). These exist to catch real bugs —
  weakening them to make a test pass is always wrong.
- If a test fails because a quality check catches a suspicious UI pattern (e.g. method-like
  text in a product name), do NOT fix it — leave it for human review.
- Only fix: wrong CSS selectors, wrong locator IDs, hardcoded wrong expected values,
  wrong test data keys.

Respond with ONLY a valid JSON object (no markdown fences, no extra text):

{{
  "summary": "one-sentence summary of all issues",
  "fixes": [
    {{
      "file": "relative/path/to/file.py",
      "description": "what was wrong and what changed",
      "original": "exact verbatim text to replace",
      "replacement": "exact verbatim replacement text"
    }}
  ]
}}

If there is nothing to fix in code (e.g. the site is down), return:
{{"summary": "no code fixes needed", "fixes": []}}
"""

    print("[*] Sending to Claude for analysis…")
    response = _call_claude(prompt)
    if response is None:
        return None

    # Strip markdown fences if Claude wrapped the JSON anyway
    response = re.sub(r"^```(?:json)?\s*", "", response, flags=re.MULTILINE)
    response = re.sub(r"```\s*$", "", response, flags=re.MULTILINE).strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract a JSON object
        m = re.search(r"\{.*\}", response, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        print(f"[ERROR] Could not parse Claude response as JSON.\nResponse:\n{response[:500]}")
        return None


# ---------------------------------------------------------------------------
# Step 4 – Apply fixes
# ---------------------------------------------------------------------------

def apply_fixes(fix_plan):
    """Apply file patches from the Claude fix plan. Returns count of applied fixes."""
    fixes = fix_plan.get("fixes", [])
    if not fixes:
        return 0

    applied = 0
    for fix in fixes:
        file_path = PROJECT_ROOT / fix["file"]
        if not file_path.exists():
            print(f"  [WARN] File not found: {fix['file']} – skipped")
            continue

        original = fix["original"]
        replacement = fix["replacement"]
        content = file_path.read_text()

        if original not in content:
            print(f"  [WARN] Original snippet not found in {fix['file']} – skipped")
            print(f"         Looking for: {original[:80]!r}…")
            continue

        file_path.write_text(content.replace(original, replacement, 1))
        print(f"  [+] {fix['file']}: {fix['description']}")
        applied += 1

    return applied


# ---------------------------------------------------------------------------
# Step 5 – Create branch FIRST, then commit + push + open PR
# ---------------------------------------------------------------------------

def create_branch(timestamp: str) -> str | None:
    """
    Switch to a new auto-fix branch BEFORE any files are touched.
    Returns the branch name, or None on failure.
    """
    base = _base_branch()
    branch = f"auto-fix/test-failures-{timestamp}"
    r = _run(["git", "checkout", "-b", branch])
    if r.returncode != 0:
        print(f"[ERROR] Could not create branch: {r.stderr}")
        return None
    print(f"[+] Branch created: {branch}  (base branch '{base}' is untouched)")
    return branch


def _base_branch() -> str:
    """Return the branch the agent was triggered from (CI or local)."""
    return os.environ.get("BASE_BRANCH") or _run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    ).stdout.strip() or "main"


def commit_and_push_pr(branch: str, summary: str, timestamp: str, fix_plan: dict):
    """Commit fixes, push branch, open PR. Called after fixes are applied."""
    # Ensure there are changes
    status = _run(["git", "status", "--porcelain"])
    if not status.stdout.strip():
        print("[*] No changes to commit.")
        return None

    # Stage all changed files
    _run(["git", "add", "-A"])

    # Collect the actual diff for the terminal + PR body
    diff_output = _run(["git", "diff", "--staged"]).stdout

    # Commit
    commit_msg = (
        f"fix: auto-fix failing Playwright tests [{timestamp}]\n\n"
        f"{summary}\n\n"
        "Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
    )
    r = _run(["git", "commit", "-m", commit_msg])
    if r.returncode != 0:
        print(f"[ERROR] Commit failed: {r.stderr}")
        return None
    print("[+] Changes committed")

    # Push
    r = _run(["git", "push", "-u", "origin", branch])
    if r.returncode != 0:
        print(f"[ERROR] Push failed: {r.stderr}")
        return None
    print(f"[+] Branch pushed: {branch}")

    # Print changes summary to terminal
    fixes = fix_plan.get("fixes", [])
    print(f"\n{'─' * 60}")
    print(f"  CHANGES MADE  ({len(fixes)} fix(es))")
    print(f"{'─' * 60}")
    for fix in fixes:
        print(f"\n  File : {fix['file']}")
        print(f"  What : {fix['description']}")
        print(f"  Before: {fix['original'][:120].strip()!r}")
        print(f"  After : {fix['replacement'][:120].strip()!r}")
    print(f"\n{'─' * 60}\n")

    # Build PR body with per-fix before/after table
    fixes_section = ""
    for fix in fixes:
        fixes_section += (
            f"#### `{fix['file']}`\n"
            f"{fix['description']}\n\n"
            f"```diff\n"
            f"- {fix['original'].strip()}\n"
            f"+ {fix['replacement'].strip()}\n"
            f"```\n\n"
        )

    base = _base_branch()
    remote_url = _run(["git", "remote", "get-url", "origin"]).stdout.strip()
    repo_path = re.sub(r"(https://github\.com/|git@github\.com:)", "", remote_url).removesuffix(".git")
    compare_url = f"https://github.com/{repo_path}/compare/{base}...{branch}"

    body = (
        f"## Auto-Fix Agent — {timestamp}\n\n"
        f"**Branch:** `{branch}`  \n"
        f"**Base:** `{base}`  \n"
        f"**Compare:** {compare_url}\n\n"
        f"**Summary:** {summary}\n\n"
        f"---\n\n"
        f"### Changes made ({len(fixes)} fix(es))\n\n"
        f"{fixes_section}"
        f"---\n\n"
        f"### Review checklist\n"
        f"- [ ] Diff looks correct\n"
        f"- [ ] Tests pass in CI\n"
        f"- [ ] No unintended changes\n\n"
        f"---\n"
        f"🤖 Generated with [Claude Code](https://claude.ai/claude-code)  \n"
        f"Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
    )

    # Try gh CLI; fall back to a browser compare URL if it is not installed
    gh_path = subprocess.run(
        ["which", "gh"], capture_output=True, text=True
    ).stdout.strip()

    gh_error = ""
    if gh_path:
        try:
            r = subprocess.run(
                [gh_path, "pr", "create",
                 "--title", f"fix: auto-fix failing Playwright tests ({timestamp})",
                 "--body", body,
                 "--base", base],
                capture_output=True, text=True, cwd=PROJECT_ROOT,
            )
            if r.returncode == 0:
                return r.stdout.strip()
            gh_error = r.stderr.strip()[:80]
        except FileNotFoundError:
            gh_error = "gh binary not found"
    else:
        gh_error = "gh not installed"

    # Fallback: print a GitHub compare URL the user can open in their browser
    print(f"[WARN] gh CLI unavailable ({gh_error})")
    print(f"[*]  Open this URL to create the PR manually:")
    print(f"     {compare_url}?expand=1")
    return compare_url


# ---------------------------------------------------------------------------
# Failure report
# ---------------------------------------------------------------------------

REPORTS_DIR = PROJECT_ROOT / "failure_reports"


def save_failure_report(timestamp, failures, raw_output):
    """
    Write a human-readable failure report to failure_reports/<timestamp>.txt
    before any fixes are applied.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"{timestamp}.txt"

    lines = [
        "=" * 70,
        f"  AUTO-FIX AGENT  –  Failure Report",
        f"  Run: {timestamp}",
        "=" * 70,
        f"\nTotal failing tests: {len(failures)}\n",
    ]

    for i, f in enumerate(failures, 1):
        lines += [
            f"{'─' * 70}",
            f"[{i}] {f['file_path']}::{f['test_name']}",
            f"    Error : {f.get('error_summary', 'N/A')}",
        ]
        tb = f.get("traceback_block", "").strip()
        if tb:
            lines.append(f"\n    Traceback:\n")
            for tl in tb.splitlines():
                lines.append(f"      {tl}")
        lines.append("")

    lines += [
        "=" * 70,
        "  Full pytest output",
        "=" * 70,
        "",
        raw_output,
    ]

    report_path.write_text("\n".join(lines))
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    _banner("Auto-Fix Agent  –  Playwright Python")

    # ── 1. Run tests ────────────────────────────────────────────────────────
    print("\n[1/5] Running test suite…")
    passed, output = run_tests()

    if passed:
        print("[✓] All tests passed — nothing to fix.")
        return 0

    print("[!] Failures detected.")

    # ── 2. Parse failures & save report ─────────────────────────────────────
    print("\n[2/5] Parsing failures…")
    failures = parse_failures(output)

    if not failures:
        print("[WARN] Could not parse individual failures; sending raw output.")
        failures = [{"test_name": "unknown", "file_path": "unknown", "error_summary": "see output"}]

    report_path = save_failure_report(timestamp, failures, output)
    print(f"[*] Failure report saved → {report_path.relative_to(PROJECT_ROOT)}")

    print(f"\n{'─' * 60}")
    print(f"  {len(failures)} FAILING TEST(S)")
    print(f"{'─' * 60}")
    for f in failures:
        print(f"\n  ✗ {f['file_path']}::{f['test_name']}")
        print(f"    Error : {f.get('error_summary', '')}")
        tb = f.get("traceback_block", "").strip()
        if tb:
            # Print the last 8 lines of the traceback (most relevant)
            tb_lines = tb.splitlines()
            for tl in tb_lines[-8:]:
                print(f"           {tl}")
    print(f"\n{'─' * 60}\n")

    # ── 3. Get fixes from Claude ─────────────────────────────────────────────
    print("\n[3/5] Asking Claude for fixes…")
    fix_plan = ask_claude_for_fixes(failures, output)

    if fix_plan is None:
        print("[ERROR] Claude did not return a usable fix plan.")
        return 1

    print(f"[*] Claude says: {fix_plan.get('summary', '')}")

    # ── 4. Create branch BEFORE touching any files ───────────────────────────
    print("\n[4/6] Creating fix branch (before modifying any files)…")
    branch = create_branch(timestamp)
    if branch is None:
        return 1

    # ── 5. Apply fixes on the new branch ────────────────────────────────────
    print("\n[5/6] Applying fixes…")
    applied = apply_fixes(fix_plan)

    if applied == 0:
        print("[!] No fixes were applied (nothing changed).")
        _run(["git", "checkout", _base_branch()])
        _run(["git", "branch", "-D", branch])
        return 1

    print(f"[*] Applied {applied} fix(es). Re-running tests…")
    passed_after, output_after = run_tests()

    if passed_after:
        print("[✓] All tests pass after fixes!")
    else:
        still_failing = parse_failures(output_after)
        print(f"[WARN] {len(still_failing)} test(s) still failing after fixes:")
        for f in still_failing:
            print(f"       {f['file_path']}::{f['test_name']}")
        print("[*] Proceeding with PR anyway — manual review required.")

    # ── 6. Commit, push, open PR ─────────────────────────────────────────────
    print("\n[6/6] Committing and creating pull request…")
    pr_url = commit_and_push_pr(branch, fix_plan.get("summary", "auto-fix"), timestamp, fix_plan)

    if pr_url:
        _banner(
            f"Auto-fix complete!\n\n"
            f"  Branch : {branch}\n"
            f"  PR     : {pr_url}"
        )
        return 0
    else:
        print("\n[ERROR] PR creation failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
