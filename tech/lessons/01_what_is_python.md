# Lesson 01 — What is Python?

> Triggered by: Ship 0 (first hello-world). Time to read: ~5 min.

## In one sentence

**Python is a programming language** — a way to write instructions a computer can run, using text that reads almost like English.

## A real-world analogy

Think of human languages: English, Hindi, French, Spanish. They're all ways to communicate ideas, just with different vocabulary and grammar.

Programming languages are the same idea — but for talking to computers. Python is one of those languages. Others you may have heard of: JavaScript, Java, C++, Go, Rust.

The thing that makes **Python special**: it's designed to read close to plain English. Compare:

In some languages, "print hello" looks like:
```c
#include <stdio.h>
int main() { printf("hello\n"); return 0; }
```

In Python:
```python
print("hello")
```

That's it. One line. This is why Python is the most popular first language for beginners and the most common language for AI/ML work — you spend more time thinking about the problem and less time fighting the language.

## Where this shows up in our project

**Every line of the job tracker is written in Python.**

When we run `python3 tracker.py` in the terminal, here's what happens:
1. The `python3` program (already on your Mac) opens
2. It reads the file `tracker.py` line by line
3. For each line, it does whatever that line says ("print this," "save that," "ask Claude this")
4. When the file ends, the program exits

That's it. There's no magic. Your job is to write the right lines in `tracker.py`.

## The minimum you need to know right now

1. **Python 3 is the version we care about.** "Python 2" is an old version that's dead and gone. When tutorials say "Python," they almost always mean Python 3 today. Your Mac has `python3` built in.
2. **Python is "interpreted."** You write text in a `.py` file. The `python3` command reads and runs it. No "compile" step like some languages. This is why iteration is fast — change a line, run it, see the result.
3. **The `.py` extension** marks Python files. The convention. Like `.docx` for Word.
4. **`pip` is how you install other people's Python code** (called "libraries" or "packages"). You'll use it later in this project to install the Anthropic SDK, FastAPI, etc.
5. **Indentation matters.** In most languages, you wrap blocks of code in `{ ... }`. In Python, you indent. Same indentation = same block. We'll see this when we write our first `if` or `for`.

## A worked example — the tracker.py we just made

Open `/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker/tracker.py`:

```python
print("Job Tracker — Ship 0. The toolchain works.")
```

One line. Let's read it together:
- `print(...)` is a **built-in function** in Python. "Function" = a small named operation. `print` writes text to your terminal.
- `"Job Tracker — Ship 0. The toolchain works."` is a **string** — Python's word for "a piece of text." Strings are wrapped in `"..."` or `'...'`.
- The whole line says: *"Take this string and print it."*

When you run `python3 tracker.py`, the terminal shows:
```
Job Tracker — Ship 0. The toolchain works.
```

That's the entire program. Trivial, but it proves: Python is on your Mac, the file is readable, the command works. From here, every feature is just more lines of Python — slightly longer, slightly fancier, but the same pattern.

## Check yourself

Without looking back, can you answer:

1. What does the `.py` at the end of a filename mean?
2. What's the difference between writing `tracker.py` (as a file) and running `python3 tracker.py` (in the terminal)?
3. If you had to choose between Python and JavaScript for this project, what's at least one reason Python makes sense for us specifically?

If any of these are fuzzy — re-read. If they're clear, you're ready to move on.

## Interview-ready 60-second answer

*"Python is a dynamically-typed, interpreted programming language known for its readable syntax and strong ecosystem. It's the dominant choice for AI/ML and a popular pick for web backends and scripting. Its main strengths are speed of development and library availability — especially anything touching data or machine learning. The trade-off is runtime performance: Python is slower than compiled languages like Go or Rust, so for hot paths you'd reach for something else, but for application code it's plenty fast. I picked Python for this project because it gets me to a working LLM-powered prototype faster than any other language."*

## Open threads (concepts this opens up — we'll cover them when we hit them)

- **Virtual environments** (`venv`) — why Python projects should isolate their dependencies (Lesson 04+)
- **`pip` and packages** — how to install other people's Python code (Lesson 04+)
- **Variables, types, lists, dicts, functions** — the core Python you actually write (Lesson 04, Ship 1)
- **Type hints** — Python's optional way to declare what kind of data is expected
- **Python versions** — yours is 3.9; current is 3.12. We may upgrade when we hit a feature we want
