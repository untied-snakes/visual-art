# visual-art

Live, audio-reactive visuals for shows, plus MP4 export for projectors.
See [PLAN.md](PLAN.md) for how it's put together.

## Setup

```bash
uv sync
```

## Colours

Every visual takes its colours from `src/visual_art/palette.py`: a dusk-in-the-desert
palette (night, indigo, dusk, mauve, rust, clay, ochre, sand, sage, turquoise, bone).
Use it in new visuals so the whole set feels like one place.

## Pictures and videos

Six visuals can show your own pictures or videos: drop files into
`media/<visual name>/` (for example `media/vision/`). See [media/README.md](media/README.md)
for what each one does with them. Empty folders leave the visuals as they are.

To use media in a new visual, see how `visuals/dunes.py` does it: make a
`Media("my_thing", size)` in `__init__`, call `self.media.update(dt)` in `update`,
draw `self.media.frame()` (None until something loads) in `draw`, and call
`self.media.close()` in `close`.

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
uv run visual-art set --display 1 --device "USB Audio"
```

`set` plays one visual per song, in the order in [setlist.txt](setlist.txt), and
only moves on when you tell it to (with a 3-second crossfade; change it with `--fade`).

| To...            | In the window                       | In the terminal |
|------------------|-------------------------------------|-----------------|
| Next song        | Space, →, ↓, Page Down, N, Enter    | Enter (or `n`)  |
| Previous song    | ←, ↑, Page Up, Backspace            | `b`             |
| Jump to song 1-10| 1-9, 0                              | the number      |
| Quit             | Q or Esc                            | `q`             |

The terminal prints which song and visual is up after every change. Bluetooth
foot pedals and page-turner remotes send arrow or Page Up/Down keys, so they
work as long as the visuals window has focus.

`uv run visual-art shuffle --display 1 --seconds 45 --fade 4` rotates through
every visual on a timer instead. Space skips, F toggles fullscreen, and Q or Esc quits. If the room is loud or quiet, restart with `--gain`
(for example `--gain 0.5` or `--gain 2`).

Backup plan: render the set to MP4 ahead of time (`visual-art render`) and bring
it on a USB stick formatted exFAT.
