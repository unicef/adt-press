# ADT Style Guide - STRICT RULES

## CRITICAL TEXT RULES
- ❌ **NO TEXT DUPLICATION** - Each data-id must appear exactly ONCE
- ❌ **NO TEXT MODIFICATION** - Use exact text provided, do not rephrase
- ❌ **NO FAKE HEADINGS** - Only use `<h1>` for text with type `section_heading`
- ✅ Text type `section_heading` → `<h1>`
- ✅ Text type `section_text` → `<p>`
- ✅ All other text types → `<p>`

## FORBIDDEN ELEMENTS (NEVER USE THESE)
- ❌ NO gradient backgrounds (`bg-gradient-*`)
- ❌ NO blur effects (`blur-*`)
- ❌ NO decorative shapes or circles
- ❌ NO `absolute` positioned decorative elements
- ❌ NO decorative dividers or separators
- ❌ NO `aria-hidden="true"` decorative elements
- ❌ NO colored container backgrounds (keep `bg-white`)
- ❌ NO shadow effects except `shadow-sm` on images

## EXACT CONTAINER STRUCTURE (USE THIS EXACTLY)
Every page MUST use this exact structure with no modifications:

```html
<div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">
  <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">
    <section data-section-type="[TYPE]" role="article">
      <!-- Content here -->
    </section>
  </div>
</div>
```

## TEXT SIZES (MANDATORY - NO EXCEPTIONS)
| Element | Class | Required |
|---------|-------|----------|
| H1 heading | `text-5xl font-bold mb-4 text-amber-700` | Yes |
| H2 heading | `text-2xl font-bold mb-4 text-amber-700` | Yes |
| Instruction | `text-xl mb-8` | Yes |
| Paragraph | `text-lg text-gray-900 leading-relaxed mb-4` | Yes |
| Caption | `text-sm text-gray-600` | Yes |

## PARAGRAPH STRUCTURE (EXACT FORMAT)
All paragraphs MUST follow this exact pattern:

```html
<p class="text-lg text-gray-900 leading-relaxed mb-4">
  <span data-id="txt_xxx">Text content here.</span>
</p>
```

Or for multiple text spans:
```html
<p class="text-lg text-gray-900 leading-relaxed mb-4">
  <span data-id="txt_xxx">First sentence.</span>
  <span data-id="txt_yyy">Second sentence.</span>
</p>
```

## HEADING STRUCTURE (EXACT FORMAT)
```html
<h1 class="text-5xl font-bold mb-4 text-amber-700" data-id="txt_xxx">Heading Text</h1>
```

## IMAGE STRUCTURE (EXACT FORMAT)
Images must use this exact structure:

```html
<div class="my-6">
  <img
    src="images/xxx.jpg"
    data-id="img_xxx"
    alt="Description"
    class="w-full max-w-md mx-auto rounded-lg shadow-sm"
  />
</div>
```

For image with caption:
```html
<figure class="my-6">
  <img
    src="images/xxx.jpg"
    data-id="img_xxx"
    alt="Description"
    class="w-full max-w-md mx-auto rounded-lg shadow-sm"
  />
  <figcaption class="text-sm text-gray-600 text-center mt-2" data-id="txt_xxx">
    Caption text
  </figcaption>
</figure>
```

## TEXT + IMAGE LAYOUTS

### Image on right:
```html
<div class="flex flex-col md:flex-row gap-6 items-start">
  <div class="flex-1">
    <p class="text-lg text-gray-900 leading-relaxed mb-4">
      <span data-id="txt_xxx">Text content.</span>
    </p>
  </div>
  <div class="md:w-1/3">
    <img src="images/xxx.jpg" data-id="img_xxx" alt="Description" class="w-full rounded-lg shadow-sm" />
  </div>
</div>
```

### Image on left:
```html
<div class="flex flex-col md:flex-row gap-6 items-start">
  <div class="md:w-1/3">
    <img src="images/xxx.jpg" data-id="img_xxx" alt="Description" class="w-full rounded-lg shadow-sm" />
  </div>
  <div class="flex-1">
    <p class="text-lg text-gray-900 leading-relaxed mb-4">
      <span data-id="txt_xxx">Text content.</span>
    </p>
  </div>
</div>
```

## COMPLETE EXAMPLE - TEXT AND IMAGE SECTION
```html
<div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">
  <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">
    <section data-section-type="text_and_images" role="article">
      <h1 class="text-5xl font-bold mb-4 text-amber-700" data-id="txt_p1_g0_t0">
        Chapter Title
      </h1>

      <div class="flex flex-col md:flex-row gap-6 items-start">
        <div class="flex-1">
          <p class="text-lg text-gray-900 leading-relaxed mb-4">
            <span data-id="txt_p1_g1_t0">First paragraph of text.</span>
          </p>
          <p class="text-lg text-gray-900 leading-relaxed mb-4">
            <span data-id="txt_p1_g1_t1">Second paragraph of text.</span>
          </p>
        </div>
        <div class="md:w-1/3">
          <img src="images/img_p1_r0.jpg" data-id="img_p1_r0" alt="Description" class="w-full rounded-lg shadow-sm" />
        </div>
      </div>
    </section>
  </div>
</div>
```

## COMPLETE EXAMPLE - TEXT ONLY SECTION
```html
<div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">
  <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">
    <section data-section-type="text_only" role="article">
      <h1 class="text-5xl font-bold mb-4 text-amber-700" data-id="txt_p1_g0_t0">
        Chapter Title
      </h1>

      <p class="text-lg text-gray-900 leading-relaxed mb-4">
        <span data-id="txt_p1_g1_t0">First paragraph.</span>
      </p>

      <p class="text-lg text-gray-900 leading-relaxed mb-4">
        <span data-id="txt_p1_g1_t1">Second paragraph.</span>
      </p>
    </section>
  </div>
</div>
```

## RULES SUMMARY
1. Use ONLY the exact classes specified above
2. NO decorative elements of any kind
3. Container is ALWAYS `bg-white`
4. ALL paragraphs use `text-lg text-gray-900 leading-relaxed mb-4`
5. ALL headings use `text-amber-700`
6. Images use `rounded-lg shadow-sm` only
7. Keep layouts simple: single column or simple 2-column flex
