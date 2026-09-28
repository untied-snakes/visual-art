# visual-art

Live, audio-reactive visuals for shows, plus MP4 export for projectors.
See [PLAN.md](PLAN.md) for how it's put together.

## Setup

```bash
uv sync
```

## Adding a visual

Every visual is one file in `src/visual_art/visuals/`. Drop a new file in and it
joins the shuffle automatically.

1. `cp src/visual_art/visuals/_template.py src/visual_art/visuals/my_thing.py`
2. Rename the class inside, e.g. `TemplateVisual` → `MyThingVisual`.
3. Try it: `uv run visual-art play my_thing`
4. Open a pull request that adds just that one file.

Rules (details in PLAN.md):

- Set up in `__init__`, change state in `update`, paint in `draw`.
- Multiply all movement by `dt`.
- Fill the whole background at the start of `draw`.
- One `Visual` class per file; the file name is the visual's name.
- Files starting with `_` are ignored.

## At the venue

Plug the laptop into the projector (HDMI or USB-C adapter), then:

```bash
uv run visual-art displays      # the projector is usually 1
uv run visual-art devices       # find your mic or audio interface
uv run visual-art shuffle --display 1 --device "USB Audio" --seconds 45 --fade 4
```

It opens fullscreen on the projector. Space skips a visual, F toggles
fullscreen, and Q or Esc quits. If the room is loud or quiet, restart with `--gain`
(for example `--gain 0.5` or `--gain 2`).

Backup plan: render the set to MP4 ahead of time (`visual-art render`) and bring
it on a USB stick formatted exFAT.
