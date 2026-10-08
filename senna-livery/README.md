# Carta x Senna tribute livery

A McLaren MP4/4 inspired (Marlboro-era red/white) livery for the Carta Car Customizer car,
rendered through the same composite pipeline the customizer's "Export PNG" button uses:
background, floor shadow, base car photo, livery SVG multiplied through the body mask, then
overlay stickers.

- `carta-senna-livery.png` – the final 3068x1088 export.
- `index.html` – standalone page with the livery SVG and the export composite (open in a browser).
- `render.cjs` – headless Chromium render: `NODE_PATH=<path to node_modules with playwright> node render.cjs`.
- `assets/` – the base car and body mask extracted from the original bundled customizer HTML.

Livery notes: red (#E1251B) nose and rear with the forward-pointing chevron split, white door band,
carbon-black roof and sills, Carta logo on the door (black) plus front fender and rear quarter (white),
Senna's 1988 number 12 in red with a white keyline, and a Brazilian flag door sticker.
