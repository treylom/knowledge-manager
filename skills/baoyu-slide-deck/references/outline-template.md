# Outline Template

Standard structure for slide deck outlines with style instructions.

## Outline Format

```markdown
# Slide Deck Outline

**Topic**: [topic description]
**Style**: [selected style]
**Audience**: [target audience]
**Language**: [output language]
**Slide Count**: N slides
**Generated**: YYYY-MM-DD HH:mm

---

<STYLE_INSTRUCTIONS>
Design Aesthetic: [2-3 sentence description from style file]

Background:
  Color: [Name] ([Hex])
  Texture: [description]

Typography:
  Primary Font: [detailed description for image generation]
  Secondary Font: [detailed description for image generation]

Color Palette:
  Primary Text: [Name] ([Hex]) - [usage]
  Background: [Name] ([Hex]) - [usage]
  Accent 1: [Name] ([Hex]) - [usage]
  Accent 2: [Name] ([Hex]) - [usage]

Visual Elements:
  - [element 1 with rendering guidance]
  - [element 2 with rendering guidance]
  - ...

Style Rules:
  Do: [guidelines from style file]
  Don't: [anti-patterns from style file]
</STYLE_INSTRUCTIONS>

---

[Slide entries follow...]
```

## Cover Slide Template

```markdown
## Slide 1 of N

**Type**: Cover
**Filename**: 01-slide-cover.png

// NARRATIVE GOAL
[What this slide achieves in the story arc]

// KEY CONTENT
Headline: [main title]
Sub-headline: [supporting tagline]

// VISUAL
[Detailed visual description - specific elements, composition, mood]

// LAYOUT
[Composition, hierarchy, spatial arrangement]
```

## Content Slide Template

```markdown
## Slide X of N

**Type**: Content
**Filename**: {NN}-slide-{slug}.png

// NARRATIVE GOAL
[What this slide achieves in the story arc]

// KEY CONTENT
Headline: [main message - narrative, not label]
Sub-headline: [supporting context]
Body:
- [point 1 with specific detail]
- [point 2 with specific detail]
- [point 3 with specific detail]

// VISUAL
[Detailed visual description]

// LAYOUT
[Composition, hierarchy, spatial arrangement]
```

## Back Cover Slide Template

```markdown
## Slide N of N

**Type**: Back Cover
**Filename**: {NN}-slide-back-cover.png

// NARRATIVE GOAL
[Meaningful closing - not just "thank you"]

// KEY CONTENT
Headline: [memorable closing statement or call-to-action]
Body: [optional summary points or next steps]

// VISUAL
[Visual that reinforces the core message]

// LAYOUT
[Clean, impactful composition]
```

## STYLE_INSTRUCTIONS Block

The `<STYLE_INSTRUCTIONS>` block contains all style-specific guidance for image generation:

| Section | Content |
|---------|---------|
| Design Aesthetic | Overall visual direction from style file |
| Background | Base color and texture details |
| Typography | Font descriptions for Gemini (no font names, describe appearance) |
| Color Palette | Named colors with hex codes and usage guidance |
| Visual Elements | Specific graphic elements with rendering instructions |
| Style Rules | Do/Don't guidelines from style file |

**Important**: Typography descriptions must describe the visual appearance (e.g., "rounded sans-serif", "bold geometric") since image generators cannot use font names.

## Section Dividers

Use `---` (horizontal rule) between:
- Header metadata and STYLE_INSTRUCTIONS
- STYLE_INSTRUCTIONS and first slide
- Each slide entry

## Slide Numbering

- Cover is always Slide 1
- Content slides use sequential numbers
- Back Cover is always final slide (N)
- Filename prefix matches slide position: `01-`, `02-`, etc.

## Filename Slugs

Generate meaningful slugs from slide content:

| Slide Type | Slug Pattern | Example |
|------------|--------------|---------|
| Cover | `cover` | `01-slide-cover.png` |
| Content | `{topic-slug}` | `02-slide-problem-statement.png` |
| Back Cover | `back-cover` | `10-slide-back-cover.png` |

Slug rules:
- Kebab-case (lowercase, hyphens)
- Derived from headline or main topic
- Maximum 30 characters
- Unique within deck
