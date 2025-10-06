import { state, setState } from '../state.js';
import { playActivitySound } from '../audio.js';
import { updateSubmitButtonAndToast, ActivityTypes } from '../utils.js';
import { translateText } from '../translations.js';
import { executeMail } from './send-email.js';
import { updateResetButtonVisibility } from '../../activity.js';

export const prepareMultipleChoice = (section) => {
    restorePreviousSelection(section); // Restaurar selección previa

    const activityOptions = section.querySelectorAll(".activity-option");

    // Remove any previous event listeners
    activityOptions.forEach((option) => {
        const newOption = option.cloneNode(true);
        option.parentNode.replaceChild(newOption, option);
    });

    // Add new event listeners
    section.querySelectorAll(".activity-option").forEach((option) => {
        option.addEventListener("click", () => selectOption(option));

        // Keyboard event handling - Enter and Space trigger option selection
        option.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault(); // Prevent scrolling on space
                selectOption(option);
            }
        });

        // Set proper ARIA attributes
        const optionLetter = option.querySelector('.option-letter')?.textContent || '';
        const imgAlt = option.querySelector('img')?.alt || '';

        // Create a more descriptive label that includes the image description
        option.setAttribute('aria-label', `Option ${optionLetter}: ${imgAlt}`);
        option.setAttribute('role', 'radio');
        option.setAttribute('aria-checked', 'false');


        // Add hover effect classes
        option.classList.add(
            'cursor-pointer',
            'transition-all',
            'duration-200',
            'hover:shadow-md',
            'focus:outline-none',
            'focus:ring-2',
            'focus:ring-blue-500',
            'focus:ring-opacity-50'
        );

        // Style option label
        const label = option.querySelector("span");
        if (label) {
            label.classList.add(
                'px-4',
                'py-2',
                'rounded-full',
                'font-medium',
                'transition-colors',
                'duration-200'
            );
        }
    });

    // Set proper radiogroup role on the container
    const radioGroup = section.querySelector('[role="group"]');
    if (radioGroup) {
        radioGroup.setAttribute('role', 'radiogroup');
        radioGroup.setAttribute('aria-labelledby', 'question-label');
    }
};
const saveSelectionState = (option) => {
    const activityId = location.pathname
        .substring(location.pathname.lastIndexOf("/") + 1)
        .split(".")[0];

    const areaId = option.closest("[data-area-id]")?.getAttribute("data-area-id") || "default";
    const storageKey = `${activityId}_${areaId}_multipleChoice`;

    const selectedData = {
        question: option.getAttribute("data-activity-item"),
        value: option.querySelector('input[type="radio"]').value,
        areaId: areaId
    };

    localStorage.setItem(storageKey, JSON.stringify(selectedData));

    console.log(`Selection saved: ${storageKey}`, selectedData);
};

const restorePreviousSelection = (section) => {
    const activityId = location.pathname
        .substring(location.pathname.lastIndexOf("/") + 1)
        .split(".")[0];

    const areaId = section.querySelector("[data-area-id]")?.getAttribute("data-area-id") || "default";
    const storageKey = `${activityId}_${areaId}_multipleChoice`;

    const savedSelection = localStorage.getItem(storageKey);
    if (savedSelection) {
        const { value } = JSON.parse(savedSelection);

        const selectedOption = [...section.querySelectorAll(".activity-option")].find(option =>
            option.querySelector('input[type="radio"]').value === value
        );

        if (selectedOption) {
            selectClickedOption(selectedOption);
            setState('selectedOption', selectedOption);
            console.log(`Selection restored: ${storageKey}`, savedSelection);
        }
    }
};


const selectOption = (option) => {
    console.log("=== Selecting option ===");

    // Clear all validation styling before selecting a new option
    clearAllValidationStyling();

    const activityItem = getActivityItem(option);
    console.log("Option selected:", option);
    console.log("Activity item found:", activityItem);

    const radioGroup = option.closest('[role="radiogroup"]') || option.closest('[role="group"]');
    if (!radioGroup) {
        console.log("No radio group found");
        return;
    }

    resetOptions(radioGroup);
    selectClickedOption(option);
    setState('selectedOption', option);

    // Update ARIA attributes
    radioGroup.querySelectorAll('.activity-option').forEach(opt => {
        opt.setAttribute('aria-checked', 'false');
    });
    option.setAttribute('aria-checked', 'true');

    // Announce selection to screen readers
    const optionLetter = option.querySelector('.option-letter')?.textContent || '';
    const liveRegion = document.getElementById('toast');
    if (liveRegion) {
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.textContent = `Option ${optionLetter} selected`;
        setTimeout(() => { liveRegion.textContent = ''; }, 1000);
    }

    // Guardar en localStorage
    saveSelectionState(option);
};

// New function to clear all validation styling
const clearAllValidationStyling = () => {
    // Reset all validation marks
    document.querySelectorAll(".validation-mark").forEach(mark => {
        mark.classList.add('hidden');
        mark.textContent = '';
    });
    
    // Reset all option containers
    document.querySelectorAll(".activity-option").forEach(option => {
        option.classList.remove('bg-green-50', 'bg-red-50');
        option.removeAttribute('aria-invalid');
        
        // Reset all feedback containers
        const feedback = option.querySelector('.feedback-container');
        if (feedback) {
            feedback.classList.add('hidden');
            
            // Clear feedback content
            const feedbackIcon = feedback.querySelector('.feedback-icon');
            const feedbackText = feedback.querySelector('.feedback-text');
            
            if (feedbackIcon) {
                feedbackIcon.className = 'feedback-icon';
                feedbackIcon.textContent = '';
            }
            
            if (feedbackText) {
                feedbackText.className = 'feedback-text';
                feedbackText.textContent = '';
            }
        }
        
        // Reset letter circle styling
        const letterCircle = option.querySelector('.option-letter')?.parentElement;
        if (letterCircle) {
            letterCircle.className = 'w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center';
        }
        
        // Reset the letter color
        const letter = option.querySelector('.option-letter');
        if (letter) {
            letter.className = 'option-letter text-gray-500';
        }
    });
    
    // Announce change to screen readers
    const validationResults = document.getElementById('validation-results-announcement');
    if (validationResults) {
        validationResults.textContent = translateText("Selección cambiada, vuelve a enviar tu respuesta");
    }
};

const resetOptions = (radioGroup) => {
    radioGroup.querySelectorAll(".activity-option").forEach((opt) => {
        console.log("Resetting option:", opt);

        // Reset aria attributes
        opt.setAttribute('aria-checked', 'false');

        // Reset letter circle styling
        const letterCircle = opt.querySelector('.option-letter')?.parentElement;
        if (letterCircle) {
            letterCircle.className = 'w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center';
        }

        // Reset the letter color
        const letter = opt.querySelector('.option-letter');
        if (letter) {
            letter.className = 'option-letter text-gray-500';
        }

        // Reset option container
        opt.classList.remove('bg-green-50', 'bg-red-50');

        // Hide feedback
        const feedback = opt.querySelector('.feedback-container');
        if (feedback) {
            feedback.classList.add('hidden');
        }
    });
};

const selectClickedOption = (option) => {
    const input = option.querySelector('input[type="radio"]');
    if (input) {
        input.checked = true;
    }

    // Update ARIA state
    option.setAttribute('aria-checked', 'true');

    // Style the letter circle as selected
    const letterCircle = option.querySelector('.option-letter')?.parentElement;
    if (letterCircle) {
        letterCircle.className = 'w-8 h-8 rounded-full border-2 border-blue-500 bg-blue-500 flex items-center justify-center';
    }

    // Change the letter color to white
    const letter = option.querySelector('.option-letter');
    if (letter) {
        letter.className = 'option-letter text-white';
    }
};

const getActivityItem = (element) => {
    let activityItem = element.getAttribute('data-activity-item');

    if (!activityItem) {
        const input = element.querySelector('input[type="radio"]');
        if (input) {
            activityItem = input.getAttribute('data-activity-item');
        }

        if (element.tagName === 'INPUT') {
            const label = element.closest('.activity-option');
            if (label) {
                activityItem = label.getAttribute('data-activity-item') || activityItem;
            }
        }
    }

    return activityItem;
};

export const checkMultipleChoice = () => {
    console.log("=== Starting validation ===");

    if (!state.selectedOption) {
        console.log("No option selected");
        
        // Add announcement for screen readers
        const liveRegion = document.getElementById('toast');
        if (liveRegion) {
            liveRegion.setAttribute('aria-live', 'assertive');
            liveRegion.textContent = translateText("select-option-first");
            liveRegion.classList.remove('hidden');
            setTimeout(() => {
                liveRegion.classList.add('hidden');
            }, 3000);
        }
        
        return;
    }

    const input = state.selectedOption.querySelector('input[type="radio"]');
    const dataActivityItem = getActivityItem(state.selectedOption);
    const isCorrect = correctAnswers[dataActivityItem];

    styleSelectedOption(state.selectedOption, isCorrect);
    showFeedback(state.selectedOption, isCorrect);
    // Add this line to update reset button visibility
    if (typeof updateResetButtonVisibility === 'function') {
        updateResetButtonVisibility();
      }
    updateSubmitButtonAndToast(
        isCorrect,
        translateText("next-activity"),
        ActivityTypes.MULTIPLE_CHOICE
    );
};

const styleSelectedOption = (option, isCorrect) => {
    const letterCircle = option.querySelector('.option-letter').parentElement;
    letterCircle.className = `w-8 h-8 rounded-full border-2 flex items-center justify-center ${isCorrect
        ? 'border-green-500 bg-green-500 text-white'
        : 'border-red-500 bg-red-500 text-white'
        }`;

    option.classList.add(isCorrect ? 'bg-green-50' : 'bg-red-50');

    // Update ARIA for feedback status
    option.setAttribute('aria-invalid', isCorrect ? 'false' : 'true');
};

const showFeedback = (option, isCorrect) => {
    const feedbackContainer = option.querySelector('.feedback-container');
    const feedbackIcon = feedbackContainer.querySelector('.feedback-icon');
    const feedbackText = feedbackContainer.querySelector('.feedback-text');

    feedbackContainer.classList.remove('hidden');

    const activityId = location.pathname
    .substring(location.pathname.lastIndexOf("/") + 1)
    .split(".")[0];
    let key = activityId + "-intentos";
    let intentCount = localStorage.getItem(key);
    if (intentCount === null) {
            localStorage.setItem(key, "0");
            intentCount = 0;
        } else {
            intentCount = parseInt(intentCount, 10);
        }

        intentCount++;
        localStorage.setItem(key, intentCount.toString()); 

    if (isCorrect) {
        feedbackIcon.className = 'feedback-icon w-5 h-5 rounded-full flex items-center justify-center text-sm bg-green-100 text-green-700';
        feedbackIcon.textContent = '✓';
        feedbackText.className = 'feedback-text text-sm font-medium text-green-700';
        feedbackText.textContent = translateText('multiple-choice-correct-answer');
        
        // Set ARIA attributes for feedback
        feedbackContainer.setAttribute('role', 'status');
        feedbackContainer.setAttribute('aria-live', 'polite');
        
        playActivitySound('success');

        // Recuperar el arreglo de actividades completadas del localStorage
        const storedActivities = localStorage.getItem("completedActivities");
        let completedActivities = storedActivities ? JSON.parse(storedActivities) : []; 
    
        const namePage = localStorage.getItem("namePage");
        const timeDone = new Date().toLocaleString("es-ES");
        const newActivityId = `${activityId}-${namePage}-${intentCount}-${timeDone}`;
    
        // Remover cualquier entrada anterior con el mismo activityId
        completedActivities = completedActivities.filter(id => !id.startsWith(`${activityId}-`));
    
        // Agregar la nueva entrada actualizada
        completedActivities.push(newActivityId);
    
        // Guardar en localStorage
        localStorage.setItem("completedActivities", JSON.stringify(completedActivities));
    
        localStorage.setItem("namePage", document.getElementsByTagName("h1")[0].innerText)
        executeMail(ActivityTypes.MULTIPLE_CHOICE);
    } else {
        feedbackIcon.className = 'feedback-icon w-5 h-5 rounded-full flex items-center justify-center text-sm bg-red-100 text-red-700';
        feedbackIcon.textContent = '✗';
        feedbackText.className = 'feedback-text text-sm font-medium text-red-700';
        feedbackText.textContent = translateText('multiple-choice-try-again');
        
        // Set ARIA attributes for feedback
        feedbackContainer.setAttribute('role', 'alert');
        
        playActivitySound('error');
    }
};