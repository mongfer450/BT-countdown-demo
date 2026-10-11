# Village Life — pixel art

A 10-second pixel-art video (1920×1080, 24fps, chiptune soundtrack) of a medieval
village, seen from a top-down 3/4 camera that slowly pans across the workyard.
Five peasants go about their day:

1. **Farmer** hoeing the crop field
2. **Woodcutter** chopping logs at the block
3. **Blacksmith** hammering at the anvil, sparks flying
4. **Maiden** carrying a bucket of water along the path
5. **Child** chasing a chicken around the big tree

Everything is drawn in code: the world is 640×330 pixels, the camera shows 480×270,
and each frame is scaled up 4× with nearest-neighbour.

## Rebuild

Needs Python 3 with Pillow and NumPy, plus ffmpeg.

```sh
python3 render.py frames
python3 music.py music.wav
ffmpeg -framerate 24 -i frames/f%04d.png -i music.wav -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -tune animation -c:a aac -shortest pixel_village.mp4
```
