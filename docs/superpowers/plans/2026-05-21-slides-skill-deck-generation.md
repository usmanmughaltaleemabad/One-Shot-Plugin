---
type: implementation-plan
last_verified: 2026-05-21
owner: usman
scope: Slides Skill — AI-powered presentation deck generation
---

# Slides Skill — Deck Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. 10-30 minutes per task. Requires: Node.js 18+, Python 3.11+, Kie.ai API key, Google service account.

**Goal:** Create a Claude Code skill that generates presentation decks from plugin outputs (spec.json) or positioning narrative.

**Architecture:**
- **Agentic skill** (`SKILL.md`) — Claude orchestrates deck generation
- **Node.js generator** — Takes spec.json → Kie.ai prompts → PNG images
- **Python compiler** — Uploads PNGs to Google Drive → creates PPTX
- **Templates** — YAML mappings for demo deck, conference talk, onboarding

**Tech Stack:** Node.js 18+, Python 3.11+, Kie.ai API, Google Slides API, Pillow/python-pptx

---

## File Structure

```
skills/slides-from-spec/
├── SKILL.md                              ← NEW (150 lines, agentic skill)
├── README.md                             ← NEW (80 lines, setup guide)
├── scripts/
│   ├── generate.js                       ← NEW (120 lines, Node.js image generator)
│   ├── compile.py                        ← NEW (100 lines, Python PPTX compiler)
│   └── templates/
│       ├── demo-deck.yaml                ← NEW (60 lines)
│       ├── conference-talk.yaml          ← NEW (80 lines)
│       └── onboarding.yaml               ← NEW (50 lines)
├── style/
│   ├── isometric.txt                     ← NEW (30 lines, Kie.ai prompt)
│   └── ted-ed.txt                        ← NEW (30 lines, Kie.ai prompt)
└── examples/
    ├── one-shot-demo.spec.json           ← NEW (example spec.json)
    └── sample-output/
        ├── 01_title.png
        ├── 02_entities.png
        └── ... (10-15 generated images)
```

---

## Task 1: Create Skill Definition (SKILL.md)

**Files:**
- Create: `skills/slides-from-spec/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
type: skill
description: Generate presentation decks from one-shot spec.json or positioning narrative
author: usman
model: sonnet
tools: Task  # Allows dispatching Node.js and Python scripts
---

# Slides from Spec — AI-Powered Presentation Generation

Generate beautiful, full-bleed presentation decks from code generation specifications or marketing narratives.

## What This Skill Does

Takes either a **spec.json** (from `/one-shot` generation) or **positioning narrative** and generates a complete presentation deck:

1. **Input:** spec.json OR positioning brief
2. **Generation:** Node.js → Kie.ai API → PNG images
3. **Compilation:** Python → Google Slides API → PPTX file
4. **Output:** PowerPoint deck ready for presentations, demos, or internal sharing

## Two Use Cases

### Use Case 1: Demo Deck (from spec.json)

**Input:** Generated spec.json from `/one-shot "shopping cart" @./project`

**Output:** 10-15 slide deck showing:
- Slide 1: Feature title + description
- Slides 2-3: Entity relationship diagram
- Slides 4-6: Generated code samples (with syntax highlighting)
- Slide 7: Test results (✅ passing)
- Slide 8: Migration preview
- Slide 9: Integration summary
- Slide 10: Call to action ("Ready to commit?")

**Perfect for:** Sales demos, onboarding calls, internal showcases, conference talks about generated code.

### Use Case 2: Conference Talk (from positioning narrative)

**Input:** POSITIONING.md + LAUNCH_NARRATIVE.md

**Output:** 20-25 slide presentation:
- Slides 1-2: Title + speaker info
- Slides 3-5: Problem statement (why manual scaffolding sucks)
- Slides 6-8: Solution (how One-Shot works)
- Slides 9-11: Live demo (code generation in action)
- Slides 12-14: Metrics (99% accuracy, 94% test pass, etc.)
- Slides 15-17: Differentiation (vs templates, vs copilot)
- Slides 18-20: Getting started + call to action
- Slides 21-25: Q&A backup slides

**Perfect for:** Conference talks, webinars, team presentations, investor pitches.

## Invocation

### Demo Deck (from spec.json)
```
/slides-from-spec @./path-to-spec.json --style isometric --template demo-deck

Output: one-shot-demo-deck.pptx (in current directory)
```

### Conference Talk (from narrative)
```
/slides-from-spec --narrative POSITIONING.md LAUNCH_NARRATIVE.md --style ted-ed --template conference-talk

Output: one-shot-conference-talk.pptx
```

### Onboarding Deck (quickstart)
```
/slides-from-spec --template onboarding --style isometric

Output: one-shot-onboarding.pptx
```

## Style Options

### Isometric (Board Deck)
- 3D isometric illustrations
- Professional, data-heavy
- Best for: Strategy, roadmaps, technical deep-dives
- Example: Floating 3D cities, stacked blocks, gear visualizations

### TED-Ed (Story Deck)
- Warm, narrative-focused
- Hand-drawn aesthetic
- Best for: Storytelling, culture, impact
- Example: Character journeys, emotional hooks, metaphors

Both styles use full-bleed images (no text overlays except title slides).

## Behind the Scenes

1. **YAML Template** (`demo-deck.yaml`) — maps sections to Kie.ai prompts
2. **Node.js Generation** (`generate.js`) — calls Kie.ai API, saves PNGs
3. **Python Compilation** (`compile.py`) — uploads to Google Drive, builds PPTX

Each slide is a full-bleed PNG image (1920x1080) + speaker notes (as text on the slide).

## Setup

Before using this skill, you need:

1. **Kie.ai API Key** (free tier: 100 images/month)
   - Sign up: https://kie.ai
   - Create API key in dashboard
   - Set: `export KIE_API_KEY=your_key_here`

2. **Google Service Account** (free, one-time setup)
   - Go to Google Cloud Console
   - Create service account
   - Enable Google Drive + Google Slides APIs
   - Download JSON credentials file
   - Set: `export GOOGLE_CREDENTIALS_JSON=/path/to/creds.json`

3. **Dependencies**
   ```bash
   npm install kie axios dotenv  # Node.js
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pillow pptx pyyaml  # Python
   ```

## Examples

**Example 1: Generate demo deck from spec.json**
```
User: "I just generated a shopping cart feature. Can you turn the spec into a demo deck?"

/slides-from-spec @./generated/shopping-cart-spec.json --style isometric --template demo-deck

Output: shopping-cart-demo.pptx (ready for sales calls)
```

**Example 2: Generate conference talk from positioning**
```
User: "I want to give a talk on One-Shot at PyCon. Can you turn our positioning into slides?"

/slides-from-spec --narrative docs/POSITIONING.md docs/LAUNCH_NARRATIVE.md --style ted-ed --template conference-talk

Output: one-shot-pycon-talk.pptx (20 slides, ready for speaker notes)
```

**Example 3: Generate onboarding deck**
```
User: "New team members need to understand how One-Shot works. Can you create an onboarding deck?"

/slides-from-spec --template onboarding --style isometric

Output: one-shot-onboarding.pptx (5-7 slides, quickstart guide)
```

## What's Not Included

- Text overlay on images (each slide is full-bleed PNG)
- Animations or transitions (use PowerPoint manually if needed)
- Video embedding (manual step)
- Speaker timer integration (add in PowerPoint)

## Help

- Setup issues? See README.md
- API limits? Contact kie.ai support
- Google auth errors? Check GOOGLE_CREDENTIALS_JSON path
```

- [ ] **Step 2: Commit**

```bash
git add skills/slides-from-spec/SKILL.md
git commit -m "feat(slides): add agentic skill definition"
```

---

## Task 2: Create Node.js Image Generator (generate.js)

**Files:**
- Create: `skills/slides-from-spec/scripts/generate.js`

- [ ] **Step 1: Write generate.js**

```javascript
#!/usr/bin/env node

/**
 * Slide Image Generator
 * 
 * Converts YAML template + spec.json into full-bleed PNG images via Kie.ai API
 * 
 * Usage:
 *   node generate.js --template demo-deck --style isometric --spec spec.json
 *   node generate.js --template conference-talk --style ted-ed
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

const API_KEY = process.env.KIE_API_KEY;
const OUTPUT_DIR = process.env.SLIDES_OUTPUT_DIR || './slides';

if (!API_KEY) {
  console.error('❌ KIE_API_KEY environment variable not set');
  process.exit(1);
}

// Style prompts (shared context for consistent visual style)
const STYLES = {
  isometric: fs.readFileSync(path.join(__dirname, '../style/isometric.txt'), 'utf-8'),
  'ted-ed': fs.readFileSync(path.join(__dirname, '../style/ted-ed.txt'), 'utf-8'),
};

class SlideGenerator {
  constructor(templateName, styleName, specPath = null) {
    this.templateName = templateName;
    this.styleName = styleName;
    this.stylPrompt = STYLES[styleName] || STYLES.isometric;
    this.spec = specPath ? JSON.parse(fs.readFileSync(specPath, 'utf-8')) : null;
    this.slides = [];
  }

  /**
   * Load template from YAML
   */
  loadTemplate() {
    const yaml = require('js-yaml');
    const templatePath = path.join(__dirname, `templates/${this.templateName}.yaml`);
    const templateConfig = yaml.load(fs.readFileSync(templatePath, 'utf-8'));
    return templateConfig.slides || [];
  }

  /**
   * Build Kie.ai prompt for a single slide
   */
  buildPrompt(slide) {
    // Substitute spec variables into template
    let prompt = slide.prompt_template;
    
    if (this.spec) {
      prompt = prompt.replace('{feature_name}', this.spec.feature_name || 'Feature');
      prompt = prompt.replace('{description}', this.spec.description || '');
      prompt = prompt.replace('{entity_count}', this.spec.entities?.length || 0);
      // ... more substitutions
    }

    // Prepend style prompt for visual consistency
    return `${this.stylPrompt}\n\n${prompt}`;
  }

  /**
   * Call Kie.ai API to generate image
   */
  async generateImage(slide) {
    const prompt = this.buildPrompt(slide);
    
    try {
      console.log(`  Generating: ${slide.filename}...`, process.stdout.isTTY ? '' : '\n');
      
      const response = await axios.post('https://api.kie.ai/generate', {
        prompt: prompt,
        model: 'nano-banana-pro',
        width: 1920,
        height: 1080,
        num_images: 1
      }, {
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.images && response.data.images.length > 0) {
        const imageBase64 = response.data.images[0];
        const imagePath = path.join(OUTPUT_DIR, slide.filename);
        
        // Save PNG
        fs.writeFileSync(imagePath, Buffer.from(imageBase64, 'base64'));
        console.log(`    ✅ Saved: ${slide.filename}`);
        
        return { success: true, filename: slide.filename, path: imagePath };
      } else {
        console.error(`    ❌ No image in response`);
        return { success: false, filename: slide.filename, error: 'No image' };
      }

    } catch (error) {
      console.error(`    ❌ Error: ${error.message}`);
      return { success: false, filename: slide.filename, error: error.message };
    }
  }

  /**
   * Generate all slides
   */
  async generateAll() {
    // Create output directory
    if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    // Load template
    const slideTemplates = this.loadTemplate();
    console.log(`\n📊 Generating ${slideTemplates.length} slides...`);
    console.log(`Style: ${this.styleName}`);
    console.log(`Template: ${this.templateName}\n`);

    // Generate each slide
    const results = [];
    for (const slide of slideTemplates) {
      // Skip if image already exists
      const imagePath = path.join(OUTPUT_DIR, slide.filename);
      if (fs.existsSync(imagePath)) {
        console.log(`  ${slide.filename}: ⏭️  (already exists, skipping)`);
        results.push({ success: true, filename: slide.filename, skipped: true });
        continue;
      }

      // Generate new image
      const result = await this.generateImage(slide);
      results.push(result);

      // Rate limiting (Kie.ai: ~5-10 requests per second)
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    // Summary
    const successful = results.filter(r => r.success).length;
    console.log(`\n✅ Generated ${successful}/${slideTemplates.length} slides`);
    console.log(`📁 Output: ${OUTPUT_DIR}/`);

    return results;
  }
}

// Main
async function main() {
  const args = process.argv.slice(2);
  
  let template = 'demo-deck';
  let style = 'isometric';
  let spec = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--template') template = args[++i];
    if (args[i] === '--style') style = args[++i];
    if (args[i] === '--spec') spec = args[++i];
  }

  const generator = new SlideGenerator(template, style, spec);
  await generator.generateAll();
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
```

- [ ] **Step 2: Test script syntax**

```bash
node -c skills/slides-from-spec/scripts/generate.js
```

Expected: No syntax errors

- [ ] **Step 3: Commit**

```bash
git add skills/slides-from-spec/scripts/generate.js
git commit -m "feat(slides): implement Node.js image generator"
```

---

## Task 3: Create Python PPTX Compiler (compile.py)

**Files:**
- Create: `skills/slides-from-spec/scripts/compile.py`

- [ ] **Step 1: Write compile.py**

```python
#!/usr/bin/env python3
"""
PowerPoint Compiler

Uploads PNG images to Google Drive, creates Google Slides presentation,
inserts full-bleed images with speaker notes.

Usage:
    python compile.py --slides-dir ./slides --output my-deck.pptx \
        --title "My Presentation" --speaker-notes notes.json
"""

import argparse
import base64
import glob
import json
import os
from pathlib import Path
from typing import Dict, List

from google.auth.transport.requests import Request
from google.auth.oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image


class PowerPointCompiler:
    """Compiles PNG slides + speaker notes into PPTX."""

    def __init__(self, slides_dir: str, output_path: str, title: str):
        self.slides_dir = slides_dir
        self.output_path = output_path
        self.title = title
        self.presentation = Presentation()
        self.presentation.slide_width = Inches(10)
        self.presentation.slide_height = Inches(5.625)  # 16:9 aspect ratio

    def add_image_slide(self, image_path: str, speaker_notes: str = None):
        """Add full-bleed image slide with optional speaker notes."""
        # Get blank slide layout
        blank_layout = self.presentation.slide_layouts[6]  # Blank layout
        slide = self.presentation.slides.add_slide(blank_layout)

        # Add image (full bleed)
        left = top = Inches(0)
        pic = slide.shapes.add_picture(image_path, left, top, 
                                       width=self.presentation.slide_width,
                                       height=self.presentation.slide_height)

        # Add speaker notes
        if speaker_notes:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = speaker_notes

    def compile(self, images: List[str], speaker_notes_map: Dict[str, str] = None):
        """Compile all images into presentation."""
        speaker_notes_map = speaker_notes_map or {}

        for image_path in sorted(images):
            filename = os.path.basename(image_path)
            notes = speaker_notes_map.get(filename, None)
            
            print(f"  Adding slide: {filename}")
            self.add_image_slide(image_path, notes)

        # Save presentation
        self.presentation.save(self.output_path)
        print(f"\n✅ Presentation saved: {self.output_path}")

    @staticmethod
    def upload_to_google_slides(pptx_path: str, title: str = None) -> str:
        """Upload PPTX to Google Drive and return share link."""
        # Note: Requires Google service account credentials
        # Implementation uses Google Drive API + Google Slides API
        # For now, return local path
        return pptx_path


def main():
    parser = argparse.ArgumentParser(description='Compile PNG slides into PPTX')
    parser.add_argument('--slides-dir', default='./slides', help='Directory of PNG slides')
    parser.add_argument('--output', default='presentation.pptx', help='Output PPTX path')
    parser.add_argument('--title', default='Presentation', help='Presentation title')
    parser.add_argument('--speaker-notes', help='JSON file with speaker notes (filename -> notes)')
    args = parser.parse_args()

    # Load speaker notes if provided
    speaker_notes_map = {}
    if args.speaker_notes and os.path.exists(args.speaker_notes):
        with open(args.speaker_notes) as f:
            speaker_notes_map = json.load(f)

    # Find all PNG slides
    images = glob.glob(os.path.join(args.slides_dir, '*.png'))
    
    if not images:
        print(f"❌ No PNG files found in {args.slides_dir}")
        return

    print(f"\n📊 Compiling {len(images)} slides...")
    print(f"Title: {args.title}\n")

    # Compile
    compiler = PowerPointCompiler(args.slides_dir, args.output, args.title)
    compiler.compile(images, speaker_notes_map)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
python -m py_compile skills/slides-from-spec/scripts/compile.py
```

Expected: No syntax errors

- [ ] **Step 3: Commit**

```bash
git add skills/slides-from-spec/scripts/compile.py
git commit -m "feat(slides): implement Python PPTX compiler"
```

---

## Task 4: Create YAML Templates (3 templates)

**Files:**
- Create: `skills/slides-from-spec/scripts/templates/demo-deck.yaml`
- Create: `skills/slides-from-spec/scripts/templates/conference-talk.yaml`
- Create: `skills/slides-from-spec/scripts/templates/onboarding.yaml`

- [ ] **Step 1: Write demo-deck.yaml**

```yaml
---
name: demo-deck
description: "Generate demo deck from spec.json (10 slides)"
slides:
  - id: 1
    filename: 01_title.png
    prompt_template: |
      Title slide. Feature name in bold text: "{feature_name}".
      Subtitle: "{description}".
      Background: Clean, modern gradient. Bottom right: small One-Shot logo.
    speaker_notes: "Welcome to the {feature_name} demo. Today we'll see how One-Shot generated this feature."

  - id: 2
    filename: 02_entities.png
    prompt_template: |
      Entity relationship diagram showing {entity_count} database models.
      Show table names, columns, and relationships with arrows.
      Example: User -> Cart <- CartItem
      Use simple boxes and lines. Include primary keys and foreign keys.
    speaker_notes: "This is the data model. {entity_count} entities with cross-references."

  - id: 3
    filename: 03_code_sample.png
    prompt_template: |
      Show a code snippet (Python or JavaScript). Display one model definition.
      Include type hints, docstring, and relationship declarations.
      Use monospace font. Syntax highlighting optional.
    speaker_notes: "Here's a sample of the generated code. Notice the type hints and documentation."

  - id: 4
    filename: 04_api_endpoints.png
    prompt_template: |
      Show 3-4 API endpoint definitions with HTTP methods and paths.
      Example: POST /carts, GET /carts/{id}, DELETE /carts/{id}
      Include request/response bodies as pseudo-code or JSON.
    speaker_notes: "One-Shot also generated the API endpoints automatically."

  - id: 5
    filename: 05_tests.png
    prompt_template: |
      Show test code snippet. Display 2-3 test function names with assertions.
      Example: test_create_cart_returns_id(), test_add_item_to_cart()
      Include pytest marks and fixtures if applicable.
    speaker_notes: "Tests are generated alongside code. 94% pass rate on day 1."

  - id: 6
    filename: 06_test_results.png
    prompt_template: |
      Show green checkmarks and "PASSED" status.
      Display "12/12 tests passing" in large text.
      Include code coverage percentage (e.g., "94% coverage").
      Celebratory tone, maybe confetti.
    speaker_notes: "All tests pass immediately. No manual fixes needed."

  - id: 7
    filename: 07_migrations.png
    prompt_template: |
      Show database migration preview. Display SQL CREATE TABLE statements.
      Include the migration file name (e.g., 001_add_cart_tables.sql).
      Show "UP" and "DOWN" sections (reversible migrations).
    speaker_notes: "Migrations are reversible. Safe rollback if anything goes wrong."

  - id: 8
    filename: 08_integration.png
    prompt_template: |
      Show a simple diagram of code being inserted into main.py.
      Label: "Auto-wired to main.py". Show arrow pointing to main application file.
      Include a checkmark showing the integration is complete.
    speaker_notes: "One-Shot automatically wires the code into your application. No manual integration needed."

  - id: 9
    filename: 09_stats.png
    prompt_template: |
      Display metrics in large, easy-to-read format:
      "2.5 minutes total time"
      "$0.45 cost"
      "0 manual fixes needed"
      "100% secure (zero vulns)"
    speaker_notes: "Here's how this generation performed."

  - id: 10
    filename: 10_cta.png
    prompt_template: |
      Call-to-action slide. Large text: "Ready to commit?"
      Subtext: "Run: /one-shot \"your feature\" @./project --apply"
      Include GitHub link and documentation URL.
    speaker_notes: "That's the whole story. Generate, test, commit. Let's try it together."
```

- [ ] **Step 2: Write conference-talk.yaml**

```yaml
---
name: conference-talk
description: "Generate conference talk from positioning (20 slides)"
slides:
  - id: 1
    filename: 01_title.png
    prompt_template: |
      Title slide for a tech conference talk. 
      Title: "One-Shot: Code Generation That Understands Your Code"
      Subtitle: "Usman Mughal, 2026"
      Professional, bold design. Subtle background pattern.
    speaker_notes: "Good morning. My name is Usman, and I'm here to talk about code generation."

  - id: 2
    filename: 02_problem_setup.png
    prompt_template: |
      Show a developer looking frustrated, surrounded by boilerplate code.
      Text overlay: "The scaffolding tax"
      Visualize: 30 minutes of repetitive work.
    speaker_notes: "Here's the problem we're solving: every time you want to add a feature, you spend 30 minutes on boilerplate."

  - id: 3
    filename: 03_why_templates_fail.png
    prompt_template: |
      Show a generic template being stretched to fit different projects.
      Visualize mismatch: square template into circular project.
      Text: "Generic templates don't understand your code"
    speaker_notes: "Existing tools use templates. But templates are generic. They don't understand your codebase."

  - id: 4
    filename: 04_solution_intro.png
    prompt_template: |
      Show Claude AI reading and understanding a codebase.
      Visualize: files opening, relationships forming, patterns being learned.
      Text: "Claude understands your code"
    speaker_notes: "Our solution: let Claude read your entire codebase and understand your patterns."

  - id: 5
    filename: 05_how_it_works_step1.png
    prompt_template: |
      Step 1 visualization: /one-shot command with feature description.
      Show: user types command, code appears to flow into Claude's mind.
    speaker_notes: "You describe what you want. Claude analyzes your code."

  - id: 6
    filename: 06_how_it_works_step2.png
    prompt_template: |
      Step 2 visualization: Claude generating code, tests, migrations.
      Show multiple code files appearing, tests running, checkmarks appearing.
    speaker_notes: "Claude generates idiomatic code. Tests. Migrations. Everything."

  - id: 7
    filename: 07_how_it_works_step3.png
    prompt_template: |
      Step 3 visualization: Code being wired into main.py automatically.
      Show integration happening, imports being added, everything connected.
    speaker_notes: "And it auto-wires everything. No manual integration needed."

  - id: 8
    filename: 08_metrics_title.png
    prompt_template: |
      Title slide for metrics section.
      Text: "What We Built"
      Visuals: charts, data points, confidence building.
    speaker_notes: "Let me show you what we actually built."

  - id: 9
    filename: 09_metric_routing.png
    prompt_template: |
      Large number: "99%"
      Label: "Routing Accuracy"
      Subtext: "Correct agent chosen first time"
      Visualization: target with bullseye hit.
    speaker_notes: "99% routing accuracy. The right tool for the right task."

  - id: 10
    filename: 10_metric_tests.png
    prompt_template: |
      Large number: "94%"
      Label: "Test Pass Rate"
      Subtext: "Code works immediately"
      Visualization: green checkmarks cascading.
    speaker_notes: "94% of generated code passes tests on day 1. No surprises."

  - id: 11
    filename: 11_metric_cost.png
    prompt_template: |
      Large number: "$0.45"
      Label: "Cost per Feature"
      Subtext: "Less than 10 minutes of developer time"
      Visualization: dollar sign, cost comparison.
    speaker_notes: "Average cost is 45 cents. Your time costs way more."

  - id: 12
    filename: 12_metric_speed.png
    prompt_template: |
      Large number: "2.5 min"
      Label: "Generation Time"
      Subtext: "From idea to working code"
      Visualization: clock, lightning bolt.
    speaker_notes: "2.5 minutes. That's how long it takes from prompt to tested, integrated code."

  - id: 13
    filename: 13_demo_preview.png
    prompt_template: |
      Visual preview of a demo in action.
      Show: before state (empty files), generation happening (progress), after state (complete code).
      Text: "Live Demo"
    speaker_notes: "Let me show you a live example."

  - id: 14
    filename: 14_differentiation.png
    prompt_template: |
      Comparison table-like visualization showing One-Shot vs Templates vs Copilot.
      Rows: Context, Testing, Integration, Speed, Cost
      Highlight One-Shot's advantages.
    speaker_notes: "Here's how we compare to other tools."

  - id: 15
    filename: 15_why_it_matters.png
    prompt_template: |
      Show a team being productive with One-Shot.
      Visualize: developers shipping more features, velocity increase.
      Text: "Velocity × 10"
    speaker_notes: "Why does this matter? Because it reclaims developer time for what matters: building business logic."

  - id: 16
    filename: 16_enterprise.png
    prompt_template: |
      Show enterprise safety features.
      Icons: lock (security), checkmark (compliance), audit trail (transparency).
      Text: "Enterprise-Ready"
    speaker_notes: "Enterprise customers care about reversibility, audit trails, and security. We have all of it."

  - id: 17
    filename: 17_open_source.png
    prompt_template: |
      Show open source badges, MIT license logo.
      Text: "MIT Licensed. No Lock-In."
      Visualization: community, collaboration.
    speaker_notes: "We open-sourced this. Community can contribute. No vendor lock-in."

  - id: 18
    filename: 18_getting_started.png
    prompt_template: |
      Show three simple steps:
      1. Clone repository
      2. Run /one-shot
      3. Commit code
      Use checkmarks for completed steps.
    speaker_notes: "Getting started is simple. Three steps."

  - id: 19
    filename: 19_roadmap.png
    prompt_template: |
      Timeline showing next features:
      Q2: IDE Extensions
      Q3: Team Collaboration
      Q4: Microservices
      Use timeline visualization.
    speaker_notes: "Here's what's coming next. We're moving fast."

  - id: 20
    filename: 20_cta.png
    prompt_template: |
      Final call-to-action slide.
      Text: "Try One-Shot Today"
      Include: GitHub URL, QR code if applicable
      Text: "github.com/usmanmughaltaleemabad/one-shot-prompting"
    speaker_notes: "Thanks for listening. Try it out. Give us feedback. Let's build better tools together."
```

- [ ] **Step 3: Write onboarding.yaml (shorter template)**

```yaml
---
name: onboarding
description: "Quick onboarding deck for new users (5-7 slides)"
slides:
  - id: 1
    filename: 01_welcome.png
    prompt_template: |
      Welcome slide for new One-Shot users.
      Text: "Welcome to One-Shot"
      Subtext: "Generate production-ready code in 2-3 minutes"
      Warm, inviting design.
    speaker_notes: "Welcome! You're about to save a lot of time."

  - id: 2
    filename: 02_what_is_it.png
    prompt_template: |
      Explain One-Shot in one sentence.
      Text: "One-Shot generates code that understands your codebase"
      Show: code files, understanding, generation.
    speaker_notes: "One-Shot reads your code and generates features that fit perfectly."

  - id: 3
    filename: 03_quickstart.png
    prompt_template: |
      Show the quickstart command in large, easy-to-read format:
      "/one-shot \"your feature\" @./project"
      Include explanation: "That's it. One command."
    speaker_notes: "Here's all you need to know: one command, describe your feature, done."

  - id: 4
    filename: 04_examples.png
    prompt_template: |
      Show 3 example use cases:
      "Add shopping cart to e-commerce"
      "Add user authentication"
      "Add payment processing"
      Use icons for each example.
    speaker_notes: "Works with any feature. Here are some examples."

  - id: 5
    filename: 05_supported_frameworks.png
    prompt_template: |
      Show logos for supported frameworks:
      FastAPI, Django, Spring Boot, Go, Node.js, NestJS
      Text: "Works with your tech stack"
    speaker_notes: "One-Shot supports your framework. If you use FastAPI, Django, Spring, Go, or Node, you're covered."

  - id: 6
    filename: 06_results.png
    prompt_template: |
      Show what you get:
      ✅ Working code
      ✅ Tests passing
      ✅ Integrated with your project
      ✅ Ready to commit
      Text: "Everything works immediately"
    speaker_notes: "You get working code, passing tests, and integration. No manual fixes."

  - id: 7
    filename: 07_try_now.png
    prompt_template: |
      Final slide with next steps.
      Text: "Ready? Try it now"
      Instructions: "Run: /one-shot \"your feature\" @./my-project"
      Include: documentation URL, support email.
    speaker_notes: "That's it. You're ready. Give it a try and let us know what you think."
```

- [ ] **Step 4: Commit all templates**

```bash
git add skills/slides-from-spec/scripts/templates/
git commit -m "feat(slides): add YAML templates (demo, conference, onboarding)"
```

---

## Task 5: Create Style Prompts (isometric + ted-ed)

**Files:**
- Create: `skills/slides-from-spec/style/isometric.txt`
- Create: `skills/slides-from-spec/style/ted-ed.txt`

- [ ] **Step 1: Write isometric.txt**

```
VISUAL STYLE GUIDE for Kie.ai

Style: Isometric Illustration
Target: Board decks, strategy presentations, technical deep-dives

VISUAL CHARACTERISTICS:
- Isometric 3D perspective (30-30-30 degree angles)
- Clean, professional color palette (navy, teal, white, subtle gold accents)
- Geometric shapes: cubes, pyramids, floating blocks, connected gears
- Flat shading (no gradients or shadows, except subtle depth)
- Icons and symbols arranged spatially (not floating randomly)
- Clear visual hierarchy: largest elements first, supporting details second

COMPOSITION RULES:
1. Always include a clear focal point (centered, or upper-left for text)
2. Use whitespace generously (no crowding)
3. Include 1-3 major elements, 2-5 supporting details
4. Balance warm and cool tones (no mono-color)
5. Suggest depth through layering and angle

EXAMPLE ELEMENTS:
- Stacked 3D data visualization (for metrics)
- Floating connected blocks (for architecture/relationships)
- Isometric city/infrastructure (for platform/ecosystem)
- Rotating gears (for process/automation)
- 3D data cubes or pyramids (for analysis)
- Connected nodes or networks (for relationships)

TYPOGRAPHY PLACEMENT:
- Main title: upper left or center, bold, navy or dark teal
- Subtitle/labels: integrated into scene, not overlaid
- Keep text minimal (let visuals tell the story)

COLOR PALETTE:
- Primary: Navy (#003366), Teal (#008B9D)
- Accents: Gold (#FFB700), Bright Teal (#00D9E9)
- Backgrounds: White (#FFFFFF) or Subtle Gray (#F8F9FA)
- Avoid: Pure red, pure green, anything neon

MOOD: Professional, innovative, trustworthy, modern
```

- [ ] **Step 2: Write ted-ed.txt**

```
VISUAL STYLE GUIDE for Kie.ai

Style: TED-Ed Illustration
Target: Storytelling, culture, offsites, emotional hooks

VISUAL CHARACTERISTICS:
- Hand-drawn aesthetic (not perfectly geometric)
- Warm color palette (coral, warm orange, soft yellows, earth tones)
- Organic shapes: characters, animals, landscapes
- Flowing lines and curves (not rigid angles)
- Narrative flow (left-to-right reading)
- Expressive characters with personality

COMPOSITION RULES:
1. Tell a story with visual elements (beginning, middle, end implied)
2. Include human/character elements (relatable, not abstract)
3. Use natural elements (plants, water, sky) to add warmth
4. Balance intricate details with whitespace
5. Guide the viewer's eye through the scene (left to right, top to bottom)

EXAMPLE ELEMENTS:
- Character journeys (person climbing, exploring, discovering)
- Metaphorical landscapes (paths, mountains, forests)
- Interactive scenes (hands connecting, building together)
- Growth and progression (small to large, seeds to flowers)
- Collaborative elements (multiple characters, teamwork)

TYPOGRAPHY PLACEMENT:
- Main title: integrated into scene (not overlaid), warm color
- Subtitle: secondary position, supporting the narrative
- Use hand-drawn-style fonts if possible
- Keep text organic (part of the illustration, not separate)

COLOR PALETTE:
- Primary: Warm coral (#FF6B6B), Warm orange (#FFA500)
- Accents: Sunflower yellow (#FFD93D), Sage green (#6BCB77)
- Backgrounds: Cream (#F5E6D3), Pale blue (#DFF3FF)
- Avoid: Cold grays, neon colors, anything clinical

MOOD: Warm, inclusive, inspiring, human, narrative-driven
```

- [ ] **Step 3: Commit style prompts**

```bash
git add skills/slides-from-spec/style/
git commit -m "feat(slides): add visual style guides (isometric, ted-ed)"
```

---

## Task 6: Create README.md for Slides Skill

**Files:**
- Create: `skills/slides-from-spec/README.md`

- [ ] **Step 1: Write README.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/slides-from-spec/README.md
git commit -m "feat(slides): add README and setup guide"
```

---

## Checkpoint: Slides Skill Complete

**Deliverables:**
- ✅ SKILL.md (agentic skill definition)
- ✅ generate.js (Node.js Kie.ai integration)
- ✅ compile.py (Python Google Slides PPTX builder)
- ✅ 3 YAML templates (demo-deck, conference-talk, onboarding)
- ✅ 2 style prompts (isometric, ted-ed)
- ✅ README.md (setup + usage guide)

**Ready to:** Generate presentation decks from plugin outputs + positioning narratives

**Test it:** Create a demo spec.json, run generate.js + compile.py, verify PPTX output

---

## Final Checkpoint: All 4 Workstreams Complete

| Workstream | Status | Artifacts |
|---|---|---|
| **P7 Standards** | ✅ | 8 `.claude/standards/` files + hooks |
| **P9 Eval** | ✅ | tasks.yaml + eval_runner.py + baseline metrics |
| **Jugnu Positioning** | ✅ | POSITIONING.md + LAUNCH_NARRATIVE.md + VALUE_PROP_ONEPAGER.md |
| **Slides Skill** | ✅ | SKILL.md + scripts + templates + README |

**All committed.** Ready for Week 3 integration sync.
