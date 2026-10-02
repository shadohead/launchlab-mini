# LaunchLab v0.33 — narrower, lower sensor platform

The launcher-facing center step is trimmed 0.5 mm on each side (1 mm narrower overall). Its native left edge has sub-micron facet variations; the trim follows its fitted plane within 0.00044 mm. The entire central solid moves down 1 mm, including the flat floor, board lands, component relief, header-tail clearance and centered screw posts. The side clips, hinge beds and clip screw posts stay at their existing height. The outer shoulder clearance beside the narrowed step extends to its original Z4.78 ceiling.

The PCB pocket still has 0.12 mm clearance per edge and a 9.24 mm opening for the 9 mm board. The PCB seat moves from Z6.4 to Z5.4; the nominal optical face moves from Z4.1 to Z3.1. The board, optics, resistors, upright Dupont plugs, sensor screws and pressure plate all move down by exactly 1 mm, retaining their prior relative clearances. The separate M5 platform is unchanged. The previous launcher-top reference is a CAD datum, not a measured model of the installed black launcher surface.

Only `01_QRE_minimal_port` needs printing. Reuse the v0.32 centered pressure plate, thicker latch crossbar, original left/right latches, separate M5 platform and four screws. The reused parts' manufacturing STLs are byte-identical to v0.32; the pressure plate has a lower assembly pose in this release. Older end-screw pressure plates do not match the centered posts.

The new base slice estimates 40m 1s and 5.59 g of PLA, including 1.96 g of support. All 216 model layers have deposition, and the adjacent layers on both sides of each thin center join deposit material through the 0.62 mm overlap.

A local Bambu P1S / PLA project contains only the new base, on its existing side print orientation, with 0.2 mm layers, Arachne walls and Tree Slim supports. Filament 3 is the requested dispatch mapping, not an assignment implied by the local slice. No printer dispatch.

Real Blender views and an editable STEP assembly show the actual exported geometry and nominal electronics. Digital checks include requested dimension changes, valid single-solid CAD, watertight mesh, unchanged outer mounting regions and hinges, original latch motion, board capture, screw access, component clearances and saved slicer geometry. The center-to-side joining height at the flat shoulder is 0.62 mm. Installed launcher clearance, printed strength and actual optical response require a physical fit check.

Source BP Gear Port: Migbello, Thingiverse 6856080, CC BY-SA (version unspecified). See `references/QRE_BP_port_LICENSE.txt` and `LICENSE.txt`.
