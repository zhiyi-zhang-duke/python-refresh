---
name: python-drill
description: Rapid-fire Python recall drill for Jack's python-refresh repo, run in chat. Claude shows one card at a time (a task plus given inputs), Jack types only the key line(s), the card's own check grades them for real (on glados through the funemployed-hq MCP server, so no local repo is needed), and Knew/Shaky/Missed is logged to Funemployed HQ so the next session starts with what he missed. Use whenever Jack says "/python-drill", "quiz me on python", "drill me", "python flashcards", "let's do some python reps", "review my python", or names a python-refresh topic to drill ("drill me on dicts"). Prefer this over having him solve whole exercises when he wants speed or volume. For syncing solved exercises (not a drill), use funemployed-mcp instead.
---

# python-drill

Fast recall reps over the 175 cards in `python-refresh`, one card per exercise.
Writing whole functions is slow. The thing that actually costs Jack time in
interviews is recalling idioms (`split(maxsplit=)`, `entry[0](args)`, `global`,
`except (EOFError, KeyboardInterrupt)`). Each card is the 1–5 lines that carry an
exercise, graded by running them, at roughly 30–60 seconds a card.

The source of truth for this file is the repo's `.claude/skills/python-drill/SKILL.md`.
Copies live in `~/.claude/skills/python-drill/` on Jarvis and on glados.

## Where things run

- **Everything goes through the `funemployed-hq` MCP server on glados.** It keeps
  its own clone of the repo (`~/python-refresh`, pulled from GitHub every 5
  minutes), grades answers there in a sandboxed subprocess, and stores the
  grades. Any session that can reach it works: Jarvis, a laptop on the tailnet,
  or a Remote Control session on glados driven from Jack's phone.
- Tools: `next_python_cards`, `check_python_card`, `python_card_answer`,
  `show_python_card`, `log_python_drill`. If they're deferred, load them with
  ToolSearch `+funemployed python`.
- **If the server isn't reachable** (a cloud container, or off the tailnet) but
  the repo is checked out, fall back to local grading:
  `python drill.py show|check|answer <id>` (check reads his lines on stdin). Say
  up front that grades can't be logged from here, and list them at the end
  as `<id> K/S/M` lines, so a later session can pass them to `log_python_drill`.

## Rhythm

Speed is the point. Keep every message short, and never lecture between cards.
On a phone, a short message is the whole experience.

1. **Pick cards:** `next_python_cards(n=10, topic=<if he named one>)`. Due reviews
   come first (Missed, then Shaky, then Knew), then new cards in suggested order.
   Each card comes with its `prompt` and `given`. Note the start time.
2. **Show a card:**

   > **01_strings.ex04** · easy
   > Split `line` into `cmd`, `model`, `prompt`. The prompt keeps its inner spacing exactly…
   > ```python
   > line = '  run phi3:mini tell me  a joke'
   > ```

   No hints, no `why`, no tool names beyond what the prompt says.
3. **Grade his reply** with `check_python_card(id, code=<his lines exactly as typed>)`.
   - **`pass` on the first try = Knew.** Reply `✓` plus the returned `why` in one
     line, then show the next card **in the same message**.
   - **Fail:** give the `result` in one line plus a nudge that doesn't give the
     answer away ("the prompt lost its double space, look at how the split
     counts"). He gets one retry. A pass on the retry = **Shaky**.
   - **Second fail, or "idk" / "skip" / "?" = Missed.** Show `python_card_answer`
     (answer and why), then move on.
   - A failure that's only a typo or a wrong variable name, not the idiom, counts
     as Shaky once he fixes it. Never mark Knew on your own judgment when the
     check failed. The check is the grade.
   - If he answers in words rather than code, ask for the line. That recall is
     what the drill trains. Phone keyboards mangle quotes and indentation; if a
     failure is obviously smart quotes (“ ”) or lost indentation, fix those
     characters only, re-run the check, and say so.
4. **Every 10 cards, or when he stops,** log the batch:
   `log_python_drill(results="<id> K\n<id> S\n<id> M…", minutes=<elapsed>, notes=<pattern>)`.
   `notes` is one line on a pattern you saw ("kept writing split(' ') for
   split()"), or empty. Log before showing anything else, so a dropped session
   loses at most one batch.
5. **After logging,** re-ask the batch's Missed cards once, quickly and without a
   grade (the log already has them), then report in one line: "8 knew, 1 shaky,
   1 missed · 3 due tomorrow · next up: dicts." Offer another 10. If he wants it,
   call `next_python_cards` again with `exclude` = every id already asked this
   session.

## Rules

- One card per message. Never show the answer before he's tried, unless he asks.
- Don't skip the check because his answer looks right. Run it. "Status comes
  from the tests" is the whole design.
- Missed cards come back the same day by design. If he asks "why again?", that's
  the reason.
- If a card id doesn't exist or the server can't reach GitHub, say so. Don't
  invent cards.
- To work on solved-exercise status (the Passing column), use the funemployed-mcp
  skill's `sync_python_progress` flow instead. The two tracks are separate.
