# Lesson 04 — Virtual Environments (venv)

> Triggered by: Ship 0 final step (isolating this project's Python). Time to read: ~5 min.

## In one sentence

A **virtual environment** is a private, isolated copy of Python for one project — so libraries installed for *this* project don't conflict with libraries from other projects or with your system Python.

## A real-world analogy

Imagine cooking three different cuisines — Italian, Indian, Thai — in the same kitchen with only one set of pots. Every dish picks up flavor from the last one. Annoying for chai, ruinous for soup.

A virtual environment is like giving each cuisine its own set of pots and a clean counter. When you cook Italian, you use Italian pots; when you cook Indian, the Indian pots. The kitchen (your computer) stays sane and each dish tastes like itself.

In Python: when you `pip install some-library` outside a venv, it installs **globally** — for every Python project AND for system tools that use Python. Different projects need different versions of the same library (one needs `requests 2.30`, another needs `requests 1.8`). Without isolation, you get conflicts.

## Where this shows up in our project

- Before we install our first dependency (Anthropic SDK, FastAPI, etc. in later ships), we activate this project's venv
- After installing, when you `python3 tracker.py` while the venv is active, it uses **this project's** libraries — not system ones
- Anyone who clones our repo creates their own venv, installs from `requirements.txt`, runs the code. Reproducible setup.

## The minimum you need to know

### Creating the venv (once per project)
```
python3 -m venv .venv
```
- `python3 -m venv` runs Python's built-in `venv` module
- `.venv` is the folder name (convention)
- This creates a `.venv/` folder with its own copy of Python and `pip`

### Activating the venv (once per terminal session)
```
source .venv/bin/activate
```
After this, your prompt changes to show `(.venv)` at the start — your signal that you're inside.

Now `python3` and `pip` point to the venv's copies. Install a package → it lands inside `.venv/`, not your system.

### Deactivating
```
deactivate
```
Returns you to system Python.

### The `.venv/` folder is gitignored
Never commit `.venv/`. It's large, machine-specific, and rebuildable from `requirements.txt`. Other devs (or future-you on a new machine) create their own.

(Already in our `.gitignore`.)

### `requirements.txt`

A plain text file listing dependencies, one per line, optionally version-pinned:
```
anthropic==0.8.0
fastapi==0.110.0
```
- Generate from current venv: `pip freeze > requirements.txt`
- Install from it on a new machine: `pip install -r requirements.txt`

We have **zero dependencies right now**, so this file doesn't exist yet. We'll create it the moment we install our first package (Ship 5, the Anthropic SDK).

## A worked example — the workflow

```
# 1. Create the venv (one-time, from project root)
cd /Users/ajinkya/Desktop/Ajinkya\ Kate/job-tracker
python3 -m venv .venv

# 2. Activate it (every new terminal session)
source .venv/bin/activate
# Prompt becomes: (.venv) ajinkya@... %

# 3. Verify you're in the venv
which python3
# → .../job-tracker/.venv/bin/python3   (NOT /usr/bin/python3)

# 4. Run your code as usual
python3 tracker.py
# → Job Tracker — Ship 0. The toolchain works.

# 5. When done for the day
deactivate
```

**You don't need a venv for the one-line hello-world we have now** — it works fine on system Python. But the moment we install our first library (Ship 5), the venv is non-negotiable. So we set it up *now* and use it from this point forward to build the habit.

## Check yourself

- Why don't we install packages globally (without a venv)?
- What does activating a venv actually change about your terminal?
- If you clone a Python project to a new machine, what's typically the first thing you do?
- Why is `.venv/` in `.gitignore`?

## Interview-ready 60-second answer

*"A virtual environment is per-project Python isolation. It prevents library version conflicts across projects and keeps system Python clean. Standard tool is `venv`, built into Python 3. Workflow: `python3 -m venv .venv`, then `source .venv/bin/activate`, then `pip install` your dependencies. You pin versions in a `requirements.txt` so others can reproduce your environment. Production deployments typically do the same — install from `requirements.txt` into a fresh environment."*

## Open threads

- **`pip`** — Python's package installer; used constantly inside venvs
- **`requirements.txt` and pinning** — comes up Ship 5 when we install Anthropic
- **Alternatives**: `poetry`, `uv`, `pipenv` — fancier tools; `venv` is the right starting point
- **`pyenv`** — for managing multiple Python versions (e.g., 3.9 alongside 3.12); defer until needed
