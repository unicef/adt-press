import { initializeAdminPopup } from "./modules/admin_popup.js";
import {
  changeAudioSpeed,
  initializeAudioSpeed,
  playNextAudio,
  playPreviousAudio,
  togglePlayPause,
  toggleReadAloud,
  initializeTtsQuickToggle,
} from "./modules/audio.js";
import { initializeWordByWordHighlighter } from "./modules/tts_highlighter.js";
import { getCookie } from "./modules/cookies.js";
import {
  handleInitializationError,
  showMainContent,
} from "./modules/error_utils.js";
import { loadAtkinsonFont } from "./modules/font_utils.js";
import {
  initializeLanguageDropdown,
  cacheInterfaceElements,
  getCachedInterface,
  getCachedNavigation,
  initializePlayBar,
  initializeSidebar,
  loadEasyReadMode,
  restoreInterfaceElements,
  switchLanguage,
  toggleEasyReadMode,
  toggleSyllablesMode,
  toggleGlossaryMode,
  highlightGlossaryTerms,
  togglePlayBarSettings,
  toggleSidebar,
  updatePageNumber,
  formatNavigationItems,
  initializeNavigation,
  toggleStateMode,
  loadStateMode,
  toggleSignLanguageMode,
  loadSignLanguageMode,
  adjustLayout,
  initializeSignLanguage
  //checkWindowsScaling
  //adjustPageScale
} from "./modules/interface.js";
import { initializeZoomController, testZoomNow } from "./modules/browser_zoom_controller.js";
import {
  handleKeyboardShortcuts,
  handleNavigation,
  nextPage,
  toggleNav,
  previousPage,
  setupClickOutsideHandler,
} from "./modules/navigation.js";
import { setState, state } from "./modules/state.js";
import { setupTranslations } from "./modules/translations.js";
import {
  initializeAutoplay,
  loadAutoplayState,
  loadDescribeImagesState,
  loadGlossaryState,
  toggleAutoplay,
  toggleDescribeImages,
  toggleEli5Mode,
  handleEli5Popup,
  initializeAudioElements,
  initializeGlossary,
  initializeTabs,
  initializeReferencePage,
  setAutoplayContainerVisibility,
  setDescribeImagesContainerVisibility,
  updateTtsOptionsContainerVisibility,
  loadToggleButtonState,
  initializeEli5
} from "./modules/ui_utils.js";
import {
  toggleNotepad,
  saveNotes,
  loadSavedNotes,
  loadNotepad,
  initializeNotepad
} from "./modules/notepad.js";
import { prepareActivity } from "./activity.js";
import { initCharacterDisplay } from "./modules/character-display.js"
import { initMatomo } from "./modules/analytics.js";

// Constants
const PLACEHOLDER_TITLE = "Accessible Digital Textbook";
const basePath = window.location.pathname.substring(
  0,
  window.location.pathname.lastIndexOf("/") + 1
);

// Create a centralized asset loader
const assetLoader = {
  cache: new Map(),
  
  async load(paths) {
    try {
      const promises = paths.map(path => 
        this.cache.has(path) ? 
          Promise.resolve(this.cache.get(path)) : 
          fetch(path)
            .then(response => {
              if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
              return response.text();
            })
            .then(content => {
              this.cache.set(path, content);
              return content;
            })
      );
      
      return await Promise.all(promises);
    } catch (error) {
      console.error("Error loading assets:", error);
      throw error;
    }
  }
};

// Element cache to avoid repetitive DOM lookups
const elementCache = {
  _cache: new Map(),
  
  get(id) {
    if (!this._cache.has(id)) {
      const element = document.getElementById(id);
      this._cache.set(id, element);
    }
    return this._cache.get(id);
  },
  
  getAll(selector) {
    const key = `selector:${selector}`;
    if (!this._cache.has(key)) {
      const elements = document.querySelectorAll(selector);
      this._cache.set(key, elements);
    }
    return this._cache.get(key);
  },
  
  clear() {
    this._cache.clear();
  }
};

// Initialize the application
document.addEventListener("DOMContentLoaded", async function () {
  try {
    await initializeApp();
  } catch (error) {
    console.error("Error initializing application:", error);
    handleInitializationError();
  }
});

// Store the current page state before leaving
window.addEventListener("beforeunload", () => {
  cacheInterfaceElements();
  //saveInterfaceState();
});

// Create a structured initialization sequence
async function initializeApp() {
  try {
    showLoadingIndicator();
    addFavicons();
    
    // Ensure DOM is ready
    await waitForDOM();
    
    // Initialize in a specific sequence with dependencies
    const initSequence = [
      { 
        name: "Core", 
        fn: initializeCoreFunctionality 
      },
      { 
        name: "EventListeners", 
        fn: setupEventListeners, 
        dependencies: ["Core"] 
      },
      { 
        name: "UI", 
        fn: initializeUIComponents, 
        dependencies: ["Core", "EventListeners"] 
      },
      { 
        name: "Final", 
        fn: finalizeInitialization, 
        dependencies: ["UI"] 
      }
    ];
    
    for (const step of initSequence) {
      console.log(`Initializing: ${step.name}`);
      await step.fn();
    }
  } catch (error) {
    console.error("Error in initialization:", error);
    handleInitializationError(error);
  } finally {
    showMainContent();
    hideLoadingIndicator();
  }
}

// Add this function in the initializeApp() function

function addFavicons() {
  const faviconLinks = [
    { rel: "icon", type: "image/x-icon", href: "./assets/favicon_io/favicon.ico" },
    { rel: "apple-touch-icon", sizes: "180x180", href: "./assets/favicon_io/apple-touch-icon.png" },
    { rel: "icon", type: "image/png", sizes: "32x32", href: "./assets/favicon_io/favicon-32x32.png" },
    { rel: "icon", type: "image/png", sizes: "16x16", href: "./assets/favicon_io/favicon-16x16.png" },
    { rel: "manifest", href: "./assets/favicon_io/site.webmanifest" }
  ];

  faviconLinks.forEach(linkData => {
    // Check if link already exists to avoid duplicates
    const exists = Array.from(document.head.querySelectorAll('link')).some(
      link => link.rel === linkData.rel && link.href.includes(linkData.href.split('/').pop())
    );
    
    if (!exists) {
      const link = document.createElement('link');
      for (const [attr, value] of Object.entries(linkData)) {
        link.setAttribute(attr, value);
      }
      document.head.appendChild(link);
    }
  });
}

function waitForDOM() {
  return new Promise((resolve) => {
    if (document.readyState === "complete") {
      resolve();
    } else {
      window.addEventListener("load", resolve);
    }
  });
}

function showLoadingIndicator() {
  const loader = document.createElement("div");
  loader.id = "app-loader";
  loader.className =
    "fixed top-0 left-0 w-full h-full flex items-center justify-center bg-white z-50";
  loader.innerHTML = `
       <div class="text-center">
           <div class="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
           <p class="mt-4 text-gray-600">Loading...</p>
       </div>
   `;
  document.body.appendChild(loader);
}

function hideLoadingIndicator() {
  const loader = document.getElementById("app-loader");
  if (loader) {
    loader.remove();
  }
}

function restoreNavAndSidebar() {
  const navPopup = document.getElementById("navPopup");
  const sidebar = document.getElementById("sidebar");

  if (navPopup) navPopup.classList.remove("hidden");
  if (sidebar) sidebar.classList.remove("hidden");
}

function hideMainContent() {
  // Instead of adding hidden class, use opacity
  const mainContent = document.body;
  if (mainContent) {
    mainContent.classList.add("opacity-0");
    mainContent.classList.add("z-30");
    // Set a maximum time to stay hidden
    setTimeout(() => {
      mainContent.classList.remove("opacity-0");
    }, 3000); // Failsafe timeout
  }
}

async function initializeCoreFunctionality() {
  try {
    // First ensure the DOM is fully loaded
    if (document.readyState !== "complete") {
      await new Promise((resolve) => {
        window.addEventListener("load", resolve);
      });
    }

    // Initialize language before other components
    initializeLanguage();
    loadAtkinsonFont();
    initCharacterDisplay();

    // Initialize components after HTML is definitely loaded
    await fetchAndInjectComponents();

    // Try to initialize language dropdown
    const dropdownInitialized = await initializeLanguageDropdown();
    if (!dropdownInitialized) {
      console.warn(
        "Language dropdown initialization failed, continuing with other components"
      );
    }

    formatNavigationItems();
    // Initialize page numbering
    updatePageNumber();
    await setupTranslations();
    
    return true;
  } catch (error) {
    console.error("Error in core initialization:", error);
    return false;
  }
}

function initializeLanguage() {
  let languageCookie = getCookie("currentLanguage");
  setState(
    "currentLanguage",
    languageCookie ||
      document.getElementsByTagName("html")[0].getAttribute("lang")
  );
}

const handleResponse = async (response) => {
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response;
};

async function fetchAndInjectComponents() {
  try {
    // Fetch interface and navigation
    const [interfaceHTML, navHTML] = await Promise.all([
      fetch("./assets/interface.html").then(response => response.text()),
      fetch("./content/navigation/nav.html").then(response => response.text())
    ]);
    
    // Fetch config as JSON instead of HTML
    const configResponse = await fetch("./assets/config.json");
    const config = await configResponse.json();
    
    // Pass the config object instead of HTML string
    await injectComponents(interfaceHTML, navHTML, config);
  } catch (error) {
    throw new Error("Failed to fetch components: " + error.message);
  }
};

async function injectComponents(interfaceHTML, navHTML, config) {
  try {
    const cachedInterface = getCachedInterface();
    const cachedNavigation = getCachedNavigation();

    if (cachedInterface && cachedNavigation) {
      const restored = restoreInterfaceElements();
      if (!restored) {
        throw new Error("Failed to restore cached interface elements");
      }
    } else {
      const interfaceContainer = elementCache.get("interface-container");
      const navContainer = elementCache.get("nav-container");

      if (!interfaceContainer || !navContainer) {
        throw new Error("Required containers not found");
      }

      interfaceContainer.innerHTML = interfaceHTML;
      navContainer.innerHTML = navHTML;
      
      // Clear cache since DOM has changed
      elementCache.clear();
      
      cacheInterfaceElements();
    }

    setupConfig(config);
  } catch (error) {
    console.error("Error injecting components:", error);
    throw new Error("Failed to inject components: " + error.message);
  }
}

function setupConfig(config) {
  // Apply title from config
  if (config.title && config.title !== PLACEHOLDER_TITLE) {
    document.title = config.title;
  }
  
  // Set available languages meta tag
  if (config.languages && config.languages.available) {
    const availableLanguagesStr = config.languages.available.join(',');
    
    // Create or update the meta tag
    let availableLanguagesMeta = document.querySelector('meta[name="available-languages"]');
    if (!availableLanguagesMeta) {
      availableLanguagesMeta = document.createElement("meta");
      availableLanguagesMeta.name = "available-languages";
      document.head.appendChild(availableLanguagesMeta);
    }
    availableLanguagesMeta.content = availableLanguagesStr;
  }
  
  // Store the config for access throughout the application
  window.appConfig = config;
  
  // Apply feature flags
  applyFeatureFlags(config.features || {});
}

// Add this helper function
function applyFeatureFlags(features) {
  // Loop through features and apply them
  Object.entries(features).forEach(([feature, enabled]) => {
    // Convert camelCase to kebab-case for element IDs
    const kebabFeature = feature.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
    
    // Find the toggle element
    const toggleElement = elementCache.get(`toggle-${kebabFeature}`);
    
    // If the toggle exists but feature is disabled, hide its container
    if (toggleElement) {
      const container = toggleElement.closest('.setting-item') || 
                       toggleElement.closest('.feature-container') || 
                       toggleElement.parentElement;
      
      if (container) {
        container.classList.toggle('hidden', !enabled);
      }
    }
    
    // Also store in the state for programmatic checks
    setState(`${feature}Enabled`, enabled);
  });
}

// Create a helper function for attaching event listeners
function addListener(elementId, event, handler) {
  const element = document.getElementById(elementId);
  if (element) element.addEventListener(event, handler);
  return element;
}

// Use with an object map for clarity
function setupEventListeners() {
  // Handle basic click events
  const clickHandlers = {
    "open-sidebar": toggleSidebar,
    "close-sidebar": toggleSidebar,
    "toggle-eli5": toggleEli5Mode,
    "toggle-easy-read": toggleEasyReadMode,
    "toggle-sign-language": toggleSignLanguageMode,
    "sl-quick-toggle-button": toggleSignLanguageMode,
    "toggle-syllables": toggleSyllablesMode,
    "toggle-glossary": toggleGlossaryMode,
    "toggle-autoplay": toggleAutoplay,
    "toggle-describe-images": toggleDescribeImages,
    "toggle-state": toggleStateMode,
    "back-button": previousPage,
    "forward-button": nextPage,
    "nav-popup": toggleNav,
    "nav-close": toggleNav,
    "notepad-button": toggleNotepad,
    "close-notepad": toggleNotepad,
    "save-notepad": saveNotes,
  };
  
  // Attach all click handlers
  Object.entries(clickHandlers).forEach(([id, handler]) => {
    const element = elementCache.get(id);
    if (element) element.addEventListener("click", handler);
  });
  
  // Handle special cases
  const languageDropdown = elementCache.get("language-dropdown");
  if (languageDropdown) languageDropdown.addEventListener("change", switchLanguage);
  
  // Set up notepad auto-save
  const notepadTextarea = elementCache.get("notepad-textarea");
  if (notepadTextarea) {
    let saveTimeout;
    notepadTextarea.addEventListener("input", () => {
      clearTimeout(saveTimeout);
      saveTimeout = setTimeout(saveNotes, 1000);
    });
  }
  
  // Global listeners
  document.addEventListener("click", handleNavigation);
  document.addEventListener("keydown", handleKeyboardShortcuts);
  
  // Purple links
  const purpleLinks = elementCache.getAll('.purple-link-button');
  purpleLinks.forEach(link => {
    link.addEventListener('click', () => {
      localStorage.setItem('originatingPage', window.location.href);
    });
  });
  
  setupClickOutsideHandler();
  initializeAudioElements();
}

function setupAudioListeners() {
  // Set up basic controls with a map
  const audioControls = [
    ["play-pause-button", togglePlayPause],
    ["toggle-read-aloud", toggleReadAloud],
    ["audio-previous", playPreviousAudio],
    ["audio-next", playNextAudio],
    ["read-aloud-speed", togglePlayBarSettings]
  ];
  
  audioControls.forEach(([id, handler]) => {
    const element = elementCache.get(id);
    if (element) element.addEventListener("click", handler);
  });

  // Speed buttons
  const speedButtons = elementCache.getAll(".read-aloud-change-speed");
  speedButtons.forEach(button => {
    button.addEventListener("click", changeAudioSpeed);
  });
}

async function initializeUIComponents() {
  try {
    // Layout and visual components - always initialize these
    await lazyLoad.load('zoom', () => Promise.resolve({ init: initializeZoomController }))
      .then(module => module.init());
    initializeSidebar();
    initializeTabs();
    adjustLayout();
    
    // Initialize features based on config
    if (window.appConfig?.features) {
      // Audio features
      if (isFeatureEnabled('readAloud')) {
        initializePlayBar();
        initializeAudioSpeed();
        setupAudioListeners();
        initializeTtsQuickToggle();
        
        // Show play bar if needed
        if (state.readAloudMode) {
          const playBar = elementCache.get("play-bar");
          if (playBar) playBar.classList.remove("hidden");
        }
      }
      
      // Glossary
      if (isFeatureEnabled('glossary')) {
        initializeGlossary();
      }
      
      // ELI5
      if (isFeatureEnabled('eli5')) {
        initializeEli5();
      }
      
      // Notepad
      if (isFeatureEnabled('notepad')) {
        initializeNotepad();
      }

      // Character display
      if (isFeatureEnabled('characterDisplay')) {
        initCharacterDisplay();
        displayCharacterInSettings();
      }

      // Highlighting text
      if (isFeatureEnabled('highlight')) {
        initializeWordByWordHighlighter();
      }

      // Load state modes - only if features are enabled
      const stateInitTasks = [];
      
      if (isFeatureEnabled('easyRead')) stateInitTasks.push(loadEasyReadMode);
      if (isFeatureEnabled('state')) stateInitTasks.push(loadStateMode);
      if (isFeatureEnabled('signLanguage')) {
        initializeSignLanguage();
        stateInitTasks.push(loadSignLanguageMode);
      }
      if (isFeatureEnabled('notepad')) {
        stateInitTasks.push(loadSavedNotes());
        stateInitTasks.push(loadNotepad);
      }
      if (isFeatureEnabled('autoplay')) { 
        setAutoplayContainerVisibility(true);
        stateInitTasks.push(loadAutoplayState);
      } else {
        setAutoplayContainerVisibility(false);
      }
      if (isFeatureEnabled('describeImages')){
        setDescribeImagesContainerVisibility(true);
        stateInitTasks.push(loadDescribeImagesState);
      }
      if (isFeatureEnabled("autoplay") || isFeatureEnabled("describeImages")) {
        updateTtsOptionsContainerVisibility(true);
      } else {
        updateTtsOptionsContainerVisibility(false);
      }
      // if (isFeatureEnabled('glossary')) stateInitTasks.push(loadGlossaryState);
      if (isFeatureEnabled('eli5')) {
        handleEli5Popup();
      }
      if (stateInitTasks.length > 0) {
        await Promise.all(stateInitTasks.map(task => Promise.resolve().then(task)));
      }
      
    } else {
      // Fallback to the original behavior if config isn't available
      const initGroups = [
        // All your original initialization groups
      ];
      await Promise.all(initGroups.map(group => group()));
    }
    
    // Activities should be initialized after UI components
    if (isFeatureEnabled('activities', true)) {
      prepareActivity();
    }
    loadToggleButtonState();
  } catch (error) {
    console.error('Error initializing UI components:', error);
  }
}

const finalizeInitialization = async () => {
  const navPopup = elementCache.get("navPopup");
  const sidebar = elementCache.get("sidebar");

  setTimeout(async () => {
    // Show navigation and sidebar
    if (navPopup) navPopup.classList.remove("hidden");
    if (sidebar) sidebar.classList.remove("hidden");

    // Initialize autoplay if needed
    if (isFeatureEnabled('readAloud') && isFeatureEnabled('autoplay')) {
      initializeAutoplay();
    }
    
    // Run these tasks in parallel
    const finalTasks = [
      // Navigation
      () => initializeNavigation(),
      
      // Reference page functionality
      () => initializeReferencePage(),
      
      // Glossary terms
      () => {
        if (isFeatureEnabled('glossary')) {
          highlightGlossaryTerms();
        }
      },
      
      // Math rendering
      () => {
        if (window.MathJax) {
          window.MathJax.typeset();
        }
      },
      
      // Adjust layout after all content is ready
      () => {
        adjustLayout();
      },
      
      // Initialize tutorial via lazy loading
      async () => {
        const tutorialModule = await lazyLoad.load('tutorial', () => import('./modules/tutorial.js'));
        if (tutorialModule.init) {
          tutorialModule.init();
        }
      },
      
      // Analytics
      async () => {
        // Check if analytics is enabled in config
        if (window.appConfig?.analytics?.enabled) {
          const analyticsModule = await lazyLoad.load('analytics', () => import('./modules/analytics.js'));
          analyticsModule.initMatomo(window.appConfig.analytics);
        }
}
    ];
    
    // Execute all tasks in parallel
    await Promise.all(finalTasks.map(task => Promise.resolve().then(task)));
  }, 100);
};

/**
 * Displays character information in the settings menu
 */
function displayCharacterInSettings() {
  // Get the character information from localStorage
  const characterInfo = localStorage.getItem('characterInfo');
  const studentID = localStorage.getItem('studentID');

  // Show the entire character-profile-row if it is hidden
  const profileRow = document.getElementById('character-profile-row');
  if (profileRow && profileRow.classList.contains('hidden')) {
    profileRow.classList.remove('hidden');
  }
  
  if (characterInfo) {
    try {
      const character = JSON.parse(characterInfo);
      const emojiElement = elementCache.get('settings-character-emoji');
      const nameElement = elementCache.get('settings-character-name');
      const studentIDElements = elementCache.getAll('#student-id');
      
      if (emojiElement && nameElement) {
        emojiElement.textContent = character.emoji || '👤';
        nameElement.textContent = character.fullName || localStorage.getItem('nameUser') || 'Guest';
      }
      
      // Update any student ID elements in the settings
      if (studentID && studentIDElements.length > 0) {
        studentIDElements.forEach(element => {
          if (element) element.textContent = studentID;
        });
      }
    } catch (e) {
      console.error('Error parsing character information:', e);
    }
  }
}

// Lazy load module function
const lazyLoad = {
  _modules: {},
  
  async load(name, loader) {
    if (!this._modules[name]) {
      this._modules[name] = await loader();
    }
    return this._modules[name];
  }
};

// Add this function near your setupConfig function
export const isFeatureEnabled = (featureName, defaultValue = false) => {
  // Access from appConfig if available, otherwise fall back to state
  if (typeof window.appConfig?.features?.[featureName] !== 'undefined') {
    return window.appConfig.features[featureName] === true;
  }
  
  // Fall back to state object
  const stateKey = `${featureName}Enabled`;
  if (typeof state[stateKey] !== 'undefined') {
    return state[stateKey] === true;
  }
  
  return defaultValue;
}


// Export necessary functions
export {
  changeAudioSpeed,
  handleKeyboardShortcuts,
  initializeAutoplay,
  loadAutoplayState,
  loadDescribeImagesState,
  playNextAudio,
  playPreviousAudio,
  toggleEli5Mode,
  togglePlayPause,
  toggleReadAloud,
};
