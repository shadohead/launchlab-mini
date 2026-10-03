# TCRT5000 module: user measurements, 2026-09-21

Units: mm. These are user-reported caliper measurements of the blue TCRT5000/LM393 module pictured in IMG_7445–IMG_7448, not the subsequently discussed QRE1113 breakout. No CAD release or firmware has been changed by this record.

## Reported dimensions

| Feature | Measurement | Interpretation / uncertainty |
| --- | --- | --- |
| PCB | 31 long × 13 wide × 1 thick | Excludes components and connector extension. |
| Blue adjustment block | 7 × 7; 6 high | Height interpreted from its own PCB face to highest point, per measurement request. |
| Adjustment block longitudinal position | 12 from connector-end PCB edge | Interpreted to nearest block edge, per request; block extends to 19 from this edge. |
| Adjustment block lateral position | Approximately 0.3 from a long PCB edge | Which edge needs identification. Approximate, not an exact datum. |
| Optical head projection | 12 from its PCB face | Interpreted to outermost lens tip; black housing alone may be shorter. |
| Optical housing footprint | 10 long × 6 wide | Supplied in follow-up; orientation of the 10 mm dimension relative to PCB axes still needs confirmation. |
| Two-lens section footprint | 6 × 7 | User confirmed this describes the two-lens section; not individual lens diameters or center spacing. |
| Lens protrusion above black housing | 2.5 | User explicitly confirmed the datum is black housing to lens tip, not PCB to tip. |
| Optical head end position | 1 inset | Interpreted as housing inset from sensor-end PCB edge. Lateral position not supplied. |
| Connector extension | 6 beyond connector-end PCB edge | Bare pins; plugged-in wire housing/bend envelope not supplied. |
| Connector height | 4 from PCB surface | Side identified from photos; complete connector footprint not supplied. |
| Other solder/lead protrusions | 2 on both sides | Local protrusions; locations/footprints not supplied. Do not add 2 to already surface-referenced component heights. |

## Photo evidence and derived envelopes

The side-view photo IMG_7445 shows the blue adjustment block and the optical head on opposite PCB faces. This must be represented explicitly in the next CAD iteration.

Assuming the reported heights use the requested PCB-surface datums, the module's bounding thickness is approximately 12 + 1 + 6 = 19. This spans components at different locations; it does not imply a uniform 19 mm pocket. PCB plus bare connector pins span approximately 31 + 6 = 37 along the length. Wiring and manufacturing clearances are additional, unmeasured allowances.

## Comparison with released v0.7 reference meshes

Read directly from releases/LaunchLab_v07_simplified/preview using trimesh:

- PCB reference: 32 × 14 × 1.6, Z 13.8 to 15.4.
- Optical head reference: 10 × 5.8 × 7, Z 6.8 to 13.8; 7 projection from PCB lower face.
- Pot reference: 7 × 7 × 5, Z 8.8 to 13.8; modeled on the SAME face as the optical head, contrary to the photos.

The optical projection is 5 greater than the old assumed envelope. The adjustment block is 1 taller and on the opposite face. These reference differences are not a completed interference analysis and do not establish required enclosure height.

## Remaining geometry needed before final optical-mount design

1. Optical housing lateral position and orientation of the reported 10 × 6 footprint relative to PCB axes.
2. Identify the long PCB edge used for the approximately 0.3 adjustment-block offset.
3. Establish which way the confirmed trapezoidal opening is oriented on the mount.
4. Establish the assembled spacing between printed plate underside and launcher top; target depth datum is now confirmed below.
5. Photo with mount on launcher and relevant optical opening marked, to register the target to the preserved original-scale top connection.
6. Lens spacing/diameters if aperture clearance cannot otherwise be established, plus chosen wire connector envelope.

Preserve the original two-clip top connection scale. Do not silently substitute QRE1113 dimensions or treat any sensor as optically validated through the launcher opening. A fit coupon and real black/white signal test should precede a final revised enclosure print.

## Follow-up: outer optical opening (user-confirmed shape and depth datum)

The user subsequently confirmed the interpreted opening shape and that target depth is measured from the launcher's own top surface to its internal black/white ring. Dimensions remain user-reported and approximate, not independently verified:

- Trapezoidal opening viewed from above: 5 between the parallel edges; short edge 5; long edge 6.
- Printed plate thickness: approximately 3.
- Launcher opening: reported to have the same shape/dimensions.
- Target depth: approximately 1–2 below the launcher's own top surface, to its internal black/white ring.
- User subsequently confirmed the two-lens section is 6 × 7, with 2.5 protrusion from black housing to lens tips. This is the pair's overall footprint, not center spacing or individual lens diameters. Final optical-axis location remains unmeasured.

Raw user wording: “1. 10mm x 6 wide 2. the opening for the outer opening is 5mm tall and 5. the thickness is like 3 mm, the hole hopening on the short trapezoidal side and. 6 on the larger side and the launcher opening is the same . the depth is maybe 1-2mm. the”

The 10 × 6 housing cannot be assumed to pass through this approximately 5–6 wide opening. This does not by itself establish optical failure: the relevant quantities are both optical paths, aperture thickness, lens spacing, alignment and target gap. No release geometry has been altered using these aperture dimensions.

If the approximately 3 mm printed plate underside sits flush against the launcher top, the printed plate upper surface is approximately 4–5 mm above the target (3 + 1–2). This is NOT a measured lens-to-target gap. Any plate-to-launcher spacing and lens setback above the plate add to that distance; a lens protrusion/recessed mounting arrangement reduces it. The usable optical path through both openings still needs verification.

The reported 7 mm lens-pair span exceeds the opening's 5–6 mm transverse width. For alignment along that width this suggests partial optical obstruction, but it does not establish failure or quantify transmitted/returned light. Lens span is not emitter/receiver center spacing, and aperture orientation, lens field of view, distance and target reflection matter. Test black/white contrast through the actual launcher opening, followed by fast-pull capture, before committing a new enclosure around this sensor. Do not enlarge the launcher or change the original clip interface based on this comparison alone.

Height reconciliation: retaining the earlier interpreted 12 mm PCB-face-to-lens-tip measurement, the black housing's lens-side surface is approximately 12 - 2.5 = 9.5 mm from that PCB face. This is a derived placement dimension including the lead standoff; it is NOT the black housing's body thickness. The 2.5 mm is already included in the 12 mm total and must not be added again.
