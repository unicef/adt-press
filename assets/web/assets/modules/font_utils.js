/**
 * @module font_utils
 * @description
 * Utilities for dynamically loading and applying custom fonts.
 */

/**
 * Dynamically loads the Atkinson Hyperlegible font from Google Fonts,
 * injects the necessary <link> tags for preconnect and stylesheet,
 * and applies the font to the entire document and common elements.
 *
 * This function is idempotent but will append new <link> and <style> tags
 * each time it is called, so it should only be called once per page load.
 */
export const loadAtkinsonFont = () => {
    const fontHref = 'https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap';
    const styleId = 'atkinson-hyperlegible-style';

    if (!document.querySelector(`link[href="${fontHref}"]`)) {
        // Create and load the preconnect links
        const gFontsPreconnect = document.createElement('link');
        gFontsPreconnect.rel = 'preconnect';
        gFontsPreconnect.href = 'https://fonts.googleapis.com';
        
        const gStaticPreconnect = document.createElement('link');
        gStaticPreconnect.rel = 'preconnect';
        gStaticPreconnect.href = 'https://fonts.gstatic.com';
        gStaticPreconnect.crossOrigin = 'anonymous';
        
        // Create and load the font stylesheet
        const fontStylesheet = document.createElement('link');
        fontStylesheet.rel = 'stylesheet';
        fontStylesheet.href = fontHref;
        
        // Append elements to document head
        document.head.appendChild(gFontsPreconnect);
        document.head.appendChild(gStaticPreconnect);
        document.head.appendChild(fontStylesheet);
    }

    if (!document.getElementById(styleId)) {
        const styleSheet = document.createElement('style');
        styleSheet.id = styleId;
        styleSheet.textContent = `
            body, p, h1, h2, h3, h4, h5, h6, span, div, button, input, textarea, select {
                font-family: "Atkinson Hyperlegible", sans-serif !important;
            }
        `;
        document.head.appendChild(styleSheet);
    }
};