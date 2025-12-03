# Mark Feature Example

This project is a minimal example on how to set up and build a mark feature in a UFO workflow.

### Various hand-edited files:

* `font.ufo` – the main source file with anchors and `COMBINING_MARKS` group in place. Subset of Source Serif Display.
* `features.fea` – the file tying all the features together
* `GSUB.fea` – contains all GSUB features

### Various generated files:

* `GlyphOrderAndAliasDB` – spreadsheet which helps `makeotf` understand ordering and code point mapping. Built using the FDK’s [`goadbWriter`](https://github.com/adobe-type-tools/python-modules/blob/main/goadbWriter.py)
* `kern.fea` – GPOS kerning. Built using the FDK’s [`kernFeatureWriter`](https://github.com/adobe-type-tools/python-modules/tree/main?tab=readme-ov-file#kernfeaturewriterpy)
* `mark.fea` – GPOS mark feature. Built using the FDK’s [`markFeatureWriter`](https://github.com/adobe-type-tools/python-modules/tree/main?tab=readme-ov-file#markfeaturewriterpy)
* `mkmk.fea` – GPOS mark-to-mark feature. Also built using the FDK’s [`markFeatureWriter`](https://github.com/adobe-type-tools/python-modules/tree/main?tab=readme-ov-file#markfeaturewriterpy)
* `MarkFeatureTest-Regular.otf` – the product of this whole exercise


## Building the font:

Navigate to the directory containing the UFO file, and execute

    makeotf -r

`-r` stands for “release mode”, the most important effect in our case is applying the `GlyphOrderAndAliasDB` file ordering, and assigning Unicode code points.

---

NB: `makeotf` relies on finding a number of specifically-named files:

* `font.ufo`
* `features.fea`
* `GlyphOrderAndAliasDB`


Using other file names is possible, but requires additional arguments. See `makeotf -h` for further information.
