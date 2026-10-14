# Media

Drop pictures or videos into a visual's folder and that visual shows them.
An empty folder means the visual looks the way it always has.

| Folder    | What the pictures become |
|-----------|---------------------------|
| `pulse/`  | a picture inside the sun |
| `dunes/`  | mirages rising between the ridges, drifting with them (up to 4 files at once) |
| `canyon/` | texture pressed into the rock walls |
| `scales/` | a mosaic of the picture, lit up by the music |
| `vision/` | a turning kaleidoscope behind the mandala |
| `cosmos/` | a dim nebula behind the galaxy, slowly drifting |

- Pictures: `.jpg .jpeg .png .bmp .gif .webp .tga`. Videos: `.mp4 .mov .m4v .webm .mkv .avi` (they loop, at half speed).
- Several files in one folder take turns, crossfading every 30 seconds, in file-name order.
  Number them (`01-mesa.jpg`, `02-snake.mp4`) to control the order.
- Everything is recoloured to the show's dusk palette, so any photo fits in.
  Contrast matters more than colour: photos with strong lights and darks look best.
- Any size works; they're cropped to fill. Short, small videos (720p or 1080p, under a
  minute) use the least battery.
- Nothing in these folders is committed to git (see `.gitignore`); share files some other way.
- `uv run visual-art list` shows how many files each folder has.
