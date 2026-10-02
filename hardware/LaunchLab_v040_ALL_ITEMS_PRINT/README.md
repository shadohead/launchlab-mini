# LaunchLab v0.40 complete print package

Open `bambu/LaunchLab_v040_P1S_PLA_ALL_ITEMS_ONE_PLATE.3mf` in Bambu Studio. It contains one plate with one of each of the six required printed parts:

- v0.33 QRE base, with the center step trimmed 0.5 mm per side and the center platform/sensor seat lowered 1 mm.
- v0.32 thicker latch crossbar.
- v0.32 centered sensor pressure plate, upright on its continuous flat edge.
- Left launcher latch.
- Right launcher latch.
- v0.40 separate M5 platform with the circled right block trimmed 3 mm left and its factory edge finish restored.

Only the M5 platform changes; reuse the five sensor parts if you already have them. The circled raised right block is shortened 3 mm toward the left in the top view with USB-C on the right. Its end changes from Y-18.5 to Y-15.5. The opposite edge's native 0.5 mm bevel, including its corner, is copied onto the new top edge. The lower launcher foot, curved receivers, M5 position, 2 mm deck, M2 mounting posts and other raised block are preserved. See `reports/M5_before_after.png` for a rendering of the actual meshes.

Settings: Bambu P1S, 0.4 mm nozzle, PLA, 0.2 mm layers, Arachne walls and 5 mm outer brims. Tree Slim supports are enabled globally, with supports explicitly disabled on the upright pressure plate. All six parts retain their manufacturing geometry and print orientations; auto-arrangement changes only their positions and rotation within the plate.

The slice estimates 1h 15m 59s and 18.04 g of PLA. Assign the project's single PLA filament to AMS filament 3 in the print dialog. This package has not been dispatched to the printer.

Nominal assembly hardware:

- 2 x M2x6 screws for the M5 platform, installed from underneath.
- 2 x M2x5 countersunk screws for the latch crossbar.
- 2 x M2x4 pan-head screws for the sensor pressure plate.

Individual STLs are included in `stl/`. Each matches its frozen source release byte-for-byte. The five QRE STEP files are included in `step/`; the M5 platform is supplied as a mesh. The saved 3MF is checked against all six source STLs, its G-code checksum and per-object settings are verified, and all models fit within one P1S plate. Actual model deposition is checked for every part, with no support deposition through the pressure plate's bounding box. Digital clearance checks pass; physical thumb reach, button operation and the trimmed mount's strength need checking after printing.

Source BP Gear Port and native grip: Migbello, Thingiverse 6856080, CC BY-SA (version unspecified). See `LICENSE.txt` and `references/QRE_BP_port_LICENSE.txt`.
