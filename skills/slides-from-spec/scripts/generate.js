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
