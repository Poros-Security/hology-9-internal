# Design — STELLAR

A locked design system for an unofficial Hoshimachi Suisei fan archive. The
site must feel like a lovingly edited artist publication. The native GIF and
encryption implementation is invisible presentation plumbing.

## Genre

Atmospheric editorial: image-led, nocturnal, expressive, and restrained.

## Macrostructure family

- Home: **Photographic** — one dominant Suisei image, concise introduction,
  then music and memory fragments.
- Profile and highlights: **Long Document** — readable narrative sections and
  a chronological spine.
- Music and gallery: **Catalogue / Portfolio Grid** — artwork and media lead;
  technical data never appears.

## Theme

- `--color-paper` oklch(12% 0.035 264)
- `--color-paper-2` oklch(17% 0.052 264)
- `--color-paper-3` oklch(22% 0.070 260)
- `--color-ink` oklch(97% 0.014 238)
- `--color-ink-2` oklch(82% 0.040 240)
- `--color-muted` oklch(68% 0.045 245)
- `--color-rule` oklch(36% 0.075 257)
- `--color-accent` oklch(63% 0.205 253)
- `--color-accent-2` oklch(82% 0.125 229)
- `--color-rose` oklch(66% 0.185 8)
- `--color-focus` oklch(87% 0.145 222)

Suisei blue is the dominant signal. Rose is limited to tiny highlight moments.

## Typography

- Display: Archivo Variable, weight 700, width 112, roman
- Body: Archivo Variable, weight 400, width 100
- Japanese fallback: Noto Sans JP Variable
- Display tracking: -0.045em
- Type scale anchor: `--text-display = clamp(2.8rem, 9vw, 7rem)`

The open-source font files are bundled locally so the Linux desktop build stays
offline and deterministic. Archivo gives STELLAR the wide geometric character
of the official site's Avantt without redistributing that commercial face.

## Spacing

A 4-point named scale lives in `tokens.css`. No page invents spacing values.

## Motion

- Image reveal: opacity only
- Links and controls: short transform or color feedback
- Reduced motion: instant or opacity-only under 150 ms

## Microinteractions stance

- Quiet and tactile; no toasts or decorative celebration
- Visible focus is immediate
- Media auto-plays and loops like an ordinary GIF
- Optional play/pause is the only exposed playback control

## What pages MUST share

- Top masthead, STELLAR wordmark, and original four-point aperture logo
- Suisei blue palette and image treatment
- Display/body typography
- Editorial captions and source credits
- Unofficial-project disclaimer

## What pages MUST NOT expose

- SGIF, encryption, native decoder, filenames, frame registers, disposal modes,
  backend diagnostics, or challenge-specific metadata

## Exports

The canonical implementation is [`tokens.css`](tokens.css).
