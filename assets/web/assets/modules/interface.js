/**
 * @module interface
 * @description
 * UI logic for navigation, sidebar, glossary, language switching, accessibility, and layout adjustments.
 */
import { stopAudio, toggleReadAloud } from './audio.js';
import { getCookie, setCookie } from "./cookies.js";
import { showErrorToast } from "./error_utils.js";
import { setState, state } from "./state.js";
import { fetchTranslations, translateText } from "./translations.js";
import { toggleButtonState, toggleButtonColor } from "./utils.js";
import { populateGlossaryTerms } from './ui_utils.js';
import { stopSLVideo, startSLVideo, toggleBottomContainer } from './video.js';
// Replace previous zoom imports with the new controller functions
import {
  setNativeZoom,
  resetZoom,
  getCurrentZoom,
  applyStoredZoom,
  isHighDpiWindows,
  initializeZoomController,
  createZoomControls
} from './browser_zoom_controller.js';
import { trackToggleEvent } from './analytics.js';
import { toggleNav } from './navigation.js';


let glossaryTerms = {};
let interfaceCache = {
  interface: null,
  navigation: null,
  sidebarState: null,
};

/**
 * Returns the cached sidebar HTML.
 * @returns {string|null} The cached sidebar HTML or null if not cached.
 */
export const getCachedInterface = () => interfaceCache.interface;

/**
 * Returns the cached navigation HTML.
 * @returns {string|null} The cached navigation HTML or null if not cached.
 */
export const getCachedNavigation = () => interfaceCache.navigation;

/**
 * Initializes the sidebar, applies saved state, and attaches listeners.
 * Adds styling and restores open/closed state from cookies.
 */
export const initializeSidebar = () => {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  // Load saved sidebar state
  const savedState = getCookie("sidebarState");
  const stateMode = getCookie("stateMode") === "true";
  const isOpen = savedState === "open";

  // Apply initial state
  if (!stateMode) {
    setSidebarVisibility(isOpen);
  }

  // Ensure proper styling
  sidebar.classList.add(
    "fixed",
    "top-2",
    "w-80",
    "bg-white",
    "shadow-lg",
    "z-70",
    "transform",
    "transition-transform",
    "duration-300",
    "ease-in-out",
    "overflow-y-auto"
  );
  attachSidebarListeners();
};

/**
 * Initializes the navigation popup and applies saved state.
 * Restores open/closed state from cookies.
 */
export const initializeNavigation = () => {
  const navPopup = document.getElementById("navPopup");
  if (!navPopup) return;

  // Load saved navigation state
  const savedState = getCookie("navState");
  const stateMode = getCookie("stateMode") === "true";
  const isOpen = savedState === "open";

  // Apply initial state
  if (!stateMode) {
    if (isOpen) {
      toggleNav(isOpen);
    }
  }
};

/**
 * Attaches listeners to the sidebar for state persistence.
 * @private
 */
const attachSidebarListeners = () => {
  // Save sidebar state before page unload
  window.addEventListener("beforeunload", () => {
    const sidebarState = interfaceCache.sidebarState ? "open" : "closed";
    setCookie("sidebarState", sidebarState, 7);
  });
};

/**
 * Initializes the language dropdown, populates options, and sets current language.
 * Retries initialization if the dropdown is not found immediately.
 * @returns {Promise<boolean>} Resolves true if successful, false otherwise.
 */
export const initializeLanguageDropdown = async () => {
  try {
    // Maximum retry attempts
    const MAX_RETRIES = 3;
    let retryCount = 0;

    const tryInitialize = async () => {
      const dropdown = document.getElementById("language-dropdown");
      if (!dropdown) {
        if (retryCount >= MAX_RETRIES) {
          throw new Error("Language dropdown not found after maximum retries");
        }
        retryCount++;
        console.log(`Language dropdown not found, attempt ${retryCount} of ${MAX_RETRIES}`);
        await new Promise(resolve => setTimeout(resolve, 200));
        return tryInitialize();
      }

      // Once found, clear existing options
      dropdown.innerHTML = '';

      // Get languages from meta tag
      const metaTag = document.querySelector('meta[name="available-languages"]');
      const languages = metaTag ? metaTag.getAttribute("content")?.split(",") : ["es", "en"];

      // Set current language before adding options
      const currentLang = state.currentLanguage ||
        getCookie("currentLanguage") ||
        document.documentElement.lang ||
        "es";

      // Add options for each language, marking currentLang as selected
      languages.forEach(lang => {
        const option = document.createElement("option");
        option.value = lang;
        option.textContent = lang.toUpperCase();
        if (lang === currentLang) {
          option.selected = true;
        }
        dropdown.appendChild(option);
      });

      dropdown.value = currentLang;
      setState("currentLanguage", currentLang);

      // Ensure visibility of dropdown and container
      dropdown.classList.remove('hidden');
      const container = dropdown.closest('.flex.items-center');
      if (container) {
        container.classList.remove('hidden');
        container.style.display = 'flex';
        // Add necessary Tailwind classes
        container.classList.add(
          'flex',
          'items-center',
          'space-x-4',
          'ml-auto',
          'mr-4'
        );
      }

      // Style the dropdown
      dropdown.classList.add(
        'ml-4',
        'p-2',
        'border',
        'border-gray-300',
        'rounded-md',
        'bg-white',
        'text-gray-700'
      );
      // Update the HTML lang attribute to match the selected language
      document.documentElement.lang = currentLang;
      return true;
    };

    return await tryInitialize();

  } catch (error) {
    console.error("Error initializing language dropdown:", error);
    return false; // Return false instead of throwing to prevent cascading failures
  }
};

/**
 * Updates the page number display based on meta tags.
 * Handles special cases for sectioned and non-sectioned pages.
 */
export const updatePageNumber = () => {
  const pageSectionMetaTag = document.querySelector('meta[name="page-section-id"]');
  const pageElement = document.getElementById('page-section-id');

  if (!pageElement) return;
  state.currentPage = pageSectionMetaTag?.getAttribute('content') || '0';

  // Default to page 0 if no meta tag is found
  if (!pageSectionMetaTag) {
    pageElement.innerHTML = '<span data-id="page"></span> 0';
    return;
  }

  const pageSectionContent = pageSectionMetaTag.getAttribute('content');
  if (!pageSectionContent) {
    pageElement.innerHTML = '<span data-id="page"></span> 0';
    return;
  }

  const parts = pageSectionContent.split('_').map(Number);
  let humanReadablePage;

  // Handle special case of page 0
  if (parts[0] === 0 && (!parts[1] || parts[1] === 0)) {
    humanReadablePage = '<span data-id="page"></span> 0';
  }
  // For pages with sections (format "7_0" renders as "6.1")
  else if (parts.length === 2) {
    humanReadablePage = `<span data-id="page"></span> ${parts[0] - 1}.${parts[1] + 1}`;
  }
  // For pages with no section information (format "6" renders as "5")
  else {
    humanReadablePage = `<span data-id="page"></span> ${parts[0] - 1}`;
  }

  pageElement.innerHTML = humanReadablePage;
};

/**
 * Updates the page number display based on meta tags.
 * Handles special cases for sectioned and non-sectioned pages.
 */
export const toggleSidebar = () => {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  // Determine current state
  const isCurrentlyOpen = !sidebar.classList.contains("translate-x-full");

  // Toggle to opposite state
  setSidebarVisibility(!isCurrentlyOpen);

  // Update state
  state.sideBarActive = !isCurrentlyOpen;

  // Adjust layout
  adjustLayout();
};

/**
 * Adjusts layout for sidebar, navigation, and submit button based on state.
 * Applies/removes Tailwind classes to main content and navigation elements.
 */
export const adjustLayout = () => {
  const submitButtonContainer = document.querySelector(".fixed.bottom-0 .container .absolute");
  const navButtons = document.getElementById("back-forward-buttons");
  const mainContent = document.querySelector("body > .container");
  const submitButton = document.getElementById("submit-button");

  // Determine if any panel is active (sidebar or sign language)
  const isPanelActive = state.sideBarActive || state.signLanguageMode;

  // Check if this is an activity page with submit button visible
  const isActivity = submitButton && window.getComputedStyle(submitButton).display !== 'none';

  // Set classes directly based on current state rather than toggling
  if (mainContent) {
    // Remove all relevant classes first
    mainContent.classList.remove("lg:ml-0", "lg:w-[calc(100vw-450px)]", "mx-auto");

    // Apply appropriate classes based on current state
    if (isPanelActive) {
      mainContent.classList.add("lg:ml-0", "lg:w-[calc(100vw-450px)]");
    } else {
      mainContent.classList.add("mx-auto");
    }
  }

  // Adjust the submit button position
  if (submitButtonContainer) {
    // Remove all relevant classes first
    submitButtonContainer.classList.remove("lg:right-0", "lg:right-[calc(425px-1rem)]");

    // Apply appropriate classes based on current state
    if (isPanelActive) {
      submitButtonContainer.classList.add("lg:right-[calc(425px-1rem)]");
    } else {
      submitButtonContainer.classList.add("lg:right-0");
    }
  }

  // Adjust the navigation buttons position
  if (navButtons) {
    // Remove all relevant classes first
    navButtons.classList.remove("left-1/2", "lg:left-[calc(50vw-212.5px)]", "left-20");

    // Apply appropriate classes based on current state
    if (isActivity) {
      // On activity pages, use left-20 for all screen sizes
      navButtons.classList.add("left-20");
    } else if (isPanelActive) {
      navButtons.classList.add("lg:left-[calc(50vw-212.5px)]", "left-1/2");
    } else {
      navButtons.classList.add("left-1/2");
    }
  }

  // Re-apply zoom if active to maintain proper layout
  const currentZoom = getCurrentZoom();
  if (currentZoom !== 1) {
    // Small delay to let the DOM update first
    setTimeout(() => {
      setNativeZoom(currentZoom);
    }, 10);
  }
};

/**
 * Caches the current sidebar and navigation HTML.
 * Stores them in the interfaceCache object.
 */
export const cacheInterfaceElements = () => {
  try {
    const sidebar = document.getElementById("sidebar");
    const navPopup = document.getElementById("navPopup");

    if (sidebar) {
      interfaceCache.interface = sidebar.outerHTML;
    }
    if (navPopup) {
      interfaceCache.navigation = navPopup.outerHTML;
    }
  } catch (error) {
    console.error("Error caching interface elements:", error);
  }
};

/**
 * Restores cached sidebar and navigation HTML.
 * @returns {boolean} True if successful, false otherwise.
 */
export const restoreInterfaceElements = () => {
  try {
    if (interfaceCache.interface) {
      const interfaceContainer = document.getElementById("interface-container");
      if (interfaceContainer) {
        interfaceContainer.innerHTML = interfaceCache.interface;
      }
    }
    if (interfaceCache.navigation) {
      const navContainer = document.getElementById("nav-container");
      if (navContainer) {
        navContainer.innerHTML = interfaceCache.navigation;
      }
    }
    return true;
  } catch (error) {
    console.error("Error restoring interface elements:", error);
    return false;
  }
};

/**
 * Handles sidebar accessibility attributes and focus.
 * Sets aria-hidden and tabindex based on sidebar state.
 * @private
 * @param {HTMLElement} openSidebar - Sidebar toggle button.
 * @param {HTMLElement} languageDropdown - Language dropdown element.
 */
const handleSidebarAccessibility = (openSidebar, languageDropdown) => {
  const elements = ["close-sidebar", "language-dropdown", "sidebar"];

  elements.forEach((id) => {
    const element = document.getElementById(id);
    if (state.sideBarActive) {
      element.setAttribute("aria-hidden", "false");
      element.removeAttribute("tabindex");
      openSidebar.setAttribute("aria-expanded", "true");

      setTimeout(() => {
        languageDropdown.focus();
      }, 500);
    } else {
      element.setAttribute("aria-hidden", "true");
      element.setAttribute("tabindex", "-1");
      openSidebar.setAttribute("aria-expanded", "false");
    }
  });
};

/**
 * Switches the UI language, updates state, cookies, and translations.
 * Also updates glossary highlights if glossary mode is active.
 */
export const switchLanguage = async () => {
  try {
    const dropdown = document.getElementById("language-dropdown");
    if (!dropdown) return;

    // Disable dropdown during switch
    dropdown.disabled = true;

    // Stop any audio playing
    stopAudio();

    // Update language state
    setState("currentLanguage", dropdown.value);

    // Save to cookie
    const basePath = window.location.pathname.substring(
      0,
      window.location.pathname.lastIndexOf("/") + 1
    );
    setCookie("currentLanguage", state.currentLanguage, 7, basePath);

    // Update HTML lang attribute
    document.documentElement.lang = state.currentLanguage;

    // Fetch and apply new translations
    await fetchTranslations();

    populateGlossaryTerms();

    // If glossary mode is on, update the highlights
    if (state.glossaryMode) {
      highlightGlossaryTerms();
    }

    // Re-enable dropdown
    dropdown.disabled = false;

  } catch (error) {
    console.error("Error switching language:", error);
    showErrorToast("Error changing language");
  }
};

/**
 * Toggles Easy Read mode, updates state and cookie, and fetches translations.
 * @param {Object} [options]
 * @param {boolean} [options.stopCalls=false]
 * @async
 */
export const toggleEasyReadMode = async ({ stopCalls = false } = {}) => {
  setState("easyReadMode", !state.easyReadMode);
  setCookie("easyReadMode", state.easyReadMode, 7);
  toggleButtonState("toggle-easy-read", state.easyReadMode);

  // Track the toggle event
  trackToggleEvent('EasyReadMode', state.easyReadMode);

  /*if (!stopCalls && state.readAloudMode) {
    toggleReadAloud({ stopCalls: true });
  }
  if (!stopCalls && state.signLanguageMode) {
    toggleSignLanguageMode({ stopCalls: true });
  }*/

  stopAudio();
  /*setState(
    "currentLanguage",
    document.getElementById("language-dropdown").value
  );*/
  await fetchTranslations();
};

/**
 * Toggles syllables mode and updates state and cookie.
 */
export const toggleSyllablesMode = () => {
  setState("syllablesMode", !state.syllablesMode);
  setCookie("syllablesMode", state.syllablesMode, 7);
  toggleButtonState("toggle-syllables", state.syllablesMode);
};

/**
 * Initializes the Sign Language quick toggle button.
 * Makes the button visible if it was hidden.
 */
export const initializeSignLanguage = () => {
  const slQuickToggleButton = document.getElementById("sl-quick-toggle-button");
  if (slQuickToggleButton && slQuickToggleButton.classList.contains("hidden")) {
    slQuickToggleButton.classList.remove("hidden");
  }
};

/**
 * Toggles Sign Language mode, updates state and cookie, and manages video and layout.
 * @param {Object} [options]
 * @param {boolean} [options.stopCalls=false]
 */
export const toggleSignLanguageMode = ({ stopCalls = false } = {}) => {
  setState("signLanguageMode", !state.signLanguageMode);
  setCookie("signLanguageMode", state.signLanguageMode ? "true" : "false", 7);
  toggleButtonState("toggle-sign-language", state.signLanguageMode);
  toggleButtonColor("sl-quick-toggle-button", state.signLanguageMode);

  // Toggle the bottom container
  toggleBottomContainer(state.signLanguageMode);

  // Track the toggle event
  trackToggleEvent('SignLanguageMode', state.signLanguageMode);

  adjustLayout();

  if (state.signLanguageMode) {
    startSLVideo();
  } else {
    stopSLVideo();
  }
  if (!stopCalls && state.readAloudMode) {
    toggleReadAloud({ stopCalls: true });
  }
  /* if (!stopCalls && state.easyReadMode) {
    toggleEasyReadMode({ stopCalls: true });
  } */
}

/**
 * Loads Sign Language mode from cookies and applies state.
 * Updates UI and video as needed.
 */
export const loadSignLanguageMode = () => {
  const signLanguageModeCookie = getCookie("signLanguageMode") === "true";

  if (signLanguageModeCookie !== "") {
    setState("signLanguageMode", signLanguageModeCookie);
    toggleButtonState("toggle-sign-language", state.signLanguageMode);
    toggleButtonColor("sl-quick-toggle-button", state.signLanguageMode);

    // Toggle the bottom container based on saved state
    toggleBottomContainer(state.signLanguageMode);

    stopSLVideo();
    if (state.signLanguageMode) {
      startSLVideo();
    }
  }
};

/**
 * Loads glossary terms for the current language and updates state.
 * Fetches glossary JSON and stores it in state.
 * @async
 */
export const loadGlossaryTerms = async () => {
  try {
    // Fallback to "es" if state.currentLanguage is not set
    const language = state.currentLanguage || "es";
    const response = await fetch(`./content/i18n/${language}/glossary/glossary.json`);
    const data = await response.json();
    glossaryTerms = data;
    state.glossaryTerms = data;
  } catch (error) {
    console.error('Error loading glossary:', error);
  }
}

/**
 * Toggles glossary mode, updates state and cookie, and highlights or removes glossary terms.
 */
export const toggleGlossaryMode = () => {
  setState("glossaryMode", !state.glossaryMode);
  setCookie("glossaryMode", state.glossaryMode, 7);
  toggleButtonState("toggle-glossary", state.glossaryMode);

  if (state.glossaryMode) {
    loadGlossaryTerms().then(() => {
      highlightGlossaryTerms();
    })
  } else {
    removeGlossaryHighlights();
  }
};

/**
 * Highlights glossary terms in the content area.
 * Adds event listeners for showing definitions.
 */
export const highlightGlossaryTerms = () => {
  if (!state.glossaryMode || !glossaryTerms) return;

  console.log("Starting glossary highlighting");
  // Remove any existing highlights first
  removeGlossaryHighlights();

  // Extract terms from the current page
  const pageTerms = extractPageTerms();

  // Escape special characters for regex
  const escapeRegExp = (string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  };

  // Build term objects with normalized base forms
  const termObjects = [];
  Object.entries(glossaryTerms || {}).forEach(([key, value]) => {
    // Add main term
    termObjects.push({
      text: key,
      pattern: escapeRegExp(key),
      baseForm: key.toLowerCase().replace(/[es]$|[s]$/, ''), // Basic singular form
      definition: value.definition,
      emoji: value.emoji || ''
    });

    // Add variations
    if (value.variations) {
      value.variations.forEach(term => {
        termObjects.push({
          text: term,
          pattern: escapeRegExp(term),
          baseForm: term.toLowerCase().replace(/[es]$|[s]$/, ''), // Basic singular form
          definition: value.definition,
          emoji: value.emoji || ''
        });
      });
    }
  });

  // Sort longer terms first to handle overlapping terms properly
  termObjects.sort((a, b) => b.text.length - a.text.length);

  if (termObjects.length === 0) return;

  // Track which base forms have been highlighted
  const highlightedBaseForms = new Set();

  // Get content area
  const contentArea = document.getElementById('content');
  if (!contentArea) return;

  // First check headers for terms we should highlight elsewhere
  const termsInHeaders = new Set();
  contentArea.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(header => {
    const headerText = header.textContent.toLowerCase();

    // Check each term
    for (const term of termObjects) {
      const regex = new RegExp(`\\b${term.pattern}\\b`, 'i');
      if (regex.test(headerText)) {
        termsInHeaders.add(term.baseForm);
      }
    }
  });

  // Process text nodes using a safer approach - direct DOM manipulation
  const walker = document.createTreeWalker(
    contentArea,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        // Skip nodes in headers, scripts, styles, or already processed nodes
        if (
          node.parentNode.nodeName.match(/^H[1-6]$/i) ||
          node.parentNode.nodeName === 'SCRIPT' ||
          node.parentNode.nodeName === 'STYLE' ||
          node.parentNode.classList?.contains('glossary-term') ||
          node.parentNode.closest('.glossary-popup, .glossary-term') ||
          node.parentNode.closest('.activity-text')
        ) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  // We'll process nodes one by one - can't modify during traversal
  const nodesToProcess = [];
  let currentNode;
  while (currentNode = walker.nextNode()) {
    // Only process non-empty text nodes
    if (currentNode.textContent.trim()) {
      nodesToProcess.push(currentNode);
    }
  }

  // Process each node
  nodesToProcess.forEach(textNode => {
    const originalText = textNode.textContent;
    if (!originalText.trim()) return;

    // Create segments array to hold parts of the text and their status (highlighted or not)
    const segments = [{ text: originalText, highlighted: false }];

    // Process each term
    for (const term of termObjects) {
      // Skip if this base form is already highlighted (unless it was in a header)
      if (highlightedBaseForms.has(term.baseForm) && !termsInHeaders.has(term.baseForm)) {
        continue;
      }

      // Loop through segments looking for matches
      for (let i = 0; i < segments.length; i++) {
        const segment = segments[i];

        // Skip already highlighted segments
        if (segment.highlighted) continue;

        // Look for the term in this segment
        const regex = new RegExp(`\\b(${term.pattern})([,;:.!?)]|\\s|$)`, 'i');
        const match = segment.text.match(regex);

        if (match) {
          // Found a match - split this segment into three parts
          const beforeText = segment.text.substring(0, match.index);
          const termText = match[1]; // The matched term
          const punctuation = match[2]; // Any punctuation that followed
          const afterText = segment.text.substring(match.index + match[1].length + match[2].length);

          // Replace the segment with three new segments
          segments.splice(
            i, 1,
            { text: beforeText, highlighted: false },
            { text: termText, highlighted: true, term: term },
            { text: punctuation, highlighted: false },
            { text: afterText, highlighted: false }
          );

          // Mark this term as highlighted
          highlightedBaseForms.add(term.baseForm);
          termsInHeaders.delete(term.baseForm);

          // Only process the first match of each term
          break;
        }
      }
    }

    // Check if any segments were highlighted
    if (segments.some(s => s.highlighted)) {
      // Filter out empty segments
      const nonEmptySegments = segments.filter(s => s.text);

      // Create document fragment to hold the new content
      const fragment = document.createDocumentFragment();

      // Process each segment
      nonEmptySegments.forEach(segment => {
        if (segment.highlighted) {
          // Create a highlighted span
          const span = document.createElement('span');
          span.className = 'glossary-term bg-emerald-100 bg-opacity-80 text-emerald-800 rounded cursor-pointer';
          span.setAttribute('role', 'button');
          span.setAttribute('tabindex', '0');
          span.textContent = segment.text;

          // Add click event
          span.addEventListener('click', showGlossaryDefinition);
          span.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              showGlossaryDefinition.call(span, e);
            }
          });

          fragment.appendChild(span);
        } else {
          // Create a text node
          fragment.appendChild(document.createTextNode(segment.text));
        }
      });

      // Replace the original text node with our fragment
      textNode.parentNode.replaceChild(fragment, textNode);
    }
  });
};

/**
 * Shows a glossary definition popup for a clicked term.
 * Handles popup positioning, accessibility, and navigation to glossary sidebar.
 * @param {Event} event - The click event from a glossary term.
 */
export const showGlossaryDefinition = async (event) => {

  // Hide any existing popups
  const existingPopup = document.querySelector('.glossary-popup');
  if (existingPopup) {
    existingPopup.remove();
  }

  // Get the term text and normalize it by removing punctuation
  const termWithPunctuation = event.target.textContent;
  const term = termWithPunctuation
    .toLowerCase()
    .trim()
    .replace(/[.,;:!?()]/g, ''); // Remove punctuation

  let definition = '';
  let emoji = '';
  let originalTerm = ''; // Store the original key term

  // Find the definition, emoji and original term
  for (const [key, value] of Object.entries(glossaryTerms)) {
    // Compare using normalized versions of both the key and search term
    const normalizedKey = key.toLowerCase().trim().replace(/[.,;:!?()]/g, '');

    if (normalizedKey === term) {
      definition = value.definition;
      emoji = value.emoji;
      originalTerm = key; // Use the original key
      break;
    } else if (value.variations && value.variations.some(v =>
      v.toLowerCase().trim().replace(/[.,;:!?()]/g, '') === term)) {
      definition = value.definition;
      emoji = value.emoji;
      originalTerm = key; // Use the original key even for variations
      break;
    }
  }

  if (!definition) return;

  // Create popup
  const popup = document.createElement('div');
  popup.className = 'glossary-popup text-2xl fixed z-50 bg-white rounded-lg border-[1px] border-gray shadow-xl p-4 max-w-sm text-base';
  popup.setAttribute('role', 'dialog');
  popup.setAttribute('aria-label', `Definition for ${originalTerm}`);

  // Create header container with flex layout
  const headerContainer = document.createElement('div');
  headerContainer.className = 'flex items-center gap-4 mb-4';

  // Create emoji container
  const emojiContainer = document.createElement('div');
  emojiContainer.className = 'text-4xl flex-shrink-0';
  emojiContainer.textContent = emoji;
  emojiContainer.setAttribute('role', 'img');
  emojiContainer.setAttribute('aria-label', `Symbol for ${originalTerm}`);

  // Create header text - now using the original term
  const header = document.createElement('div');
  header.className = 'font-bold text-2xl';
  header.textContent = originalTerm; // Use the original key from glossaryTerms

  // Assemble header
  headerContainer.appendChild(emojiContainer);
  headerContainer.appendChild(header);

  // Create content
  const content = document.createElement('div');
  content.className = 'mt-3 text-lg leading-relaxed';
  content.textContent = definition;

  // Create footer with button
  const footer = document.createElement('div');
  footer.className = 'mt-4 flex justify-end border-t border-gray-200 pt-4 pb-1';

  // Create "View in glossary" button
  const viewInGlossaryButton = document.createElement('button');
  viewInGlossaryButton.className = 'px-4 py-2 border border-blue-600 text-blue-600 bg-transparent rounded hover:bg-blue-50 transition-colors flex items-center gap-2 mx-auto';
  viewInGlossaryButton.innerHTML = '<i class="fas fa-book"></i> <span data-id="glossary-view-term">' + translateText("glossary-view-term") + '</span>';
  viewInGlossaryButton.addEventListener('click', (event) => {
    // Stop event propagation to prevent it from reaching document click handlers
    event.stopPropagation();

    // Close the popup
    popup.remove();
    document.removeEventListener('click', handleClickOutside);
    document.removeEventListener('keydown', handleEscape);
    document.removeEventListener('scroll', updatePopupPosition);

    // Get sidebar and glossary elements
    const sidebar = document.getElementById('sidebar');
    const glossaryContent = document.getElementById('glossary-content');
    const pageTab = document.getElementById('page-tab');
    const pageContent = document.getElementById('page-content');
    const glossaryTermsPage = document.getElementById('glossary-terms-page');

    // Make sure the sidebar is open
    if (sidebar && sidebar.classList.contains('translate-x-full')) {
      toggleSidebar();

      // Add small delay to ensure sidebar is open before proceeding
      setTimeout(() => {
        // Rest of the function...
        showGlossaryContent();
      }, 50);
    } else {
      showGlossaryContent();
    }

    // Function to handle showing glossary content
    function showGlossaryContent() {
      // Show the glossary content
      if (glossaryContent && glossaryContent.classList.contains('hidden')) {
        // Hide other sidebar content first
        document.querySelectorAll('#sidebar > div').forEach(div => {
          if (div !== glossaryContent) {
            div.classList.add('hidden');
          }
        });

        // Show glossary content
        glossaryContent.classList.remove('hidden');
      }

      // Select the "On this page" tab
      if (pageTab) {
        pageTab.setAttribute('aria-selected', 'true');
        pageTab.classList.add('bg-gray-100');

        if (document.getElementById('book-tab')) {
          document.getElementById('book-tab').setAttribute('aria-selected', 'false');
          document.getElementById('book-tab').classList.remove('bg-gray-100');
        }
      }

      // Show the page content tab content
      if (pageContent && pageContent.classList.contains('hidden')) {
        pageContent.classList.remove('hidden');

        if (document.getElementById('book-content')) {
          document.getElementById('book-content').classList.add('hidden');
        }
      }

      // Find the term in the glossary list and scroll to it
      if (glossaryTermsPage) {
        // Wait a bit for any animations to complete
        setTimeout(() => {
          // Look for all items with the glossary-page-item class
          const glossaryItems = glossaryTermsPage.querySelectorAll('.glossary-page-item');
          let targetItem = null;

          for (const item of glossaryItems) {
            // Find the term element using the new glossary-page-term class
            const termElement = item.querySelector('.glossary-page-term');
            if (termElement) {
              // Get the text content and normalize it for comparison
              const termText = termElement.textContent.toLowerCase().trim();
              // Check if this term matches our search term
              if (termText.includes(term.toLowerCase())) {
                targetItem = item;
                break;
              }
            }
          }

          if (targetItem) {
            // Scroll the item into view
            targetItem.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Highlight the item temporarily using Tailwind classes
            targetItem.classList.add('bg-yellow-100', 'transition-colors', 'duration-500');

            // Remove highlight after delay
            setTimeout(() => {
              targetItem.classList.remove('bg-yellow-100', 'transition-colors', 'duration-500');
            }, 2000);
          }
        }, 300);
      }
    }
  });

  footer.appendChild(viewInGlossaryButton);

  // Assemble popup
  popup.appendChild(headerContainer);
  popup.appendChild(content);
  popup.appendChild(footer);

  // Position popup
  const updatePopupPosition = () => {
    const popupElement = document.querySelector('.glossary-popup');
    if (popupElement) {
      // Get the current position of the clicked element relative to the viewport
      const newRect = event.target.getBoundingClientRect();

      // Calculate absolute position by adding current scroll position
      const absoluteTop = newRect.bottom + window.scrollY;
      const absoluteLeft = newRect.left + window.scrollX;

      // Position the popup relative to the clicked element's current position
      popup.style.position = 'absolute'; // Use absolute instead of fixed
      popup.style.top = `${absoluteTop + 10}px`;
      popup.style.left = `${absoluteLeft}px`;

      // Adjust position if popup goes off screen
      const popupRect = popup.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      if (popupRect.right > viewportWidth) {
        popup.style.left = `${window.scrollX + viewportWidth - popupRect.width - 10}px`;
      }

      if (popupRect.bottom > viewportHeight) {
        // Show popup above the term if it would go off the bottom
        popup.style.top = `${window.scrollY + newRect.top - popupRect.height - 10}px`;
      }
    }
  };
  // Add to document
  document.body.appendChild(popup);
  updatePopupPosition();
  // Handle scroll event to update position
  window.addEventListener('scroll', updatePopupPosition);

  // Handle click outside
  function handleClickOutside(e) {
    if (!popup.contains(e.target) && e.target !== event.target) {
      popup.remove();
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('scroll', updatePopupPosition);
    }
  }

  // Handle Escape key
  function handleEscape(e) {
    if (e.key === 'Escape') {
      popup.remove();
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('scroll', updatePopupPosition);
      // Return focus to the term that was clicked
      event.target.focus();
    }
  }

  // Add event listeners
  setTimeout(() => {
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    document.addEventListener('scroll', updatePopupPosition);
  }, 0);
}

/**
 * Removes all glossary term highlights and glossary popups from the content area.
 */
export const removeGlossaryHighlights = () => {
  // First, handle any existing popups
  document.querySelectorAll('.glossary-popup').forEach(popup => {
    popup.remove();
  });

  // Find all glossary terms
  document.querySelectorAll('.glossary-term').forEach(term => {
    const text = document.createTextNode(term.textContent);
    term.parentNode.replaceChild(text, term);
  });

  // Look for empty wrapper spans that may have been created
  document.querySelectorAll('span:not([class])').forEach(span => {
    // Check if this is likely a wrapper we created (no attributes, only text nodes)
    if (span.attributes.length === 0 &&
      span.childNodes.length > 0 &&
      Array.from(span.childNodes).every(node => node.nodeType === 3)) {

      // Get the text content
      const text = document.createTextNode(span.textContent);

      // Replace the span with its content
      if (span.parentNode) {
        span.parentNode.replaceChild(text, span);
      }
    }
  });
};

/**
 * Loads Easy Read mode from cookies and applies state.
 * Updates UI and fetches translations.
 * @async
 */
export const loadEasyReadMode = async () => {
  const easyReadModeCookie = getCookie("easyReadMode");

  if (easyReadModeCookie !== "") {
    setState("easyReadMode", easyReadModeCookie === "true");
    toggleButtonState("toggle-easy-read", state.easyReadMode);

    stopAudio();
    /*setState(
      "currentLanguage",
      document.getElementById("language-dropdown").value
    );*/
  }
};

/**
 * Toggles state mode and updates state and cookie.
 */
export const toggleStateMode = () => {
  setState("stateMode", !state.stateMode);
  setCookie("stateMode", state.stateMode ? "true" : "false", 7);
  toggleButtonState("toggle-state", state.stateMode);
};

/**
 * Loads state mode from cookies and applies state.
 */
export const loadStateMode = () => {
  const stateModeCookie = getCookie("stateMode") === "true" || getCookie("stateMode") === "" || getCookie("stateMode") === null;

  if (stateModeCookie !== "") {
    setState("stateMode", stateModeCookie);
    setCookie("stateMode", state.stateMode ? "true" : "false", 7);
    toggleButtonState("toggle-state", state.stateMode);
  }
};

/**
 * Initializes the play bar based on state and cookies.
 * Shows or hides the play bar as needed.
 */
export const initializePlayBar = () => {
  try {
    // Get play bar visibility state
    const playBarVisible = getCookie("playBarVisible") === "true";
    const readAloudMode = getCookie("readAloudMode") === "true";
    // Set initial state
    setState("readAloudMode", readAloudMode);

    // Get play bar element
    const playBar = document.getElementById("play-bar");
    if (!playBar) return;

    if (state.readAloudMode) {
      playBar.classList.remove("hidden");
    } else {
      playBar.classList.add("hidden");
    }
    // // Show/hide based on read aloud mode
    // if (readAloudMode) {
    //     playBar.classList.remove("hidden");
    //     setCookie("playBarVisible", "true", 7);
    // } else {
    //     playBar.classList.add("hidden");
    //     setCookie("playBarVisible", "false", 7);
    // }
  } catch (error) {
    console.error('Error initializing play bar:', error);
  }
};

/**
 * Toggles the visibility of the play bar settings panel.
 */
export const togglePlayBarSettings = () => {
  const readAloudSettings = document.getElementById("read-aloud-settings");
  if (readAloudSettings.classList.contains("opacity-0")) {
    readAloudSettings.classList.add(
      "opacity-100",
      "pointer-events-auto",
      "h-auto"
    );
    readAloudSettings.classList.remove(
      "opacity-0",
      "pointer-events-none",
      "h-0"
    );
  } else {
    readAloudSettings.classList.remove(
      "opacity-100",
      "pointer-events-auto",
      "h-auto"
    );
    readAloudSettings.classList.add("h-0", "opacity-0", "pointer-events-none");
  }
};

/**
 * Formats navigation items, adds icons, and highlights the current page.
 * Handles activity completion and page/section formatting.
 */
export const formatNavigationItems = () => {
  const navListItems = document.querySelectorAll(".nav__list-item");

  navListItems.forEach((item, index) => {
    const link = item.querySelector(".nav__list-link");
    if (!link) return;

    // Setup basic classes for the item and link
    item.classList.add(
      "border-b",
      "border-gray-300",
      "flex",
      "items-center"
    );

    link.classList.add(
      "flex-grow",
      "flex",
      "items-center",
      "w-full",
      "h-full",
      "p-2",
      "py-3",
      "hover:bg-blue-50",
      "transition",
      "text-gray-500"
    );

    // Add border top to first element
    if (index === 0) {
      item.classList.add("border-t");
    }

    // Get section and page numbers from href
    const href = link.getAttribute("href");
    const textId = link.getAttribute("data-text-id");

    // Check for both patterns - either "6_0" format or just "6" format
    const pageSectionMatch = href.match(/(\d+)_(\d+)/);
    const pageOnlyMatch = !pageSectionMatch && href.match(/(\d+)/);

    // Handle activity items
    let itemIcon = "";
    let itemSubtitle = "";
    if (item.classList.contains("activity")) {
      const activityId = href.split(".")[0];
      const success = JSON.parse(localStorage.getItem(`${activityId}_success`)) || false;

      if (success) {
        itemIcon = `<i class="${activityId} fas fa-check-square text-green-500 mt-1"></i>`;
        itemSubtitle = "<span data-id='activity-completed'></span>";
      } else {
        itemIcon = `<i class="${activityId} fas fa-pen-to-square mt-1 text-blue-700"></i>`;
        itemSubtitle = "<span data-id='activity-to-do'></span>";
      }
    }
    // Format the link content with section numbers
    let humanReadablePage;
    if (pageSectionMatch) {
      const [_, pageNumber, sectionNumber] = pageSectionMatch.map(Number);

      // Handle special case of page 0
      if (pageNumber === 0 && (!sectionNumber || sectionNumber === 0)) {
        humanReadablePage = "0";
      }

      // For pages with sections (format "7_0" renders as "6.1")
      else if (sectionNumber !== undefined) {
        humanReadablePage = `${pageNumber - 1}.${sectionNumber + 1}`;
      }
    } else if (pageOnlyMatch) {
      // For pages with no section information (format "6" renders as "5")
      const pageNumber = Number(pageOnlyMatch[1]);
      humanReadablePage = pageNumber - 1;
    } else {
      humanReadablePage = "0";
    }

    // Check the textId format to ensure we're not incorrectly treating this as a sectioned page
    // If href has no section but textId does (like "text-6-0"), we should use href as the source of truth
    const textIdHasSection = textId && textId.match(/-\d+-\d+$/);
    const hrefHasNoSection = !pageSectionMatch && pageOnlyMatch;

    if (hrefHasNoSection && textIdHasSection) {
      // This is a page without sections being incorrectly treated as having sections
      // Use just the page number without decimal formatting
      humanReadablePage = Number(pageOnlyMatch[1]) - 1;
    }

    link.innerHTML =
      "<div class='flex items-top space-x-2'>" +
      itemIcon +
      "<div>" +
      `<div>${humanReadablePage}: <span class='inline text-gray-800' data-id='${textId}'></span></div>` +
      "<div class='text-sm text-gray-500'>" +
      itemSubtitle +
      "</div>" +
      "</div>" +
      "</div>";

    // Highlight current page
    if (href === window.location.pathname.split("/").pop()) {
      item.classList.add("min-h-[3rem]");
      link.classList.add(
        "border-l-4",
        "border-blue-500",
        "bg-blue-100",
        "p-2"
      );
    }
  });
}

/**
 * Updates the play/pause icon in the play bar based on state.
 */
export const setPlayPauseIcon = () => {
  const playIcon = document.getElementById("read-aloud-play-icon");
  const pauseIcon = document.getElementById("read-aloud-pause-icon");

  if (state.isPlaying) {
    playIcon.classList.add("hidden");
    pauseIcon.classList.remove("hidden");
  } else {
    playIcon.classList.remove("hidden");
    pauseIcon.classList.add("hidden");
  }
};

const initializePlaybackControls = () => {
  const playbackSpeed = document.getElementById("read-aloud-speed");
  if (playbackSpeed) {
    playbackSpeed.classList.add(
      "absolute",
      "bottom-24",
      "right-4",
      "bg-white",
      "rounded-lg",
      "shadow-lg",
      "z-50"
    );
  }
};

/**
 * Updates toggle switch visuals based on checked state.
 * @param {HTMLInputElement} toggle - The toggle input element.
 */
export const updateToggleVisuals = (toggle) => {
  const container = toggle.closest(".toggle-container");
  if (container) {
    const track = container.querySelector(".toggle-track");
    const thumb = container.querySelector(".toggle-thumb");

    if (toggle.checked) {
      track?.classList.remove("bg-gray-200");
      track?.classList.add("bg-blue-600");
      thumb?.classList.add("translate-x-5");
    } else {
      track?.classList.add("bg-gray-200");
      track?.classList.remove("bg-blue-600");
      thumb?.classList.remove("translate-x-5");
    }
  }
};

/**
 * Extracts glossary terms found on the current page.
 * @returns {string[]} Array of terms found.
 */
export const extractPageTerms = () => {
  const contentArea = document.getElementById('content');
  if (!contentArea) return [];

  // Get the actual text content of the page
  const pageContent = contentArea.textContent;

  // Create a map to track terms and their original capitalization
  const termMap = new Map(); // Maps lowercase terms to their preferred display form

  // Escape special characters for regex
  const escapeRegExp = (string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  };

  // Build a list of all terms to check
  const allTerms = [];
  Object.entries(glossaryTerms || {}).forEach(([key, value]) => {
    // Add main term
    allTerms.push(key);

    // Add variations
    if (value.variations && Array.isArray(value.variations)) {
      value.variations.forEach(term => allTerms.push(term));
    }
  });

  // Check each term with a word boundary regex to ensure exact matches
  allTerms.forEach(term => {
    // Create a pattern that handles word boundaries better with accented characters
    const regex = new RegExp(`(^|[^a-záéíóúñA-ZÁÉÍÓÚÑ])${escapeRegExp(term)}($|[^a-záéíóúñA-ZÁÉÍÓÚÑ])`, 'gi');

    // Find all exact matches in the content
    let matches = pageContent.match(regex);
    if (matches) {
      matches.forEach(match => {
        // Extract just the term from the match (remove the boundary characters)
        const extractedTerm = match.trim().replace(/^[^a-záéíóúñA-ZÁÉÍÓÚÑ]|[^a-záéíóúñA-ZÁÉÍÓÚÑ]$/g, '');

        // Store the lowercase version as key, but keep the first occurrence's capitalization
        const lowerCaseTerm = extractedTerm.toLowerCase();

        // Only add to the map if it's not already there
        if (!termMap.has(lowerCaseTerm)) {
          termMap.set(lowerCaseTerm, extractedTerm);
        }
      });
    }
  });

  // Convert the map values to an array and sort it alphabetically
  return Array.from(termMap.values()).sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
};

// export const adjustPageScale = () => {
//   const container = document.getElementById("content");
//   if (!container) return;
/*
const viewportHeight = window.innerHeight;
const pixelRatio = window.devicePixelRatio;

// Calculate the scale factor based only on the height
const scaleY = viewportHeight / container.offsetHeight;
const scale = scaleY / pixelRatio;

// Apply the scale to the container
container.style.transform = `scale(${scale})`;
container.style.transformOrigin = 'top left'; // Ensure scaling starts from the top-left corner*/
//};

// export const adjustPageScale = () => {
//   // Target the html element for the most global effect
//   const htmlElement = document.documentElement;

//   // Apply a 90% scale to simulate zooming out
//   htmlElement.style.transform = 'scale(0.9)';
//   htmlElement.style.transformOrigin = 'top center';

//   // Adjust the width to prevent horizontal scrollbar
//   // When scaled down to 90%, we need to make the width about 111% (1/0.9)
//   htmlElement.style.width = '111.1%';

//   // Compensate for the extra space created at the bottom
//   htmlElement.style.height = '111.1%';

//   // Adjust the margin to center the content
//   htmlElement.style.marginLeft = '-5.55%'; // Half of the extra width (11.1% / 2)

//   console.log('Applied 90% zoom simulation to entire page');
// }

// export const adjustPageScale = () => {
//   const body = document.body;
//   const pixelRatio = window.devicePixelRatio;

//   // More modern detection of Windows platform
//   const isWindows = () => {
//     // Try modern API first
//     if (navigator.userAgentData && navigator.userAgentData.platform) {
//       return navigator.userAgentData.platform === 'Windows';
//     }

//     // Fallback to user agent string checking
//     return navigator.userAgent.indexOf('Win') !== -1;
//   };

//   // For Windows with high DPI settings, we need special handling
//   if (pixelRatio > 1 && isWindows()) {

//     const fixedScale = 0.9;

//     const compensationFactor = (100 / fixedScale);

//     // Rest of your scaling code
//     document.documentElement.style.setProperty('--page-scale', 1/pixelRatio);
//     body.style.transform = `scale(${fixedScale})`;
//     body.style.transformOrigin = 'top left';
//     body.style.width = `${compensationFactor}%`;
//     body.style.height = `${compensationFactor}%`;

//     console.log(`Adjusted scale to fixed 90%, scaling entire body. Device pixel ratio: ${pixelRatio}`);
//   } else {
//     // Reset any scaling for standard displays
//     document.documentElement.style.removeProperty('--page-scale');
//     body.style.transform = '';
//     body.style.width = '';
//     body.style.height = '';
//   }
// };

// document.addEventListener('DOMContentLoaded', function() {
//   // Initialize simple zoom
//   initSimpleZoom();
// });

/**
 * Checks for Windows scaling and shows a notification if needed.
 * Also initializes the zoom controller.
 */
export const checkWindowsScaling = () => {
  // Initialize the zoom controller first
  initializeZoomController();

  console.log('Checking Windows scaling...', isHighDpiWindows());

  // Only show notification if we're on Windows with high DPI and haven't shown it before
  if (isHighDpiWindows() && localStorage.getItem('hasSeenScalingNotice') !== 'true') {
    //if (true) {
    console.log('High DPI Windows detected, showing notification');

    // Create notification container
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md z-50 flex flex-col';
    notification.style.maxWidth = '350px';

    // Add notification content
    notification.innerHTML = `
      <div class="flex items-start mb-3">
      <div class="text-amber-500 mr-3 text-xl flex-shrink-0">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <div>
        <h3 class="font-semibold text-gray-800 mb-1">Escalado de Pantalla Detectado</h3>
        <p class="text-gray-600 text-sm">
        Se ha detectado un escalado de alta resolución. Esto puede resultar en una experiencia de visualización menos óptima. Presiona Ctrl + “-” (menos) para reducir el zoom hasta alcanzar el tamaño de visualización deseado.
        </p>
      </div>
      </div>
      <div class="flex justify-end space-x-2">
      <button id="dismiss-scaling-notice" class="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors">
        No mostrar de nuevo
      </button>
      </div>
    `;

    // <button id="apply-zoom-out" onclick="this.closest('.fixed').remove(); console.log('Zoom applied')" class="text-sm px-3 py-1 bg-blue-600 text-white hover:bg-blue-700 rounded transition-colors">
    //       Zoom to 75%
    //     </button>
    //     <button id="show-zoom-controls" class="text-sm px-3 py-1 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors">
    //       Show zoom controls
    //     </button>

    // Add to document
    document.body.appendChild(notification);

    // const applyZoomNew = () => {

    //       // Apply zoom to body
    //       if (body) {
    //         body.style.transform = `scale(${zoomLevel})`;
    //         body.style.transformOrigin = 'top center';
    //         body.style.width = `${inverseZoom * 100}%`;
    //         body.style.minHeight = `${inverseZoom * 100}vh`;
    //         body.style.overflowY = 'auto'; // Allow vertical scrolling
    //         body.style.overflowX = 'hidden'; // Prevent horizontal scrolling
    //       }
    //     };

    // // Add zoom out handler
    // document.getElementById('apply-zoom-out').addEventListener('click', () => {
    //   // Set zoom to compensate for 150% scaling (1/1.5 ≈ 0.67)
    //   console.log('zooming out');

    //   document.body.style.zoom = 0.75;
    //   //setNativeZoom(0.75);

    //   // Show zoom controls
    //   createZoomControls();

    //   // Close notification
    //   notification.remove();
    // });

    // Add show controls handler
    // document.getElementById('show-zoom-controls').addEventListener('click', () => {
    //   createZoomControls();
    //   notification.remove();
    // });

    // Add dismiss handler
    document.getElementById('dismiss-scaling-notice').addEventListener('click', () => {
      console.log('Dismissing scaling notice');
      // Close notification
      notification.remove();
      localStorage.setItem('hasSeenScalingNotice', 'true');
    });

    // Auto-dismiss after 15 seconds
    setTimeout(() => {
      if (document.body.contains(notification)) {
        notification.remove();
      }
    }, 15000);
  }
};

/**
 * Creates and shows the zoom reset button (or controls).
 */
export const createZoomResetButton = () => {
  // Use the more comprehensive zoom controls instead
  return createZoomControls();
};

// Update this function to match the new ID
function removeResetZoomButton() {
  const existingButton = document.getElementById('zoom-reset-button');
  if (existingButton) {
    console.log('Removing zoom reset button');
    existingButton.remove();
  }
}

// Add a direct zoom function to test functionality
export const testZoom = (level) => {
  console.log(`Testing zoom at level: ${level}`);
  return setNativeZoom(level);
};

/**
 * Public function to manually trigger the zoom reset button creation.
 */
export const showZoomResetButton = () => {
  return createZoomResetButton();
};

// Initial check on load - using window.onload instead of DOMContentLoaded to ensure everything is loaded
window.addEventListener('load', () => {
  console.log('Window loaded, checking scaling...');
  setTimeout(checkWindowsScaling, 500); // Slight delay to ensure everything is ready
});

/**
 * Shows or hides the sidebar based on provided state.
 * @param {boolean} show - Whether to show the sidebar (true) or hide it (false).
 */
export const setSidebarVisibility = (show) => {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  // Add these new elements to adjust
  const submitButtonContainer = document.querySelector(".fixed.bottom-0 .container .absolute");
  const navButtons = document.getElementById("back-forward-buttons");
  const mainContent = document.querySelector(".container");

  if (show) {
    // Show sidebar
    sidebar.classList.remove("translate-x-full");
    sidebar.setAttribute("aria-expanded", "true");
    sidebar.removeAttribute("inert");
    document.querySelector("body > .container")?.classList.remove("lg:mx-auto");

    if (mainContent) {
      mainContent.classList.add("lg:ml-0");
      mainContent.classList.add("lg:w-[calc(100vw-425px)]");
    }

    // Adjust the submit button position when sidebar is open
    if (submitButtonContainer) {
      submitButtonContainer.classList.remove("lg:right-0");
      submitButtonContainer.classList.add("lg:right-[calc(425px-1rem)]");
    }

    // Adjust the navigation buttons position
    if (navButtons) {
      navButtons.classList.remove("left-1/2");
      navButtons.classList.add("lg:left-[calc(50vw-212.5px)]");
    }
  } else {
    // Hide sidebar
    sidebar.classList.add("translate-x-full");
    sidebar.setAttribute("aria-expanded", "false");
    sidebar.setAttribute("inert", "");

    if (mainContent) {
      mainContent.classList.remove("lg:ml-0");
      mainContent.classList.remove("lg:w-[calc(100vw-425px)]");
    }

    // Reset positions when sidebar is closed
    if (submitButtonContainer) {
      submitButtonContainer.classList.add("lg:right-0");
      submitButtonContainer.classList.remove("lg:right-[calc(425px-1rem)]");
    }

    if (navButtons) {
      navButtons.classList.add("left-1/2");
      navButtons.classList.remove("lg:left-[calc(50vw-212.5px)]");
    }
  }

  // Save current state
  interfaceCache.sidebarState = show;
  setCookie("sidebarState", show ? "open" : "closed", 7);

  // If zoomed, re-apply zoom to keep sidebar properly positioned
  const currentZoom = getCurrentZoom();
  if (currentZoom !== 1) {
    setTimeout(() => {
      setNativeZoom(currentZoom);
    }, 50);
  }
};

/**
 * Shows or hides the navigation popup based on provided state.
 * @param {boolean} show - Whether to show the navigation (true) or hide it (false).
 */
export const setNavVisibility = (show) => {
  const navPopup = document.getElementById("navPopup");
  const navList = document.querySelector(".nav__list");
  if (!navPopup) return;

  // Always ensure transform and transition classes are present
  navPopup.classList.add("transform", "transition-transform", "duration-300", "ease-in-out");

  if (show) {
    // Remove translate-x-full to slide in
    navPopup.classList.remove("-translate-x-full");
    navPopup.classList.add("left-2");
    navPopup.setAttribute("aria-expanded", "true");
    navPopup.removeAttribute("inert");

    // Show navList
    if (navList) {
      // navList.removeAttribute("hidden");
      // Restore scroll position if available
      const savedPosition = getCookie("navScrollPosition");
      if (savedPosition) {
        navList.scrollTop = parseInt(savedPosition);
      }
    }
    setCookie("navState", "open", 7);
  } else {
    // Add translate-x-full to slide out
    navPopup.classList.add("-translate-x-full");
    navPopup.classList.remove("left-2");
    navPopup.setAttribute("aria-expanded", "false");
    navPopup.setAttribute("inert", "");

    // Hide navList and save scroll position
    if (navList) {
      const scrollPosition = navList.scrollTop;
      // navList.setAttribute("hidden", "true");
      setCookie("navScrollPosition", scrollPosition, 7);
    }
    setCookie("navState", "closed", 7);
  }

  // Save current state
  interfaceCache.navigation = show;
};