# LaunchLab v0.19 — compact OLD TCRT5000 + top-mounted M5StickS3

This is a **separate old-sensor variant**. The complete v0.17 QRE1113 package is preserved unchanged while you print it. The intact M5 sits exposed on top of a sensor cradle and removable top dock; there are no enclosing M5 walls, separate battery bay, screen cradle or top retaining frame.

The core footprint is **43.15 × 48 mm**, compared with the previous M5/TCRT enclosure's 44 × 72.5 mm. It is 24.5 mm shorter, a 34% reduction in length. Original clips extend the assembled width to approximately **59.78 mm**. The M5 top is Z38.9, **35.12 mm above the modeled launcher plane**; it is 2.7 mm below the earlier v0.15 frame top. Provisional connectors and the short rear loop extend length to about 56.2 mm; actual connector housings and bends are unmeasured.

## Sensor identity and dimension basis

**OLD means the blue TCRT5000/LM393 analog/digital module pictured in IMG_7445–7448. It does not mean QRE1113.** The source is the user's recorded caliper measurements, copied into `references/TCRT5000_user_measurements_2026-09-21.md`, together with three original photos.

| Feature | Dimension used | Evidence boundary |
|---|---|---|
| PCB | 31 × 13 × 1 mm | Recorded user measurement |
| PCB lower face to outer lens tips | 12 mm | Recorded user measurement; includes lens protrusion |
| Lens protrusion from housing | 2.5 mm | Already included in the 12 mm total |
| Optical housing footprint | 10 × 6 mm | User measurement; orientation follows prior CAD and photos, lateral center needs confirmation |
| Lens-pair envelope | 7 × 6 mm | User's 6 × 7 measurement oriented as prior CAD; not individual lens diameters |
| Adjustment block | 7 × 7 × 6 mm | Opposite face from optical head, confirmed in side photo |
| Bare header | 6 mm beyond PCB, 4 mm high | User measurement; lateral footprint follows prior CAD |
| Solder/component clearance | 2 mm on both faces | Locations unmeasured; four corner contact lands are reserved from photo-based assumptions |

The correct measured component thickness is **12 + 1 + 6 = 19 mm**. Earlier v0.15 CAD placed the PCB only 10.5 mm above the lens tips. This variant honors the recorded 12 mm rather than silently copying that smaller projection. PCB lower face is Z16.1, top Z17.1, lens tips Z4.1 and adjustment-block top Z23.1. The M5's lowest back is Z23.9, leaving **0.8 mm above the adjustment block**. Two 2 mm support beams run beside the components, with a 0.3 mm soft liner.

PCB pocket clearance is 0.3 mm per side. Four small underside corner lands support the board. The removable M5 top dock includes a 1.4 mm keeper that captures those corners with 0.2 mm nominal vertical play. Its four screws sit outside the M5 footprint and remain accessible. Thin holder cheeks are 1.3 mm thick; the native launcher attachment is kept at its original scale.

The upper optical recess in the printed port accommodates the 7 × 6 lens envelope. Native material below the modeled launcher plane and original clip mating regions are preserved. **The actual launcher is not modified or fully modeled.** Its reported 5–6 mm opening may obscure part of the optical path. Printed clearance does not prove black/white contrast, target alignment or launch-speed response.

## Complete first-build inventory

Print **five installed pieces**, one of each:

| Piece | Print file | Role |
|---|---|---|
| Old-sensor attachment port | `stl/01_TCRT_attachment_port.stl` | Native launcher connection and old-sensor upper optical recess |
| Sensor cradle | `stl/03_TCRT_sensor_cradle.stl` | PCB seats and original clip keepers |
| Removable M5 top dock | `stl/04_TCRT_M5_top_dock.stl` | M5 support and integrated PCB corner keeper |
| Left launcher mounting clip | `stl/02_latch_LEFT.stl` | Original-scale left clip, included unchanged |
| Right launcher mounting clip | `stl/02_latch_RIGHT.stl` | Original-scale right clip, included unchanged |

**`bambu/LaunchLab_v019_P1S_PLA_ALL_PARTS.3mf` is the complete five-piece first-build plate.** `LaunchLab_v019_ALL_PARTS_UNSLICED.3mf` is the same inventory as geometry only. The three-piece `REPLACEMENTS` plate is for an upgrade if the original clips are already owned; the clips-only plate is also included. Do not use a QRE dock or keeper in this old-sensor stack.

The complete five-piece P1S/PLA plate estimates **1h 27m 57s and 21.80 g**, including 11.20 g supports. The sensor-fit pair estimates 18m 21s and 2.83 g; the M5 mount sample estimates 9m 43s and 0.51 g. These are local slicer estimates, not completed prints.

Required nonprinted parts:

- One intact M5StickS3 K150 and one old blue TCRT5000/LM393 module.
- Four **M3×8 DIN912 socket-head screws** to join sensor cradle and port. Nominal printed-post engagement is 6.6 mm; tips remain 0.766 mm above the source post bottom.
- Two **M2×6 pan-head screws** into the user-confirmed brass M5 inserts, from underneath. Nominal insert engagement is 1.7 mm; actual insert depth must be checked.
- Four **M2×4 pan-head screws** for the removable M5 top dock, into printed pilots. Nominal engagement is 2.6 mm. These do not pass through PCB holes.
- A 0.3 mm soft liner cut to the two long M5 beams, and a short three-wire analog harness. Connector housings and strain relief are not physically measured.

No nuts, separate display, external battery or Grove attachment are required. Factory M5 cover screws stay installed. Existing analog wiring remains sensor VCC → Hat 3V3_L2, GND → Hat GND, AO → Hat G1. DO is unused. Verify actual labels and polarity; no firmware or device setting is changed by this package.

## Fit samples and assembly

Print the optional samples before committing to the dock:

- `extras/11_TCRT_SEAT_FIT.stl` and `extras/12_TCRT_KEEPER_FIT.stl`, used together: checks PCB size, corner lands, solder clearance, keeper play and printed pilots. The keeper must land on clear PCB corners, not components or solder joints. These locations are an assumption until checked against your board.
- `extras/13_M5_MOUNT_FIT.stl`: checks the two brass axes, 2 mm stepped factory mounting face, liner and M2 insertion depth. The two axes are 18 mm apart, 3 mm inward from the Grove-end edge.

1. Install both original clips in the separate old-sensor port. Lower the sensor cradle onto the port and fit four M3×8 screws. Confirm clip opening and retention on the actual launcher without forcing or scaling it.
2. With the M5 top dock removed, lower the old PCB vertically onto the cradle's four corner lands, lens tips downward and bare header toward +Y. Check underside solder, head clearance and clear PCB corner contact areas.
3. Prepare the M5 top dock separately. Add the 0.3 mm liner to its long beams and place the intact M5 on them, **Grove/USB toward −Y and Hat toward +Y**. Install two M2×6 screws from below into the brass inserts while this top module is off the cradle. Stop if a screw bottoms before seating. Grove carries no attachment load.
4. Lower this M5/top-dock module onto the sensor cradle. Its integrated corner keeper captures the PCB with 0.2 mm nominal play. Fit four M2×4 screws through the exposed side ears into the cradle's pilots. Check that the keeper avoids all solder/components, the adjustment block has its 0.8 mm clearance, and printed pilots hold without splitting. Do not bend or compress the PCB.
5. Connect the short three-wire analog harness at +Y, with both the sensor header and Hat at the same end. The open rear accommodates the socket and wire bends. Keep wires clear of screws, clip movement and the optical path. Screen, buttons, USB/Grove and Hat remain exposed.

For sensor service, unplug the harness and remove the four M2×4 top-dock screws. Lift the M5 and its top dock together, then lift the sensor vertically from the open cradle. To separate the M5 from its top dock, access the two underside M2×6 screws while that module is off the cradle. Four M3 screws release the cradle from the launcher port if required. No populated board needs to slide through fixed rails.

## Files and verification

`LaunchLab_v019_tcrt5000_open_stack.blend` contains assembled, underside, exploded and complete five-piece print views. `step/` contains editable solids, `stl/` contains print-oriented meshes, and `preview/` holds assembled meshes and reference envelopes. Reference electronics and screws are not printed pieces. `print_inventory.json` specifies quantities, hardware and filenames. `reports/` provides CAD/mesh validity, preserved interface checks, nominal clearances, mounting bearing/contact, driver access, sampled assembly/service/clip movement, saved-model and project readback, slice metrics and package completeness.

The original clips are unchanged from the older full v0.2 source. The manufacturer M5 reference uses the three assembled shell pieces with a rigid translation only. Pot/header/head registration and corner contact lands have documented assumptions; plug/wire/solder allowances are not scans of the populated assembly. Digital checks and local slice estimates do not establish physical fit, attachment strength, insert depth, optical performance, RPM accuracy or runtime. No printer job or purchase is initiated.

See `LICENSE.txt` for Migbello's original BP Gear Port Connector attribution. Manufacturer case geometry is an unmodified reference, not a printed replacement for the factory M5 shell.
