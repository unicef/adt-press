# ADT Cuaderno 3 HTML Style Guide

Reference pages: 9_0_adt.html, 9_1_adt.html, 13_0_adt.html, 16_0_adt.html, 19_0_adt.html, 20_0_adt.html, 21_1_adt.html, 25_0_adt.html

## Layout Shell
- The application provides the `<body>` shell plus the persistent `interface-container` and `nav-container` elements.
- Start markup with the page wrapper: `flex justify-center items-start min-h-[calc(100dvh-100px)]`
- Nest the content container inside: `container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12` with `id="content"`

```html
<div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">
  <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">
    <!-- section content -->
  </div>
</div>
```

## Headings & Intro Text
- Primary heading (H1): `text-5xl font-bold mb-4 text-amber-700`
- Secondary heading (H2 if needed): `text-2xl font-bold mb-4 text-amber-500`
- Instruction line: `text-xl mb-8` and prepend `<i class="fas fa-pen-to-square text-blue-700 mr-2"></i>` or `<i class="fas fa-book text-blue-700 mr-2"></i>`

```html
<h1 class="text-5xl font-bold mb-4 text-amber-700">El orden de la historia</h1>
<p class="text-xl mb-8">
  <i class="fas fa-pen-to-square text-blue-700 mr-2"></i>
  <span>Elige las expresiones de cada columna para formar enunciados.</span>
</p>
```

## Regular Text (Narrative & Section Content)
- **NO background color** - Regular narrative paragraphs and section text should have NO highlight/background
- Use plain `<p class="mb-4">` with `<span data-id="...">` children for text blocks
- Text color is default (black/gray-900) - readable on white background

```html
<p class="mb-4">
  <span data-id="text-13-1">La vida en nuestro planeta depende de la energía del sol.</span>
  <span data-id="text-13-2">Pero no todas las regiones del mundo poseen las mismas condiciones.</span>
</p>
```

## Highlighted Text Blocks & Callouts
**ONLY use background colors for special callout boxes, NOT regular section text:**
- Info card (e.g., "Recuerda que..."): `bg-amber-50 p-4 rounded-lg text-amber-900 shadow-sm`
- Instruction boxes: `bg-amber-50 p-4 rounded-lg`
- Special highlight tiles (grids): `bg-amber-50 p-3 rounded-md text-center font-medium`

```html
<!-- ONLY for special callout boxes -->
<div class="bg-amber-50 p-4 rounded-lg text-amber-900 shadow-sm">
  <p class="text-lg"><span data-id="text-x">Recuerda que...</span></p>
</div>
```

## Forms & Inputs
- Inline label/input row: `flex gap-2 items-center` with input `grow p-2 border border-gray-300 rounded`
- Stacked grid: `grid grid-cols-1 gap-6` and labels `font-semibold whitespace-nowrap`
- Radio cards: `flex items-center p-4 border-2 border-green-50 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 [&:has(:checked)]:bg-green-200 [&:has(:checked)]:border-green-400`
- Text inputs in cards (checkbox/radio hidden): use `class="sr-only"` on `<input type="radio">`

```html
<div class="flex gap-2 items-center">
  <label class="block font-semibold">Mis amigos me quieren porque</label>
  <input class="grow p-2 border border-gray-300 rounded" type="text" placeholder="Respuesta..." />
</div>
```

## Interactive Elements
- Draggable token: `activity-item` base with `cursor-move` and color-coded backgrounds (`bg-yellow-100`, `bg-teal-100`, `bg-green-100`)
- Dropzone: `flex gap-4 items-center border border-gray-300 p-2 pl-4 rounded-lg min-h-[62px]`
- Word chips: `bg-gray-100 p-2 px-4 rounded-full inline-block`
- Auto-fill span: `<span data-id="..." data-fill="storage-key"></span>` and populate via JavaScript on `DOMContentLoaded`

```html
<div class="activity-item bg-teal-100 p-2 rounded-md shadow-sm text-center cursor-move" data-activity-item="text-19-6" draggable="true">
  corrió
</div>
<div class="flex gap-4 items-center dropzone border border-gray-300 p-2 pl-4 rounded-lg min-h-[62px]" id="dropzone-1">
  <p class="text-lg font-bold">1.</p>
  <div role="region" class="flex flex-wrap justify-center gap-2"></div>
</div>
```

## Sorting Activity Structure (activity_sorting)
**CRITICAL:** Sorting activities require specific structure for drag-and-drop functionality to work.

### Word Cards (Draggable Items)
Each option MUST be a `<div>` with:
- Class: `word-card` (NOT `activity-item`)
- Attribute: `data-activity-item="unique-id"` (REQUIRED for JS)
- Attribute: `data-id="text-id"` (for content tracking)
- Attribute: `draggable="true"`
- Color-coded backgrounds: `bg-yellow-100`, `bg-teal-100`, `bg-green-100`, `bg-gray-100`

```html
<!-- Word bank with draggable word cards -->
<div class="flex flex-wrap gap-3 mb-6">
  <div class="word-card bg-yellow-100 p-2 px-4 rounded-full cursor-move" 
       data-activity-item="txt_p58_g1_t0" 
       data-id="txt_p58_g1_t0" 
       draggable="true">voz ronca</div>
  <div class="word-card bg-teal-100 p-2 px-4 rounded-full cursor-move" 
       data-activity-item="txt_p58_g1_t1" 
       data-id="txt_p58_g1_t1" 
       draggable="true">prudente</div>
</div>
```

### Categories (Drop Zones)
Each category MUST be a `<div>` with:
- Class: `category` (REQUIRED)
- Attribute: `data-activity-category="category-name"` (REQUIRED for JS)
- Inner structure: `<ul class="word-list"></ul>` (REQUIRED for dropped items)

```html
<!-- Drop zone categories -->
<div class="category border border-gray-300 p-4 rounded-lg min-h-[100px]" 
     data-activity-category="pedrito"
     aria-label="Pedrito">
  <h3 class="font-bold mb-2">Pedrito</h3>
  <ul class="word-list"></ul>
</div>

<div class="category border border-gray-300 p-4 rounded-lg min-h-[100px]" 
     data-activity-category="tigre"
     aria-label="Tigre">
  <h3 class="font-bold mb-2">Tigre</h3>
  <ul class="word-list"></ul>
</div>
```

### Complete Sorting Activity Template
```html
<section role="activity" data-section-type="activity_sorting">
  <h1 class="text-5xl font-bold mb-4 text-amber-700" data-id="text-title">Clasifica las características</h1>
  
  <p class="text-xl mb-8">
    <i class="fas fa-pen-to-square text-blue-700 mr-2"></i>
    <span data-id="text-instruction">Arrastra cada palabra a la categoría correcta.</span>
  </p>

  <!-- Word bank -->
  <div class="mb-6">
    <h2 class="text-xl font-semibold mb-3">Opciones:</h2>
    <div class="flex flex-wrap gap-3">
      <div class="word-card bg-yellow-100 p-2 px-4 rounded-full cursor-move" 
           data-activity-item="word-1" 
           data-id="text-word-1" 
           draggable="true">palabra 1</div>
      <div class="word-card bg-teal-100 p-2 px-4 rounded-full cursor-move" 
           data-activity-item="word-2" 
           data-id="text-word-2" 
           draggable="true">palabra 2</div>
    </div>
  </div>

  <!-- Categories -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="category border border-gray-300 p-4 rounded-lg min-h-[150px]" 
         data-activity-category="category-1">
      <h3 class="font-bold mb-2" data-id="text-cat-1">Categoría 1</h3>
      <ul class="word-list"></ul>
    </div>
    
    <div class="category border border-gray-300 p-4 rounded-lg min-h-[150px]" 
         data-activity-category="category-2">
      <h3 class="font-bold mb-2" data-id="text-cat-2">Categoría 2</h3>
      <ul class="word-list"></ul>
    </div>
  </div>

  <!-- REQUIRED: Feedback element MUST be INSIDE the section -->
  <div class="mt-4 text-center">
    <p id="feedback" class="text-lg" aria-live="polite"></p>
  </div>
</section>
```

**CRITICAL Requirements:**
- Word cards: `word-card` class + `data-activity-item` + `draggable="true"`
- Categories: `category` class + `data-activity-category` + `<ul class="word-list"></ul>`
- **MUST include `<p id="feedback">` element INSIDE the `<section>` tag** for displaying validation results

## Imagery & Media
- **Plain images (NO decorations)** - Images should be displayed cleanly without borders, padding, or shadows
- Standard image: `class="w-full max-w-sm rounded-lg"`
- **Two-column layout** - Use `flex flex-col-reverse md:flex-row gap-4 md:items-center` to show image FIRST on mobile
- Always include descriptive `alt` and `aria-label`

```html
<!-- Plain image - NO borders, padding, or shadows -->
<img src="./images/25_img-0.jpg" alt="Imagen: El sol." class="w-full max-w-sm rounded-lg" data-id="img-25-0" />

<!-- Two-column: Image on right (desktop), Image FIRST (mobile) -->
<div class="flex flex-col-reverse md:flex-row gap-4 md:items-center">
  <!-- Text on left (desktop), appears second on mobile -->
  <div class="flex-1">
    <p class="mb-4"><span data-id="text-13-1">Texto aquí.</span></p>
  </div>
  <!-- Image on right (desktop), appears first on mobile -->
  <img src="./images/example.svg" alt="Descripción" class="w-full md:w-1/2 rounded-lg" data-id="img-13-0" />
</div>
```

## Color Palette (Tailwind classes)
- Primary text accent: `text-amber-700`
- Secondary accent: `text-amber-500`
- Instruction icon: `text-blue-700`
- Highlight backgrounds: `bg-amber-50`, `bg-yellow-100`, `bg-teal-100`, `bg-green-50`, `bg-green-100`, `bg-green-200`
- Neutral surfaces: `bg-white`, `border-gray-300`, `bg-gray-100`

## Accessibility & Semantics
- Maintain `role` attributes (`role="activity"`, `role="article"`, `role="region"`) and `aria-*` IDs for state sync
- Preserve `data-id`, `data-aria-id`, `data-activity-item`, `data-fill`, and `data-section-type` values for application logic
- When creating new translatable text, mint a unique `data-id` prefixed with `activity_gen_<section_id>_…` and never reuse it within a page
- Provide meaningful `aria-label` for images and interactive areas

## Reusable Section Templates

### Narrative/Text Section (NO backgrounds)
```html
<section role="article" data-section-type="text_and_images">
  <h1 class="text-5xl font-bold mb-4 text-amber-700">Los Biomas</h1>
  
  <!-- Two-column layout: image first on mobile -->
  <div class="flex flex-col-reverse md:flex-row gap-4 md:items-center">
    <div class="flex-1">
      <p class="mb-4">
        <span data-id="text-13-1">La vida en nuestro planeta depende de la energía del sol.</span>
        <span data-id="text-13-2">Pero no todas las regiones del mundo poseen las mismas condiciones.</span>
      </p>
    </div>
    <!-- Plain image - NO borders, padding, or shadows -->
    <img src="./images/example.svg" alt="Descripción" class="w-full md:w-1/2 rounded-lg" data-id="img-13-0" />
  </div>
</section>
```

### Activity Section (WITH callout boxes)
```html
<section role="activity" data-section-type="activity_open_ended_answer">
  <h1 class="text-5xl font-bold mb-4 text-amber-700">Título</h1>
  <p class="text-xl mb-8">
    <i class="fas fa-pen-to-square text-blue-700 mr-2"></i>
    <span data-id="text-x">Instrucción principal.</span>
  </p>

  <!-- ONLY use bg-amber-50 for special callout boxes -->
  <div class="bg-amber-50 p-4 rounded-lg text-amber-900 shadow-sm mb-6">
    <p class="text-lg"><span data-id="text-y">Recuerda que...</span></p>
  </div>

  <div class="flex gap-2 items-center mb-4">
    <label class="block font-semibold" for="respuesta">Etiqueta</label>
    <input id="respuesta" class="grow p-2 border border-gray-300 rounded" type="text" placeholder="Escribe tu respuesta" />
  </div>
</section>
```

Use these guidelines to keep new HTML pages consistent with existing activity and narrative layouts.
