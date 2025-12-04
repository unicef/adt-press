/**
 * @module navigation
 * @description
 * Handles navigation events, state saving/restoring, keyboard shortcuts, and navigation UI logic.
 */
import { setCookie, getCookie } from "./cookies.js";
import { cacheInterfaceElements, toggleSidebar, setNavVisibility, formatNavigationItems } from "./interface.js";
import { trackNavigation } from "./analytics.js";
import { cycleLanguage } from "./translations.js";

const PAGE_LIST_SELECTOR = '.nav__list[data-nav-type="pages"]';
const TOC_LIST_SELECTOR = '.nav__list[data-nav-type="toc"]';
const NAV_TAB_COOKIE = "navActiveTab";
const NAV_TABS = ["toc", "pages"];
const DEFAULT_NAV_TAB = "toc";

let navigationData = { pages: [], toc: [] };
const getInitialNavTab = () => {
  const savedTab = getCookie(NAV_TAB_COOKIE);
  return NAV_TABS.includes(savedTab) ? savedTab : DEFAULT_NAV_TAB;
};

let activeNavTab = getInitialNavTab();

const getPageListElement = () => document.querySelector(PAGE_LIST_SELECTOR);

const getNavLinks = () => document.querySelectorAll(`${PAGE_LIST_SELECTOR} .nav__list-link`);

const enhancePageList = (pages) => {
  if (!Array.isArray(pages)) {
    return [];
  }

  return pages.map((page, index) => {
    const pdfPageNumber = page?.page_number ?? null;
    const sequentialIndex = index + 1;
    const displayLabel = sequentialIndex === 1 ? `${sequentialIndex} (Cover)` : String(sequentialIndex);

    return {
      ...page,
      page_label: String(sequentialIndex),
      sequential_index: sequentialIndex,
      pdf_page_number: pdfPageNumber,
      display_label: displayLabel,
    };
  });
};

const renderNavigationLists = () => {
  buildTableOfContents();
  buildPageList();
  activateNavTab(activeNavTab);
};

const buildTableOfContents = () => {
  const tocList = document.querySelector(TOC_LIST_SELECTOR);
  if (!tocList) return;

  tocList.innerHTML = "";
  navigationData.toc.forEach((chapter, index) => {
    const item = document.createElement("li");
    item.classList.add("nav__list-item", "border-b", "border-gray-300", "flex", "items-center");

    const link = document.createElement("a");
    link.classList.add(
      "nav__toc-link",
      "flex-grow",
      "flex",
      "items-center",
      "w-full",
      "h-full",
      "p-2",
      "py-3",
      "hover:bg-blue-50",
      "transition",
      "text-gray-700"
    );

    link.href = chapter.href;
    if (chapter.chapter_id) {
      link.setAttribute("data-text-id", chapter.chapter_id);
    }

    const baseTitle = chapter.title || chapter.chapter_id || chapter.href;
    const displayIndex = `${index + 1}.`;

    const indexSpan = document.createElement("span");
    indexSpan.classList.add("text-gray-500", "font-semibold", "mr-3", "tabular-nums");
    indexSpan.textContent = displayIndex;

    const titleSpan = document.createElement("span");
    if (chapter.chapter_id) {
      titleSpan.setAttribute("data-id", chapter.chapter_id);
    }
    titleSpan.classList.add("inline", "text-gray-800");
    titleSpan.textContent = baseTitle;
    link.setAttribute("aria-label", `${displayIndex} ${baseTitle}`);

    link.appendChild(indexSpan);
    link.appendChild(titleSpan);
    item.appendChild(link);
    tocList.appendChild(item);
  });
};

const buildPageList = () => {
  const pageList = getPageListElement();
  if (!pageList) return;

  pageList.innerHTML = "";
  if (!navigationData.pages?.length) {
    return;
  }

  const chapterLookup = navigationData.toc.reduce((acc, chapter, index) => {
    if (!chapter?.section_id) {
      return acc;
    }
    acc[chapter.section_id] = {
      ...chapter,
      displayTitle: chapter.title || chapter.chapter_id || chapter.href,
      index: index + 1,
    };
    return acc;
  }, {});

  const renderedChapters = new Set();

  navigationData.pages.forEach((page) => {
    const chapterInfo = chapterLookup[page.section_id];
    if (chapterInfo && !renderedChapters.has(chapterInfo.section_id)) {
      const headingItem = document.createElement("li");
      headingItem.classList.add(
        "nav__list-heading",
        "px-2",
        "pt-4",
        "pb-2",
        "text-xs",
        "font-semibold",
        "tracking-wide",
        "text-gray-500",
        "uppercase"
      );
      headingItem.dataset.chapterId = chapterInfo.chapter_id || "";
      const headingLabel = chapterInfo.index ? `${chapterInfo.index}. ${chapterInfo.displayTitle}` : chapterInfo.displayTitle;
      headingItem.textContent = headingLabel;
      pageList.appendChild(headingItem);
      renderedChapters.add(chapterInfo.section_id);
    }
    const sequentialLabel = page.page_label || String(page.sequential_index || 1);
    const displayLabel = page.display_label || sequentialLabel;
    const pdfLabel =
      page.pdf_page_number !== undefined && page.pdf_page_number !== null
        ? String(page.pdf_page_number)
        : "";

    const item = document.createElement("li");
    item.classList.add("nav__list-item");
    item.dataset.sectionId = page.section_id;

    const link = document.createElement("a");
    link.classList.add("nav__list-link");
    link.href = page.href;
    link.dataset.pageNumber = sequentialLabel;
    link.dataset.sectionIndex = (page.sequential_index || sequentialLabel).toString();
    link.dataset.pageLabel = sequentialLabel;
    link.dataset.pageDisplayLabel = displayLabel;
    link.dataset.sectionId = page.section_id;
    if (pdfLabel) {
      link.dataset.pdfPage = pdfLabel;
      link.setAttribute("aria-label", `Page ${sequentialLabel}, Print page ${pdfLabel}`);
    } else {
      delete link.dataset.pdfPage;
      link.setAttribute("aria-label", `Page ${sequentialLabel}`);
    }
    link.textContent = displayLabel;

    item.appendChild(link);
    pageList.appendChild(item);
  });

  formatNavigationItems();
};

const activateNavTab = (tab) => {
  if (!tab) return;

  const previousTab = activeNavTab;
  if (previousTab) {
    const previousPanel = document.querySelector(`[data-nav-panel="${previousTab}"]`);
    const previousList = previousPanel?.querySelector('.nav__list');
    if (previousList) {
      setCookie(`navScrollPosition-${previousTab}`, previousList.scrollTop, 7);
    }
  }

  activeNavTab = tab;
  setCookie(NAV_TAB_COOKIE, activeNavTab, 7);

  const tabButtons = document.querySelectorAll('[data-nav-tab]');
  const tabPanels = document.querySelectorAll('[data-nav-panel]');

  tabButtons.forEach((button) => {
    const isActive = button.dataset.navTab === tab;
    button.setAttribute('aria-selected', isActive ? 'true' : 'false');
    button.classList.toggle('bg-white', isActive);
    button.classList.toggle('text-gray-900', isActive);
    button.classList.toggle('shadow', isActive);
    button.classList.toggle('text-gray-500', !isActive);
  });

  tabPanels.forEach((panel) => {
    const isActive = panel.dataset.navPanel === tab;
    panel.classList.toggle('hidden', !isActive);
    panel.setAttribute('aria-hidden', (!isActive).toString());
    if (isActive) {
      const currentList = panel.querySelector('.nav__list');
      if (currentList) {
        const savedPosition = getCookie(`navScrollPosition-${tab}`);
        if (savedPosition) {
          currentList.scrollTop = parseInt(savedPosition, 10);
        }
      }
    }
  });
};

export const initializeNavTabs = () => {
  const tabButtons = document.querySelectorAll('[data-nav-tab]');
  if (!tabButtons.length) return;

  tabButtons.forEach((button) => {
    button.addEventListener('click', () => activateNavTab(button.dataset.navTab));
  });

  activateNavTab(activeNavTab);
};

export const setNavigationData = ({ pages = [], toc = [] }) => {
  const normalizedPages = Array.isArray(pages) ? pages : [];
  navigationData = {
    pages: enhancePageList(normalizedPages),
    toc: Array.isArray(toc) ? toc : [],
  };
  renderNavigationLists();
};

export const getNavigationData = () => navigationData;

/**
 * Handles navigation link/button clicks, saves state, and transitions to the target page.
 * @param {Event} event - The navigation event.
 */
export const handleNavigation = (event) => {
  const navLink = event.target.closest(".nav__list-link, .nav__toc-link");
  const isNavButton =
    navLink || event.target.id === "back-button" || event.target.id === "forward-button";

  if (isNavButton) {
    event.preventDefault();
    const trigger = navLink || event.target;
    const targetHref = trigger.href || trigger.getAttribute("data-href");

    if (!targetHref) {
      console.error(
        "Navigation target URL is null or undefined for element:",
        trigger
      );
      return;
    }

    // Cache current interface state
    cacheInterfaceElements();

    // Save current page state
    savePageState();

    const mainContent = document.querySelector('body > .container');
    if (mainContent) {
      mainContent.classList.add("opacity-0");
    }

    setTimeout(() => {
      window.location.href = targetHref;
    }, 150);
  }
};

/**
 * Saves the current page state (sidebar, scroll positions) to sessionStorage.
 */
export const savePageState = () => {
  const state = {
    sidebarState: getCookie("sidebarState"),
    scrollPosition: window.scrollY,
    navScrollPosition: getPageListElement()?.scrollTop || 0,
  };

  sessionStorage.setItem("pageState", JSON.stringify(state));
};

/**
 * Restores the page state (sidebar, scroll positions) from sessionStorage.
 */
export const restorePageState = () => {
  try {
    const savedState = sessionStorage.getItem("pageState");
    if (!savedState) return;

    const state = JSON.parse(savedState);

    // Restore scroll positions
    setTimeout(() => {
      window.scrollTo(0, state.scrollPosition);
      const navList = getPageListElement();
      if (navList) {
        navList.scrollTop = state.navScrollPosition;
      }
    }, 100);
  } catch (error) {
    console.error("Error restoring page state:", error);
  }
};

/**
 * Sets the navigation state (open/closed) and highlights the active link.
 * @param {boolean} state - Whether navigation should be open.
 */
export const setNavState = (state) => {
  const navList = getPageListElement();
  const navLinks = getNavLinks();

  if (!navList || !navLinks) {
    return;
  }

  // Use the shared visibility function to handle most operations
  //setNavVisibility(state);

  // Navigation-specific behaviors
  const currentPath = window.location.pathname.split("/").pop() || "index.html";
  handleActiveLink(state, currentPath, navLinks, navList);

  console.log("setNavState - Nav is:", state ? "open" : "closed");
};

/**
 * Sets the navigation toggle button's aria-expanded attribute.
 * @param {boolean} navState - Navigation open state.
 * @param {HTMLElement} navToggle - The toggle button element.
 * @private
 */
const setNavToggle = (navState, navToggle) => {
  if (!navToggle) return;
  navToggle.setAttribute("aria-expanded", navState ? "true" : "false");
};

/**
 * Sets the navigation popup's state and accessibility attributes.
 * @param {HTMLElement} navPopup - The navigation popup element.
 * @param {boolean} state - Whether navigation should be open.
 */
export const setNavPopupState = (navPopup, state) => {
  if (!state) {
    navPopup.classList.add("-translate-x-full");
    navPopup.setAttribute("aria-expanded", "false");
    navPopup.setAttribute("inert", "");
    navPopup.classList.remove("left-2");
  } else {
    navPopup.classList.remove("-translate-x-full");
    navPopup.setAttribute("aria-expanded", "true");
    navPopup.removeAttribute("inert");
    navPopup.classList.add("left-2");
  }
};

/**
 * Toggles the navigation popup open/closed and updates toggle button.
 */
export const toggleNav = (newState = null) => {
  const navPopup = document.getElementById("navPopup");
  const navList = getPageListElement();
  const navLinks = getNavLinks();
  const navToggle = document.querySelector(".nav__toggle");

  if (!navList || !navToggle || !navLinks || !navPopup) {
    return;
  }

  // Filter out non-boolean values (like PointerEvent objects)
  const validState = typeof newState === 'boolean' ? newState : null;

  // Determine current state
  let isNavOpen;
  if (validState !== null) {
    isNavOpen = !validState;
  } else {
    isNavOpen = getCookie("navState") === "open";
  }
  const currentPath = window.location.pathname.split("/").pop() || "index.html";

  // Toggle navigation visibility and toggle button
  setNavVisibility(!isNavOpen);
  setNavToggle(!isNavOpen, navToggle);

  // Additional navigation-specific operations
  handleActiveLink(!isNavOpen, currentPath, navLinks, navList);

  // Log state for debugging
  console.log("toggleNav - Nav is now:", !isNavOpen ? "open" : "closed");
};

/**
 * Highlights the active navigation link and scrolls it into view if needed.
 * @param {boolean} isNavOpen - Whether navigation is open.
 * @param {string} currentPath - The current page path.
 * @param {NodeList} navLinks - List of navigation link elements.
 * @param {HTMLElement} navList - The navigation list element.
 * @private
 */
const handleActiveLink = (isNavOpen, currentPath, navLinks, navList) => {
  if (!isNavOpen || !navList) return;

  const activeLink = Array.from(navLinks).find(
    (link) => link.getAttribute("href") === currentPath
  );

  if (activeLink) {
    activeLink.setAttribute("tabindex", "0");

    setTimeout(() => {
      const linkRect = activeLink.getBoundingClientRect();
      const navRect = navList.getBoundingClientRect();
      const isInView =
        linkRect.top >= navRect.top && linkRect.bottom <= navRect.bottom;

      if (!isInView) {
        activeLink.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      activeLink.focus({ preventScroll: true });
    }, 100);
  }
};

/* export const updateNavPopupState = (navPopup) => {
  const isHidden = navPopup.classList.toggle("-translate-x-full");
  navPopup.setAttribute("aria-expanded", !isHidden ? "true" : "false");
  if (isHidden) {
    navPopup.setAttribute("inert", "");
  } else {
    navPopup.removeAttribute("inert");
  }
  navPopup.classList.toggle("left-2");
}; */

/**
 * Navigates to the next page in the navigation list.
 */
export const nextPage = () => {
  const currentHref = window.location.href.split("/").pop() || "index.html";
  console.log("Current page:", currentHref); // Debug log

  // Get all nav links in order
  const navItems = Array.from(document.querySelectorAll(".nav__list-link"));
  console.log(
    "Available nav items:",
    navItems.map((item) => item.getAttribute("href"))
  ); // Debug log

  // Find current page index
  const currentIndex = navItems.findIndex(
    (item) => item.getAttribute("href") === currentHref
  );
  console.log("Current index:", currentIndex); // Debug log

  if (currentIndex >= 0 && currentIndex < navItems.length - 1) {
    const navList = getPageListElement();
    const scrollPosition = navList?.scrollTop || 0;
    const basePath = window.location.pathname.substring(
      0,
      window.location.pathname.lastIndexOf("/") + 1
    );

    // Save scroll position
    setCookie("navScrollPosition", scrollPosition, 7, basePath);

    // Cache interface state
    cacheInterfaceElements();

    // Fade out content
    const mainContent = document.querySelector('body > .container');
    if (mainContent) {
      mainContent.classList.add("opacity-0");
    }

    // Navigate to next page
    const nextPage = navItems[currentIndex + 1].getAttribute("href");
    const nextPageId = nextPage.split('/').pop();
    trackNavigation(currentHref, nextPageId);
    console.log("Navigating to:", nextPage); // Debug log

    setTimeout(() => {
      window.location.href = nextPage;
    }, 150);
  }
};

/**
 * Navigates to the previous page in the navigation list.
 */
export const previousPage = () => {
  const currentHref = window.location.href.split("/").pop() || "index.html";
  const navItems = Array.from(document.querySelectorAll(".nav__list-link"));
  const currentIndex = navItems.findIndex(
    (item) => item.getAttribute("href") === currentHref
  );

  if (currentIndex > 0) {
    const navList = getPageListElement();
    const scrollPosition = navList?.scrollTop || 0;
    const basePath = window.location.pathname.substring(
      0,
      window.location.pathname.lastIndexOf("/") + 1
    );

    setCookie("navScrollPosition", scrollPosition, 7, basePath);
    cacheInterfaceElements();

    const mainContent = document.querySelector('body > .container');
    if (mainContent) {
      mainContent.classList.add("opacity-0");
    }

    const prevPage = navItems[currentIndex - 1].getAttribute("href");
    const nextPageId = prevPage.split('/').pop().split('.')[0];
    trackNavigation(currentHref, nextPageId);

    setTimeout(() => {
      window.location.href = prevPage;
    }, 150);
  }
};

/**
 * Handles keyboard shortcuts for navigation and sidebar toggling.
 * @param {KeyboardEvent} event - The keyboard event.
 */
export function handleKeyboardShortcuts(event) {
  console.log("handleKeyboardShortcuts called with key:", event.key);

  const activeElement = document.activeElement;
  console.log(
    "Active element:",
    activeElement.tagName,
    "ID:",
    activeElement.id
  );

  // More specific check for text input elements
  const isInTextBox =
    (activeElement.tagName === "INPUT" &&
      activeElement.type !== "checkbox" &&
      activeElement.type !== "radio") ||
    activeElement.tagName === "TEXTAREA" ||
    activeElement.isContentEditable;

  // Check if any modifier keys are pressed (except Alt+Shift)
  const hasModifiers =
    event.ctrlKey || event.metaKey || (event.altKey && !event.shiftKey);

  console.log("isInTextBox:", isInTextBox, "hasModifiers:", hasModifiers);

  // Exit if in text input (but not checkbox/radio) or if unwanted modifier keys are pressed
  if (
    (isInTextBox && !activeElement.id.startsWith("toggle-")) ||
    hasModifiers
  ) {
    console.log("Exiting early due to text input or modifiers");
    return;
  }

  // Get toggle states
  const readAloudMode = getCookie("readAloudMode") === "true";
  const easyReadMode = getCookie("easyReadMode") === "true";
  const eli5Mode = getCookie("eli5Mode") === "true";

  console.log(
    "Current modes - readAloud:",
    readAloudMode,
    "easyRead:",
    easyReadMode,
    "eli5:",
    eli5Mode
  );

  // Handle navigation keys with null checks
  if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
    console.log(`${event.key} pressed - handling navigation`);
    event.preventDefault();

    // Check if navigation is possible before proceeding
    const navItems = document.querySelectorAll(".nav__list-link");
    if (!navItems.length) return;

    if (event.key === "ArrowRight") {
      nextPage();
    } else {
      previousPage();
    }
    return;
  }

  switch (event.key) {
    case "x":
      console.log("X key pressed - toggling nav");
      event.preventDefault();
      toggleNav();
      break;
    case "a":
      console.log("A key pressed - toggling sidebar");
      event.preventDefault();
      toggleSidebar();
      break;
    case "z":
      console.log("Z key pressed - cycling language");
      event.preventDefault();
      cycleLanguage();
      break;
    case "Escape":
      console.log("Escape key pressed - closing nav");
      event.preventDefault();
      escapeKeyPressed();
      break;
  }

  // Handle Alt+Shift shortcuts separately
  if (event.altKey && event.shiftKey) {
    console.log("Alt+Shift modifier detected");
    console.log("Key pressed:", event.key, "Key code:", event.code);

    //const key = event.key.toLowerCase();
    switch (event.code) {
      case "KeyX":
        console.log("Alt+Shift+X pressed - toggling nav");
        event.preventDefault();
        toggleNav();
        break;
      case "KeyA":
        console.log("Alt+Shift+A pressed - toggling sidebar");
        event.preventDefault();
        toggleSidebar();
        break;
      case "KeyZ":
        console.log("Alt+Shift+Z pressed - cycling language");
        event.preventDefault();
        cycleLanguage();
        break;
    }
    return;
  }
}

/**
 * Handles Escape key to close nav/sidebar and focus main content.
 * @private
 */
const escapeKeyPressed = () => {
  const navPopup = document.getElementById("navPopup");
  const sidebar = document.getElementById("sidebar");
  const content = document.querySelector("body > .container");

  // Check if nav is open
  if (navPopup && navPopup.getAttribute("aria-expanded") === "true") {
    // Close nav using the proper function
    setNavVisibility(false);
  }
  // Check if sidebar is open
  else if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {
    toggleSidebar();
  }
  // Move focus to main content
  if (content) {
    content.setAttribute("tabindex", "-1");
    content.focus();
  }
};

/**
 * Sets up a click handler to close nav/sidebar when clicking outside.
 */
export const setupClickOutsideHandler = () => {
  document.addEventListener('click', (event) => {
    const navPopup = document.getElementById('navPopup');
    const sidebar = document.getElementById('sidebar');
    const navToggle = document.querySelector('.nav__toggle');
    const sidebarToggle = document.getElementById('open-sidebar');
    const content = document.querySelector('body > .container');

    // Check if nav menu is open using aria-expanded attribute
    const isNavOpen = navPopup && navPopup.getAttribute("aria-expanded") === "true";

    // Check if sidebar is open
  const isSidebarOpen = sidebar && sidebar.getAttribute('aria-expanded') === 'true';

    // If neither menu is open, no action needed
    if (!isNavOpen && !isSidebarOpen) {
      return;
    }

    // Check if click is outside the navigation menu
    const clickedOutsideNav = isNavOpen &&
      !navPopup.contains(event.target) &&
      (!navToggle || !navToggle.contains(event.target));

    // Check if click is outside the sidebar
    const clickedOutsideSidebar = isSidebarOpen &&
      !sidebar.contains(event.target) &&
      (!sidebarToggle || !sidebarToggle.contains(event.target));

    // Close navigation if clicked outside
    if (clickedOutsideNav) {
      toggleNav();
    }

    // Close sidebar if clicked outside
    if (clickedOutsideSidebar) {
      toggleSidebar();
    }

    // Focus main content if a menu was closed
    if ((clickedOutsideNav || clickedOutsideSidebar) && content) {
      content.setAttribute('tabindex', '-1');
      content.focus();

      // Announce to screen readers (if your announceToScreenReader function is available)
      try {
        const { announceToScreenReader } = require('./ui_utils.js');
        announceToScreenReader('Menú cerrado');
      } catch (e) {
        // Function not available, continue silently
      }
    }
  });
};