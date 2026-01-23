# ADT Generic HTML Style Guide# ADT Generic HTML Style Guide
## Design Principles## Layout Shell

Generate clean, modern, education-friendly HTML pages with:- `body`: `bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg`

- **Blue headings** for clear hierarchy and professional appearance- Sticky elements: include `<div id="interface-container"></div>` and `<div id="nav-container"></div>` directly after `<body>`

- **Black body text** for optimal readability- Page wrapper: `flex justify-center items-start min-h-[calc(100dvh-100px)]`

- **White backgrounds** for clean, distraction-free reading- Content container: `container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12` with `id="content"`

- **Consistent spacing** for organized, scannable content

- **Accessible design** following WCAG guidelines```html

<body class="bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg">

## Layout Shell  <div id="interface-container"></div>

- `body`: `bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg`  <div id="nav-container"></div>

- Sticky elements: include `<div id="interface-container"></div>` and `<div id="nav-container"></div>` directly after `<body>`  <div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">

- Page wrapper: `flex justify-center items-start min-h-[calc(100dvh-100px)]`    <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">

- Content container: `container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12` with `id="content"`      <!-- section content -->

    </div>

```html  </div>

<body class="bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg"></body>

  <div id="interface-container"></div>```

  <div id="nav-container"></div>

  <div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">## Headings & Intro Text

    <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">- Primary heading (H1): `text-5xl font-bold mb-4 text-amber-700`

      <!-- section content -->- Secondary heading (H2 if needed): `text-2xl font-bold mb-4 text-amber-500`

    </div>- Instruction line: `text-xl mb-8` and prepend `<i class="fas fa-pen-to-square text-blue-700 mr-2"></i>` or `<i class="fas fa-book text-blue-700 mr-2"></i>`

  </div>

</body>```html

```<h1 class="text-5xl font-bold mb-4 text-amber-700">El orden de la historia</h1>

<p class="text-xl mb-8">

## Typography  <i class="fas fa-pen-to-square text-blue-700 mr-2"></i>

  <span>Elige las expresiones de cada columna para formar enunciados.</span>

### Headings</p>

- **Primary heading (H1)**: `text-5xl font-bold mb-6 text-blue-600` - main page title```

- **Secondary heading (H2)**: `text-3xl font-bold mb-4 text-blue-500` - section titles

- **Tertiary heading (H3)**: `text-2xl font-semibold mb-3 text-blue-400` - subsection titles## Regular Text (Narrative & Section Content)

- Use blue shades (`blue-600`, `blue-500`, `blue-400`) for visual hierarchy- **NO background color** - Regular narrative paragraphs and section text should have NO highlight/background

- Use plain `<p class="mb-4">` with `<span data-id="...">` children for text blocks

```html- Text color is default (black/gray-900) - readable on white background

<h1 class="text-5xl font-bold mb-6 text-blue-600">Main Page Title</h1>

<h2 class="text-3xl font-bold mb-4 text-blue-500">Section Title</h2>```html

<h3 class="text-2xl font-semibold mb-3 text-blue-400">Subsection Title</h3><p class="mb-4">

```  <span data-id="text-13-1">La vida en nuestro planeta depende de la energía del sol.</span>

  <span data-id="text-13-2">Pero no todas las regiones del mundo poseen las mismas condiciones.</span>

### Body Text</p>

- **Regular paragraphs**: `mb-4 text-gray-900` - black text, clear spacing```

- **Instruction text**: `text-xl mb-6 text-gray-800` - slightly larger for emphasis

- **Icon prefix**: Use `<i class="fas fa-pen-to-square text-blue-600 mr-2"></i>` or `<i class="fas fa-book text-blue-600 mr-2"></i>` for activity instructions## Highlighted Text Blocks & Callouts

**ONLY use background colors for special callout boxes, NOT regular section text:**

```html- Info card (e.g., "Recuerda que..."): `bg-amber-50 p-4 rounded-lg text-amber-900 shadow-sm`

<p class="mb-4 text-gray-900">- Instruction boxes: `bg-amber-50 p-4 rounded-lg`

  <span data-id="text-13-1">Regular body text with optimal readability.</span>- Special highlight tiles (grids): `bg-amber-50 p-3 rounded-md text-center font-medium`

</p>

```html

<p class="text-xl mb-6 text-gray-800"><!-- ONLY for special callout boxes -->

  <i class="fas fa-pen-to-square text-blue-600 mr-2"></i><div class="bg-amber-50 p-4 rounded-lg text-amber-900 shadow-sm">

  <span data-id="inst-1">Activity instruction text.</span>  <p class="text-lg"><span data-id="text-x">Recuerda que...</span></p>

</p></div>

``````



## Regular Text & Content Sections## Forms & Inputs

- **NO background colors on regular text** - keep backgrounds white for clarity- Inline label/input row: `flex gap-2 items-center` with input `grow p-2 border border-gray-300 rounded`

- Use clean spacing with consistent `mb-4` or `mb-6` between paragraphs- Stacked grid: `grid grid-cols-1 gap-6` and labels `font-semibold whitespace-nowrap`

- Text is black/dark gray (`text-gray-900`) on white background for maximum readability- Radio cards: `flex items-center p-4 border-2 border-green-50 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 [&:has(:checked)]:bg-green-200 [&:has(:checked)]:border-green-400`

- Text inputs in cards (checkbox/radio hidden): use `class="sr-only"` on `<input type="radio">`

```html

<div class="space-y-4">```html

  <p class="mb-4 text-gray-900"><div class="flex gap-2 items-center">

    <span data-id="text-1">First paragraph of content.</span>  <label class="block font-semibold">Mis amigos me quieren porque</label>

  </p>  <input class="grow p-2 border border-gray-300 rounded" type="text" placeholder="Respuesta..." />

  <p class="mb-4 text-gray-900"></div>

    <span data-id="text-2">Second paragraph with clear spacing.</span>```

  </p>

</div>## Interactive Elements

```- Draggable token: `activity-item` base with `cursor-move` and color-coded backgrounds (`bg-yellow-100`, `bg-teal-100`, `bg-green-100`)

- Dropzone: `flex gap-4 items-center border border-gray-300 p-2 pl-4 rounded-lg min-h-[62px]`

## Callout Boxes & Highlighted Content- Word chips: `bg-gray-100 p-2 px-4 rounded-full inline-block`

**Only use colored backgrounds for special callout boxes that need emphasis:**- Auto-fill span: `<span data-id="..." data-fill="storage-key"></span>` and populate via JavaScript on `DOMContentLoaded`

- Info/tip box: `bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg mb-6`

- Warning/note: `bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg mb-6````html

- Success/example: `bg-green-50 border-l-4 border-green-500 p-4 rounded-lg mb-6`<div class="activity-item bg-teal-100 p-2 rounded-md shadow-sm text-center cursor-move" data-activity-item="text-19-6" draggable="true">

  corrió

```html</div>

<!-- Info callout box --><div class="flex gap-4 items-center dropzone border border-gray-300 p-2 pl-4 rounded-lg min-h-[62px]" id="dropzone-1">

<div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg mb-6">  <p class="text-lg font-bold">1.</p>

  <p class="font-semibold text-blue-700 mb-2">Remember:</p>  <div role="region" class="flex flex-wrap justify-center gap-2"></div>

  <p class="text-gray-800"><span data-id="text-x">Important information here.</span></p></div>

</div>```

```

## Imagery & Media

## Forms & Inputs- Standard image: `class="w-full max-w-sm rounded-lg"`

- Inline label/input row: `flex gap-2 items-center mb-4`- Split layout: `flex flex-col md:flex-row gap-4 md:items-center`

- Input fields: `grow p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none`- Framed image: `border border-gray-300 p-3 shadow-lg`

- Labels: `font-semibold text-gray-800`- Always include descriptive `alt` and `aria-label`

- Radio/checkbox cards: `flex items-center p-4 border-2 border-gray-200 bg-white rounded-lg cursor-pointer hover:border-blue-300 hover:bg-blue-50 [&:has(:checked)]:bg-blue-100 [&:has(:checked)]:border-blue-500`

```html

```html<img src="./images/25_img-0.jpg" alt="Imagen: El sol." class="block max-w-full md:w-1/2 border border-gray-300 p-3 shadow-lg" />

<div class="flex gap-2 items-center mb-4">```

  <label class="font-semibold text-gray-800" for="answer-1">Your answer:</label>

  <input id="answer-1" class="grow p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none" type="text" placeholder="Type here..." />## Color Palette (Tailwind classes)

</div>- Primary text accent: `text-amber-700`

- Secondary accent: `text-amber-500`

<!-- Radio card -->- Instruction icon: `text-blue-700`

<label class="flex items-center p-4 border-2 border-gray-200 bg-white rounded-lg cursor-pointer hover:border-blue-300 hover:bg-blue-50 [&:has(:checked)]:bg-blue-100 [&:has(:checked)]:border-blue-500">- Highlight backgrounds: `bg-amber-50`, `bg-yellow-100`, `bg-teal-100`, `bg-green-50`, `bg-green-100`, `bg-green-200`

  <input type="radio" name="choice" class="sr-only" />- Neutral surfaces: `bg-white`, `border-gray-300`, `bg-gray-100`

  <span class="text-gray-900">Option text</span>

</label>## Accessibility & Semantics

```- Maintain `role` attributes (`role="activity"`, `role="article"`, `role="region"`) and `aria-*` IDs for state sync

- Preserve `data-id`, `data-aria-id`, `data-activity-item`, `data-fill`, and `data-section-type` values for application logic

## Interactive Elements- When inventing new strings, generate a unique `data-id` starting with `activity_gen_<section_id>_` and reuse it only once per page

- Draggable tokens: `cursor-move bg-blue-100 border border-blue-300 p-2 px-4 rounded-lg shadow-sm hover:shadow-md`- Provide meaningful `aria-label` for images and interactive areas

- Dropzones: `border-2 border-dashed border-gray-300 p-4 rounded-lg min-h-[80px] bg-gray-50`

- Buttons: `bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-300`## Reusable Section Templates

- Word chips: `bg-gray-100 border border-gray-300 px-3 py-1 rounded-full inline-block`

### Narrative/Text Section (NO backgrounds)

```html```html

<div class="cursor-move bg-blue-100 border border-blue-300 p-2 px-4 rounded-lg shadow-sm hover:shadow-md" data-activity-item="item-1" draggable="true"><section role="article" data-section-type="text_and_images">

  Draggable item  <h1 class="text-5xl font-bold mb-4 text-amber-700">Los Biomas</h1>

</div>  

  <!-- Regular text paragraphs - NO background color -->

<div class="border-2 border-dashed border-gray-300 p-4 rounded-lg min-h-[80px] bg-gray-50 dropzone" id="drop-1">  <p class="mb-4">

  <div role="region" class="flex flex-wrap gap-2"></div>    <span data-id="text-13-1">La vida en nuestro planeta depende de la energía del sol.</span>

</div>    <span data-id="text-13-2">Pero no todas las regiones del mundo poseen las mismas condiciones.</span>

  </p>

<button class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-300">  

  Submit  <img src="./images/example.svg" alt="Descripción" class="w-full max-w-sm rounded-lg" data-id="img-13-0" />

</button></section>

``````



## Imagery & Media### Activity Section (WITH callout boxes)

- Standard image: `w-full max-w-md rounded-lg shadow-md````html

- Split layout (text + image): `flex flex-col md:flex-row gap-6 items-center`<section role="activity" data-section-type="activity_open_ended_answer">

- Image with caption: Wrap in `<figure>` with `<figcaption class="text-sm text-gray-600 mt-2 text-center">`  <h1 class="text-5xl font-bold mb-4 text-amber-700">Título</h1>

- Always include descriptive `alt` attributes  <p class="text-xl mb-8">

    <i class="fas fa-pen-to-square text-blue-700 mr-2"></i>

```html    <span data-id="text-x">Instrucción principal.</span>

<figure class="mb-6">  </p>

  <img src="./images/example.jpg" alt="Descriptive text" class="w-full max-w-md rounded-lg shadow-md" data-id="img-1" />

  <figcaption class="text-sm text-gray-600 mt-2 text-center">  <!-- ONLY use bg-amber-50 for special callout boxes -->

    <span data-id="caption-1">Image caption text</span>  <div class="bg-amber-50 p-4 rounded-lg text-amber-900 shadow-sm mb-6">

  </figcaption>    <p class="text-lg"><span data-id="text-y">Recuerda que...</span></p>

</figure>  </div>



<!-- Split layout -->  <div class="flex gap-2 items-center mb-4">

<div class="flex flex-col md:flex-row gap-6 items-center">    <label class="block font-semibold" for="respuesta">Etiqueta</label>

  <div class="flex-1">    <input id="respuesta" class="grow p-2 border border-gray-300 rounded" type="text" placeholder="Escribe tu respuesta" />

    <p class="mb-4 text-gray-900"><span data-id="text-1">Content text here.</span></p>  </div>

  </div></section>

  <img src="./images/example.jpg" alt="Description" class="w-full md:w-1/2 rounded-lg shadow-md" data-id="img-1" />```

</div>

```Use these guidelines to keep new HTML pages consistent with existing activity and narrative layouts.


## Color Palette (Tailwind classes)
- **Primary (Blue)**: `blue-600`, `blue-500`, `blue-400` - headings, interactive elements
- **Text**: `gray-900`, `gray-800`, `gray-700` - body text hierarchy
- **Backgrounds**: `white`, `gray-50`, `blue-50` - main surfaces, subtle accents
- **Borders**: `gray-300`, `gray-200`, `blue-300` - separators, inputs
- **Accents**: `yellow-50/500`, `green-50/500` - warnings, success states

## Accessibility & Semantics
- Use semantic HTML: `<article>`, `<section>`, `<nav>`, `<main>`, `<aside>`
- Maintain `role` attributes: `role="article"`, `role="activity"`, `role="region"`
- Include ARIA labels: `aria-label`, `aria-labelledby`, `aria-describedby`
- Preserve all `data-*` attributes for application logic: `data-id`, `data-aria-id`, `data-activity-item`, `data-section-type`
- Ensure keyboard navigation support with proper `tabindex`
- Use `sr-only` class for screen-reader-only content: `class="sr-only"`

## Reusable Section Templates

### Narrative/Reading Section
```html
<section role="article" data-section-type="text_and_images">
  <h1 class="text-5xl font-bold mb-6 text-blue-600" data-id="title-1">Chapter Title</h1>
  
  <div class="space-y-4 mb-6">
    <p class="mb-4 text-gray-900">
      <span data-id="text-1">First paragraph of educational content.</span>
    </p>
    <p class="mb-4 text-gray-900">
      <span data-id="text-2">Second paragraph with important information.</span>
    </p>
  </div>
  
  <figure class="mb-6">
    <img src="./images/example.jpg" alt="Educational diagram" class="w-full max-w-md rounded-lg shadow-md" data-id="img-1" />
    <figcaption class="text-sm text-gray-600 mt-2 text-center">
      <span data-id="caption-1">Figure 1: Description</span>
    </figcaption>
  </figure>
</section>
```

### Activity Section with Instructions
```html
<section role="activity" data-section-type="activity_interactive">
  <h1 class="text-5xl font-bold mb-6 text-blue-600" data-id="title-1">Activity Title</h1>
  
  <p class="text-xl mb-6 text-gray-800">
    <i class="fas fa-pen-to-square text-blue-600 mr-2"></i>
    <span data-id="inst-1">Complete the following exercises.</span>
  </p>

  <!-- Info callout box -->
  <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg mb-6">
    <p class="font-semibold text-blue-700 mb-2">Remember:</p>
    <p class="text-gray-800"><span data-id="text-hint">Helpful hint for students.</span></p>
  </div>

  <!-- Input form -->
  <div class="space-y-4">
    <div class="flex gap-2 items-center mb-4">
      <label class="font-semibold text-gray-800" for="answer-1">Question 1:</label>
      <input id="answer-1" class="grow p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none" type="text" placeholder="Your answer..." />
    </div>
  </div>
</section>
```

### Mixed Content Section
```html
<section role="article" data-section-type="mixed_content">
  <h1 class="text-5xl font-bold mb-6 text-blue-600" data-id="title-1">Lesson Title</h1>
  
  <h2 class="text-3xl font-bold mb-4 text-blue-500" data-id="subtitle-1">Section 1</h2>
  
  <!-- Text and image side by side -->
  <div class="flex flex-col md:flex-row gap-6 items-center mb-8">
    <div class="flex-1">
      <p class="mb-4 text-gray-900"><span data-id="text-1">Educational content explaining the concept.</span></p>
      <p class="mb-4 text-gray-900"><span data-id="text-2">Additional details and examples.</span></p>
    </div>
    <img src="./images/example.jpg" alt="Concept illustration" class="w-full md:w-1/2 rounded-lg shadow-md" data-id="img-1" />
  </div>
  
  <h3 class="text-2xl font-semibold mb-3 text-blue-400" data-id="subtitle-2">Key Points</h3>
  <ul class="list-disc list-inside space-y-2 mb-6 text-gray-900">
    <li><span data-id="point-1">First important point</span></li>
    <li><span data-id="point-2">Second important point</span></li>
    <li><span data-id="point-3">Third important point</span></li>
  </ul>
</section>
```

## Best Practices
1. **Consistency**: Use the same heading levels, spacing, and color schemes across all pages
2. **Hierarchy**: Establish clear visual hierarchy with heading sizes and colors
3. **Readability**: Maintain comfortable line lengths (max-w-5xl container) and adequate spacing
4. **Whitespace**: Use generous margins and padding for clean, uncluttered layouts
5. **Responsiveness**: Ensure layouts work on mobile (sm:), tablet (md:), and desktop (lg:) screens
6. **Focus states**: Include visible focus indicators for keyboard navigation
7. **Color contrast**: Ensure text meets WCAG AA standards (4.5:1 ratio minimum)

Use these guidelines to create professional, consistent, and accessible educational content across all generated HTML pages.
