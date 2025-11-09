# ADT Cuaderno 3 HTML Style Guide

Reference pages: 9_0_adt.html, 9_1_adt.html, 13_0_adt.html, 16_0_adt.html, 19_0_adt.html, 20_0_adt.html, 21_1_adt.html, 25_0_adt.html

## Layout Shell
- `body`: `bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg`
- Sticky elements: include `<div id="interface-container"></div>` and `<div id="nav-container"></div>` directly after `<body>`
- Page wrapper: `flex justify-center items-start min-h-[calc(100dvh-100px)]`
- Content container: `container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12` with `id="content"`

```html
<body class="bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg">
  <div id="interface-container"></div>
  <div id="nav-container"></div>
  <div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">
    <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">
      <!-- section content -->
    </div>
  </div>
</body>
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

## Imagery & Media
- Standard image: `class="w-full max-w-sm rounded-lg"`
- Split layout: `flex flex-col md:flex-row gap-4 md:items-center`
- Framed image: `border border-gray-300 p-3 shadow-lg`
- Always include descriptive `alt` and `aria-label`

```html
<img src="./images/25_img-0.jpg" alt="Imagen: El sol." class="block max-w-full md:w-1/2 border border-gray-300 p-3 shadow-lg" />
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
- When inventing new strings, generate a unique `data-id` starting with `activity_gen_<section_id>_` and reuse it only once per page
- Provide meaningful `aria-label` for images and interactive areas

## Reusable Section Templates

### Narrative/Text Section (NO backgrounds)
```html
<section role="article" data-section-type="text_and_images">
  <h1 class="text-5xl font-bold mb-4 text-amber-700">Los Biomas</h1>
  
  <!-- Regular text paragraphs - NO background color -->
  <p class="mb-4">
    <span data-id="text-13-1">La vida en nuestro planeta depende de la energía del sol.</span>
    <span data-id="text-13-2">Pero no todas las regiones del mundo poseen las mismas condiciones.</span>
  </p>
  
  <img src="./images/example.svg" alt="Descripción" class="w-full max-w-sm rounded-lg" data-id="img-13-0" />
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
