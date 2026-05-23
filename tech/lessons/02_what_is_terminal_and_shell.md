# Lesson 02 — The Terminal

> Triggered by: running `python3 tracker.py`. Time to read: ~3 min. This one's a quick reference, not a deep dive.

## In one sentence
The **terminal** is a text-based way to talk to your computer — you type a command, hit Enter, the computer does it and shows the result.

## A real-world analogy
GUI (windows, icons, mouse) is like ordering at a restaurant by pointing at pictures on the menu. The terminal is like writing your order on a slip: more typing, but you can ask for exactly what you want — including things the picture menu doesn't have.

For day-to-day file management the GUI is fine. For software development the terminal is faster and gives you exact control.

## Where this shows up in our project
Every Python command (`python3 tracker.py`), every git command (coming next), every install (`pip install ...`) — all typed in the terminal. The bottom panel of Cursor *is* a terminal.

## The minimum you need to know

**The prompt** is the line waiting for your input. Yours looks like:
```
ajinkya@Ajinkyas-MacBook-Air job-tracker %
```
Read right-to-left: `%` = "I'm waiting." `job-tracker` = the folder you're currently in. The rest is your user + machine name.

**Five commands worth knowing on day 1:**

| Command | What it does | Example |
|---|---|---|
| `pwd` | print working directory — what folder am I in? | `pwd` |
| `ls` | list — show files/folders in current location | `ls` |
| `cd <folder>` | change directory — move into a folder | `cd job-tracker` |
| `cd ..` | move UP one folder | `cd ..` |
| `python3 <file>` | run a Python file | `python3 tracker.py` |

**Two keyboard tricks worth 100× their weight:**

- **Tab to autocomplete.** Type `python3 tra` then press Tab → it fills in `tracker.py`. Saves typing and prevents typos.
- **Up arrow to repeat.** Pressing ↑ pulls up your previous commands. Saves re-typing the same thing.

## A worked example — what you already did

```
ajinkya@Ajinkyas-MacBook-Air job-tracker % python3 tracker.py
Job Tracker — Ship 0. The toolchain works.
ajinkya@Ajinkyas-MacBook-Air job-tracker %
```

- Line 1: the prompt + your command.
- Line 2: Python's output.
- Line 3: prompt comes back, ready for the next command.

## Check yourself

- What does `%` at the end of the prompt mean?
- If you wanted to see what files are in your current folder, what would you type?
- What keyboard shortcut fills in a long filename without typing it all?

## Interview-ready 60-second answer

*"The terminal is a text-based interface for running commands. In dev work it's often faster than a GUI because you can chain commands, script them, and access tools that don't have a UI. The fundamentals are navigating with `cd` / `ls` / `pwd`, running programs by typing their name, and piping output between commands. Most senior engineers do 80% of their work in the terminal."*

## Open threads

- **Shell vs terminal vs prompt** — subtly different things; treat them as one for now. (zsh is your specific shell; comes default on Mac.)
- **Piping & redirection** (`|`, `>`, `>>`) — combine commands; learn when we automate stuff
- **Aliases & dotfiles** — power-user customization; defer
