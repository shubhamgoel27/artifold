# Artifold

[![PyPI](https://img.shields.io/pypi/v/artifold?color=c1452a&label=pypi&style=flat-square)](https://pypi.org/project/artifold/)
[![Python](https://img.shields.io/pypi/pyversions/artifold?style=flat-square&color=666)](https://pypi.org/project/artifold/)
[![License](https://img.shields.io/badge/license-MIT-666?style=flat-square)](LICENSE)

**Decks, reports and pages from AI that look designed, not generated.
And one library that keeps every one of them.**

Artifold has two parts that work together:

- **`craft`**, a skill for Claude Code and Codex. Ask it for slides, a
  report, a tracker or an explainer, and it works like a designer would:
  it edits the content first, then picks a layout, type and voice for
  that subject. No purple gradients, no rows of identical cards.
- **The library**, which finds every HTML page on your disk, keeps its
  history, and makes it easy to find again and share.

Pages made with it have been passed around and praised by a designer at
Figma, engineers at OpenAI and Meta, and a data engineer at DoorDash.

![Same prompt, plain Claude vs /craft](docs/gallery/composite-2x2.jpg)
<sub>Same prompt, same model. Left: plain Claude. Right: with `craft`. See
all eleven in the [gallery](https://shubhamgoel27.github.io/artifold/).</sub>

## Why this exists

I made a 30-day workout tracker for my partner with Claude. A few weeks
later I couldn't find it. It was somewhere in a pile of project folders
and downloads, so I asked for it again and got a worse one.

Two problems there. The pages were easy to lose, and the second try came
out generic: the same purple gradient and the same row of cards as
everything else. Thariq on the Claude Code team described the first one:

> *"I've started preferring HTML as an output format instead of Markdown.
> The added expressiveness means I get overall better output, and the chance
> of someone actually reading your spec, report or PR writeup is much higher
> if it's in HTML. … When writing this article, I asked Claude Code to read
> through my code folder and find all the HTML files I've generated, group
> and categorize them …"*
>
> Thariq, *[The Unreasonable Effectiveness of HTML](https://x.com/trq212/status/2052809885763747935)*

`craft` fixes the second problem, and the library fixes the first. Each
one makes the other better: `craft` reads your library so a new page
doesn't repeat your last few, and every page it makes lands in the
library already described and searchable.

## Making pages: `craft`

Type `/craft a 30-day strength tracker for a beginner` in Claude Code, or
`$craft ...` in Codex, and it:

- decides how much design the job needs, so a daily checklist stays quiet
  and a deck, a gift or a public page gets the full treatment
- edits the content before styling it: what the reader should remember,
  what to cut, and what belongs in a table or chart instead of prose
- picks a layout, a visual style, a tone of voice and one hand-built detail
  for this subject, and reads your library first so the new page doesn't
  repeat your last few
- avoids a long list of named AI-design habits (the purple gradient hero,
  identical cards, emoji bullets)
- renders the page in a headless browser and fixes what it finds
- saves it to `~/artifold-inbox/`, where it shows up in the library within
  seconds

You can also point it at something you made before: `/craft a poker odds
explainer, like dobble` starts from that page's actual CSS.

![The SF coffee tier list, plain Claude vs craft](docs/gallery/composite-pair-coffee.jpg)

## Keeping pages: the library

### Finds everything

Point it at a few folders and it indexes every HTML file in them. Each
artifact gets a screenshot thumbnail, a category, and a one-line
description of what it is for, so two similar cheat sheets are easy to
tell apart at a glance. Search covers titles, headings, opening text,
prompts and intents. `⌘K` jumps to anything.

It leaves out what isn't yours: `node_modules`, build output, cloned git
repos, server templates, and anything nested too deep.

![Artifold demo](docs/demo.gif)

### Keeps the history

Files named `report-v2.html` or `report (1).html`, or dated copies of the
same page, collapse into one card with a version picker and a diff view.
Pages you edit in place keep a revision history too, and a card shows
how many times you have revised or opened it. "Most used" sorts by that,
so the trackers you open every day stay near the top instead of sinking
under last week's one-offs.

![Command palette](docs/cmdk.png)

### Shares in one click

Click share on any card and, usually within a minute, you get a permanent link
like `https://you.github.io/artifold-share/abc12345.html`, copied to your
clipboard. It publishes to your own GitHub Pages: free, no expiry, and
the person you send it to needs nothing installed. You can also export
any artifact to PDF.

![Share flow in detail pane](docs/share-detail.png)

### Works with other design skills too

The library indexes any HTML, whatever wrote it: Claude, ChatGPT Canvas,
v0, Cursor, or another design skill. What differs is how much it can
learn about each page.

| Made with | Artifold knows |
|---|---|
| **`craft`** | everything: intent, the layout and style chosen, and the history of those choices |
| **[Hallmark](https://github.com/Nutlope/hallmark)** | layout, theme and brief, read from Hallmark's own stamp and log |
| **[taste-skill](https://github.com/Leonxlnx/taste-skill)**, **[huashu-design](https://github.com/alchaincyf/huashu-design)**, anything else | palette, fonts, design tokens, page structure, thumbnail, full-text search |

The last row needs nothing from the page and covers most of what the
library does. The first two rows exist because a page can say what it is
in a few lines of `<head>`. If you build a design skill, that format is
documented in [docs/ARTIFACT-METADATA.md](docs/ARTIFACT-METADATA.md), and
nothing in it is specific to Artifold. Skills with their own format are
read through [adapters](artifold/adapters.py); pull requests for new ones
are welcome.

Run `artifold skills` to see which of these you have installed.

### Stays out of the way

A running `artifold serve` uses about 30 MB of memory and no CPU while
nothing changes. When a file changes, a rescan takes well under a second,
because unchanged files are recognized from their size and modification
time and never reread. While you are iterating on a page, its thumbnail
waits until you stop editing, so a burst of saves launches the headless
browser once instead of once per save.

## Install

### Everything: let your agent do it

Paste this into Claude Code or Codex:

> [!TIP]
> ```
> Install Artifold from https://github.com/shubhamgoel27/artifold using pipx
> (or pip if pipx isn't installed). Then run `artifold install-skill` to set
> up the craft skill, and `artifold init` to pick a folder to watch. Open
> the dashboard when ready and tell me what to try first.
> ```

### Just the skill

If you only want better-looking pages and no library, paste this instead:

> [!TIP]
> ```
> Install only the craft skill from https://github.com/shubhamgoel27/artifold.
> Copy the folder artifold/skills/craft (SKILL.md and references/) into
> ~/.claude/skills/craft for Claude Code, or ~/.agents/skills/craft for
> Codex. Don't install the Python package. Then tell me how to use it.
> ```

Or run it yourself. For Codex, change `~/.claude/skills` to
`~/.agents/skills`:

```bash
mkdir -p ~/.claude/skills && curl -sL https://github.com/shubhamgoel27/artifold/archive/main.tar.gz \
  | tar -xz -C ~/.claude/skills --strip-components=3 artifold-main/artifold/skills/craft
```

The skill works without the library. It just can't look at your past
pages, so it has less to go on when it avoids repeating itself. You can
add the library later and nothing changes.

### Everything, by hand

```bash
pipx install artifold        # or: pip install artifold
artifold init                # pick folders to watch, install craft
artifold                     # scan, then open the dashboard
```

No `pipx`? `brew install pipx` on a Mac, or `python -m pip install --user
pipx` anywhere. `init` installs `craft` for every agent it finds
(`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex);
restart your agent once afterwards so it picks up the skill.

The first scan downloads a headless Chromium (about 170 MB) for
thumbnails. After that only new or changed pages are captured.

## Commands

```bash
artifold                     # serve the dashboard and open it
artifold init                # setup wizard
artifold add <dir>           # watch another folder
artifold remove <dir>        # stop watching one
artifold roots               # list watched folders
artifold allow-repo <name>   # include a folder that is its own git repo
artifold scan                # rescan and rebuild the dashboard
artifold serve --no-open     # dashboard with live rescans, no browser tab
artifold open                # open the dashboard
artifold search <words>      # search from the terminal
artifold doctor              # check the setup and say what to fix

artifold share <file>        # publish to your GitHub Pages
artifold share --list        # everything you have shared
artifold share --revoke <id> # take a share down
artifold share --reconcile   # rebuild share records from what is published
artifold export-pdf <file>   # render an artifact to PDF
artifold trash <file>        # move an artifact to the system Trash

artifold import <url>        # save a public share (Claude, ChatGPT, v0, Lovable, …)
artifold link <file> --tool claude --source URL --prompt "..."
artifold info <file>         # show what Artifold knows about a file

artifold designs             # list design fingerprints
artifold designs <id> --template   # a page's CSS and structure, to reuse
artifold skills              # design skills, and what Artifold reads from each
artifold install-skill       # install craft for Claude Code and/or Codex
artifold inbox [topic]       # the path where a new artifact should go
artifold config [key] [value]  # read or change a setting
```

## Settings

`artifold config` lists them; `artifold config <key> <value>` changes one.
The file lives at `~/Library/Application Support/artifold/config.json` on
macOS and `~/.config/artifold/config.json` on Linux:

```jsonc
{
  "roots": ["/Users/me/Downloads", "/Users/me/work"],
  "allow_repos": [],        // folders with their own .git to include anyway
  "max_depth": 3,           // how deep to look inside each watched folder
  "enable_intent": false,   // optional AI descriptions, see below
  "categories": {           // add your own category keywords
    "Research": ["paper", "experiment", "ablation"]
  }
}
```

Thumbnails, the dashboard and the browser live in
`~/Library/Caches/artifold/`. Deleting that folder is safe; the next scan
rebuilds it from your files.

## Keyboard

| Key | Does |
|---|---|
| `⌘K` / `Ctrl+K` | open the palette: search artifacts and run actions |
| `/` | focus the search box |
| `↑` `↓` then `↵` | pick a result in the palette |
| `Esc` | close the palette or the preview |

## Optional: AI descriptions

Artifold works without any AI or network access. Pages made with `craft`
or Hallmark already describe themselves. For everything else, you can have
Claude Haiku write a one-line description of each artifact:

```bash
pipx install 'artifold[intent]'
export ANTHROPIC_API_KEY=sk-ant-...
artifold scan --intent
```

Each artifact costs at most about a third of a cent, and runs once: the
result is stored by content, so later scans reuse it until the page changes.

## What leaves your machine

Artifold has no server and no account, and the CLI holds no credentials
for anything. Your library is the folders you pointed it at.

The only thing that sends an artifact anywhere is `artifold share`, which
publishes the one artifact you pick to your own GitHub Pages.

## What it isn't

- **A replacement for git or your folders.** It reads what is already
  there and moves nothing.
- **Locked to `craft` or to one agent.** Hallmark, taste-skill and huashu-design are all
  good, and the library keeps their output findable too.
- **Tied to one folder.** Watch `~/Downloads`, `~/Documents` and a project
  folder at once.

## Status

Version 0.14, alpha. I use it every day on macOS; Linux should work;
Windows is untested. There are 178 tests and CI on Python 3.10 to 3.13.
It is a one-person project, so I build what I need first, but issues and
pull requests are welcome. If something is confusing, [open an
issue](../../issues/new); one line is enough.

## Roadmap

- [ ] A layout that works well on a phone
- [ ] `artifold adopt <file>` to move existing files into the inbox
- [ ] Cloudflare Pages as a sharing option for people without the `gh` CLI
- [ ] First-class Markdown files
- [ ] Search by meaning, for when you remember the gist but not the title

## Made by

[@shubhamgoel27](https://github.com/shubhamgoel27), because I needed it.
If it's useful to you, a star helps other people find it. If you make
something good with `craft`, I'd like to see it.

## License

MIT
