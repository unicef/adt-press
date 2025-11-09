import { playActivitySound } from '../audio.js';
import { updateSubmitButtonAndToast, provideFeedback, ActivityTypes } from '../utils.js';
import { clearInputValidationFeedback } from './fill_in_blank.js';
import TextValidator from './textvalidator.js';

const validator = new TextValidator();

export const prepareOpenEnded = (section) => {
    const inputs = section.querySelectorAll('input[type="text"], textarea');
    setupInputListeners(inputs);
    loadInputState(inputs);
    initializeDictionary();
    return inputs;
};

async function initializeDictionary() {
    // Initialize the TextValidator dictionary early
    console.log('Pre-initializing TextValidator dictionary...');
    const textValidator = new TextValidator();
    await textValidator.ensureInitialized();
    console.log('TextValidator dictionary pre-initialized with',
        textValidator.spanishWords ? textValidator.spanishWords.size : 0, 'words');

    // Store the validator in a global property so it can be accessed elsewhere
    window.globalTextValidator = textValidator;
}

const setupInputListeners = (inputs) => {
    inputs.forEach(input => {
        // Remove existing listeners to prevent duplicates
        input.removeEventListener('input', handleInputChange);
        input.removeEventListener('focus', handleInputFocus);
        input.removeEventListener('blur', handleInputBlur);

        // Add listeners
        input.addEventListener('input', handleInputChange);
        input.addEventListener('focus', handleInputFocus);
        input.addEventListener('blur', handleInputBlur);
    });
};

const handleInputChange = (event) => {
    const input = event.target;
    console.log('Open-ended input change detected, clearing feedback');

    // Clear validation feedback when input changes
    clearInputValidationFeedback(input);

    saveInputState(input);
};

const handleInputFocus = (event) => {
    event.target.classList.add('border-blue-500', 'ring-2', 'ring-blue-200');
};

const handleInputBlur = (event) => {
    event.target.classList.remove('border-blue-500', 'ring-2', 'ring-blue-200');
};

const saveInputState = (input) => {
    const activityId = location.pathname
        .substring(location.pathname.lastIndexOf("/") + 1)
        .split(".")[0];
    // Try data-aria-id first, fall back to id attribute
    const inputId = input.getAttribute("data-aria-id") || input.id || input.name;
    
    if (!inputId) {
        console.warn('Input has no data-aria-id, id, or name attribute:', input);
        return;
    }
    
    const localStorageKey = `${activityId}_${inputId}`;
    localStorage.setItem(localStorageKey, input.value);
};

export const loadInputState = (inputs) => {
    inputs.forEach((input) => {
        const activityId = location.pathname
            .substring(location.pathname.lastIndexOf("/") + 1)
            .split(".")[0];
        // Try data-aria-id first, fall back to id attribute
        const inputId = input.getAttribute("data-aria-id") || input.id || input.name;
        
        if (!inputId) {
            console.warn('Input has no data-aria-id, id, or name attribute:', input);
            return;
        }
        
        const localStorageKey = `${activityId}_${inputId}`;

        // Only replace content if there's a saved value in localStorage
        const savedValue = localStorage.getItem(localStorageKey);
        if (savedValue !== null) {
            input.value = savedValue;
        }
        // Otherwise, keep the pre-filled content
    });
    
    // Safely get page name from h1 if it exists
    const h1Element = document.querySelector("h1");
    if (h1Element && h1Element.innerText) {
        localStorage.setItem("namePage", h1Element.innerText);
    }
};

export const countUnfilledInputs = (inputs) => {
    let unfilledCount = 0;
    let firstUnfilledInput = null;

    // First, clear any existing feedback to avoid duplication or inconsistencies
    inputs.forEach(input => {
        clearInputValidationFeedback(input);
    });

    // Process each input in sequence
    inputs.forEach((input, index) => {
        const isFilled = input.value.trim() !== "";

        // Apply feedback directly without setTimeout to avoid race conditions
        provideFeedback(input, isFilled, "", ActivityTypes.OPEN_ENDED_ANSWER);

        if (!isFilled) {
            unfilledCount++;
            if (!firstUnfilledInput) {
                firstUnfilledInput = input;
            }
        }

        // Only focus the first unfilled input after all feedback is applied
        if (index === inputs.length - 1 && firstUnfilledInput) {
            setTimeout(() => {
                firstUnfilledInput.focus();
            }, 50);
        }
    });

    return unfilledCount;
};