---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Slides from Spec — AI-Powered Deck Generation

Generate beautiful presentation decks from code generation specs or marketing narratives.

## Quick Start

### Setup (one-time)

1. **Get Kie.ai API key**
   ```bash
   # Sign up at kie.ai
   export KIE_API_KEY=your_key_here
   ```

2. **Get Google credentials**
   ```bash
   # Google Cloud Console → service account → download JSON
   export GOOGLE_CREDENTIALS_JSON=/path/to/creds.json
   ```

3. **Install dependencies**
   ```bash
   npm install  # Node.js: kie, axios, dotenv
   pip install -r requirements.txt  # Python: google-api-python-client, pptx, pillow
   ```

### Generate Demo Deck (from spec.json)

```bash
node scripts/generate.js --template demo-deck --style isometric --spec ../spec.json
python scripts/compile.py --slides-dir ./slides --output demo-deck.pptx --title "Shopping Cart"
```

Output: `demo-deck.pptx` (10 slides, ready for demo calls)

### Generate Conference Talk (from positioning)

```bash
node scripts/generate.js --template conference-talk --style ted-ed
python scripts/compile.py --slides-dir ./slides --output pycon-talk.pptx --title "One-Shot at PyCon"
```

Output: `pycon-talk.pptx` (20 slides, ready for conference)

### Generate Onboarding Deck

```bash
node scripts/generate.js --template onboarding --style isometric
python scripts/compile.py --slides-dir ./slides --output onboarding.pptx --title "Get Started with One-Shot"
```

Output: `onboarding.pptx` (5-7 slides, quickstart guide)

## How It Works

1. **YAML Template** — Maps slide sections to Kie.ai image prompts
2. **Node.js Generator** — Calls Kie.ai API, saves PNG images (1920x1080)
3. **Python Compiler** — Takes PNGs, creates Google Slides PPTX, adds speaker notes

Each slide is a full-bleed PNG image (no text overlays except titles).

## Templates

- **demo-deck** (10 slides) — Visualize generated code from spec.json
- **conference-talk** (20 slides) — Present positioning + metrics
- **onboarding** (5-7 slides) — Quick introduction for new users

Create new templates by adding YAML files to `templates/` directory.

## Styles

- **isometric** — Professional, data-heavy (3D geometric)
- **ted-ed** — Warm, narrative-driven (hand-drawn organic)

Each style is defined in `style/*.txt` and prepended to Kie.ai prompts for visual consistency.

## Troubleshooting

**"API key not found"**
```bash
export KIE_API_KEY=your_key_here
```

**"No images generated"**
- Check Kie.ai API quota (free tier: 100 images/month)
- Verify prompt quality (too vague prompts fail)
- Check API status at kie.ai/status

**"Google Drive auth error"**
- Verify `GOOGLE_CREDENTIALS_JSON` path is correct
- Ensure Google Slides API is enabled in Cloud Console
- Check service account has Drive write permissions

## Examples

See `examples/` directory for:
- `one-shot-demo.spec.json` — sample spec.json
- `sample-output/` — generated images from demo-deck template

## Cost

- **Kie.ai:** Free tier = 100 images/month. Paid: $0.05-0.10/image
- **Google Slides:** Free (built into Workspace)
- **Total cost per 20-slide deck:** $1-2 (images only)

## Next Steps

- [ ] Try generating a demo deck from your spec.json
- [ ] Customize a template for your use case
- [ ] Share feedback: [GitHub issues](https://github.com/usmanmughaltaleemabad/one-shot-prompting/issues)
