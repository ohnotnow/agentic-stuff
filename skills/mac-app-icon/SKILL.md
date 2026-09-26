---
name: mac-app-icon
description: Turn one square PNG into a proper macOS app icon - artwork on a rounded square that matches Apple's icon grid, so macOS 26 and later show it as it is instead of shrinking it into a grey plate, plus the ten sizes and Contents.json of an Xcode AppIcon.appiconset. Use when the user wants an app icon, hands you artwork for their app, says their app shows a blank or generic icon, or says their icon looks framed, boxed or "a bit strange" in Finder or the Dock. Ships a tested script; needs ImageMagick.
---

# Mac app icon

The user has a picture and wants it to be their app's icon. It is a humdrum job with one trap, and the script next to this file already does it: `make-mac-icon.sh`.

## The trap

Since macOS 26, an icon that is not Apple's rounded-square shape gets shrunk and shown inside a grey rounded square. Artwork with a transparent background and its own outline (a folder, a character, a logo on nothing) looks framed and slightly odd. Seen on macOS 27 with Streamer: the transparent artwork came out on a grey plate.

The fix is to give the artwork its own rounded-square background on Apple's grid: an 824-point square inset 100 in a 1024 canvas, corner radius about 185. macOS then shows the icon as drawn. Streamer's navy version came out with no grey frame.

Icon Composer, Apple's tool for the new layered icon format, would not open a plain PNG for the user, so don't send them there as the easy route.

## Workflow

1. **Check the artwork.** `sips -g pixelWidth -g pixelHeight -g hasAlpha FILE.png`. It should be square and at least 1024 pixels. Look at it (Read the file) so you can suggest a background that suits its colours.

2. **Show the user choices before touching the project.** Make two or three versions in the scratchpad with different backgrounds and put them side by side:

   ```sh
   SCRIPT=<this skill's directory>/make-mac-icon.sh
   $SCRIPT art.png "$SCRATCH/dark"                          # default: navy #232a66 to #0b0d2a
   $SCRIPT art.png "$SCRATCH/light" '#ffffff' '#e6e9f5'
   magick \( -size 1100x560 xc:'#2b2b2b' \) \
       \( "$SCRATCH/dark/icon-1024.png" -resize 480x480 \) -geometry +40+40 -composite \
       \( "$SCRATCH/light/icon-1024.png" -resize 480x480 \) -geometry +580+40 -composite \
       "$SCRATCH/compare.png"
   ```

   Read `compare.png` yourself, then give the user its full path and your recommendation. Bright, saturated artwork usually glows on a dark background. A near-white one can read as Apple's grey frame. The background is a vertical gradient from the first colour (top) to the second (bottom).

3. **Generate into the project.** For an Xcode or XcodeGen app, point the script at the asset catalogue:

   ```sh
   $SCRIPT art.png Sources/<App>/Assets.xcassets [TOP BOTTOM]
   ```

   That writes `Assets.xcassets/AppIcon.appiconset/` (ten PNGs, 16 to 512 at 1x and 2x, and `Contents.json`) and `Assets.xcassets/icon-1024.png`. Move or delete `icon-1024.png` so it does not sit loose in the catalogue. It is the right file for a README image.

   If `Assets.xcassets/Contents.json` does not exist, create it:

   ```json
   {
     "info" : { "author" : "xcode", "version" : 1 }
   }
   ```

4. **Tell the build about it.** With XcodeGen, add to the app target's settings in `project.yml`:

   ```yaml
   ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon
   ```

   The asset catalogue only needs to be under the target's sources. After building, `AppIcon.icns` and `Assets.car` should be in `Contents/Resources`, and `CFBundleIconName` should be `AppIcon` in the built `Info.plist`.

5. **Have the user look.** The icon only matters in Finder and the Dock, and you can't see those. Ask the user to install or open the app and check it. Finder can hold on to an old icon for a while; relaunching Finder usually clears it.

6. **Keep the source.** Commit the original artwork (Streamer uses `icon-source.png`) and, if the project has a Makefile, add an `icon` target that reruns the script, so the next change is one command. A 256-pixel copy of `icon-1024.png` shown at `width="256"` works well at the top of a README; give the `<img>` real alt text.

## Script reference

```
make-mac-icon.sh SOURCE.png OUT_DIR [TOP_COLOUR BOTTOM_COLOUR]
```

- Needs ImageMagick (`magick`); resizes with the built-in `sips`.
- Artwork is scaled to 690 pixels, centred on the plate, and nudged 8 pixels down. Edit the script if an image needs more or less room.
- Exit 64 for bad arguments, 66 for a missing source file, 69 if `magick` is missing.
- Tested 2026-09-26 against Streamer's hand-made icon: nine of the ten sizes byte-identical, the 1024 one pixel-identical (only PNG metadata differs), and `Contents.json` equivalent.

## Not covered

Only the Xcode asset catalogue route has been used. An app that wants a single `.icns` file instead can probably get one from the same PNGs with `iconutil`; check `man iconutil` and try it before telling the user it works.
