# Rebuild the v0.68 carrier

The editable Blender file and complete manufacturing STL are included one
directory above. The STEP file contains the analytic hook only.

`carrier_before_hook.stl` is the exact pre-hook v0.65 carrier, including its
launcher attachment, side-open channel, screw seats and two support humps.
`build.py` reads the published parameters, creates the rounded hook, unions it
with that baseline, and applies the saved manufacturing pose. Its geometry does
not depend on private drawing submissions or earlier development directories.

From this directory, using Python 3.12:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python build.py --output /tmp/launchlab-v068-rebuilt
```

Choose a new output directory if that path already exists. The builder preserves
the frozen package. It emits native and print-oriented STLs plus the hook STEP.
Compare the rebuilt native STL with `../preview/01_M5_channel_two_humps_cable_hook.stl`
and the print STL with `../stl/01_M5_channel_two_humps_cable_hook.stl`.

The source dependencies record the versions used for the saved build. The source
mesh, complete carrier meshes, hook STEP and sliced 3MF retain their original
geometry. Public documentation and relative evidence paths were prepared for
this repository; private markup and local dispatch records are not included.

Rebuilding or slicing does not establish printed fit, wire retention or strength.

Rebuild verification compares mesh surfaces, bounds and volume. Coplanar
triangle subdivisions can differ without changing the carrier surface.
