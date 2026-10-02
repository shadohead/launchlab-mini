# Contributing

Keep changes focused on M5StickS3 K150, analog QRE sensing, print files, and the USB updater. Run the native sanitizer suites, site tests, production site build, and artifact checks before submitting a pull request.

Keep firmware and hardware versions separate. Never silently replace a published binary or frozen print package. Publish a new version and checksum. Update `site/public/firmware/catalog.json` alongside the firmware images, record the exact source/toolchain, and distinguish software evidence from physical acceptance.

Do not commit device backups, factory flash dumps, personal practice logs, secrets, build caches, or editor autosaves. Preserve upstream copyright and the hardware share-alike attribution. Inspect file paths before exporting a release archive.
