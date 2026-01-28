/**
 * Alexandria Keyboard Shortcuts Handler
 *
 * Provides keyboard shortcuts for common actions in the Alexandria application:
 * - Ctrl+1-5: Navigate between tabs
 * - Ctrl+K or /: Focus search/query input
 * - ? or Ctrl+/: Show keyboard shortcuts help
 * - Ctrl+Enter: Trigger ingestion (when on ingestion tabs)
 * - Esc: Close help dialog, clear focus
 */

(function() {
    'use strict';

    // Configuration
    const SHORTCUTS = {
        TAB_NAVIGATION: {
            'Digit1': 0,  // Ctrl+1 -> First tab
            'Digit2': 1,  // Ctrl+2 -> Second tab
            'Digit3': 2,  // Ctrl+3 -> Third tab
            'Digit4': 3,  // Ctrl+4 -> Fourth tab
            'Digit5': 4,  // Ctrl+5 -> Fifth tab
        },
        SEARCH_FOCUS: ['KeyK', 'Slash'],           // Ctrl+K or /
        HELP_TOGGLE: ['Slash', 'Shift'],           // ? (Shift+/) or Ctrl+/
        INGESTION_TRIGGER: 'Enter',                 // Ctrl+Enter
        ESCAPE: 'Escape'
    };

    // State management
    let helpDialogVisible = false;

    /**
     * Find the active tab index in Streamlit
     * @returns {number|null} The current active tab index or null
     */
    function getActiveTabIndex() {
        const tabs = document.querySelectorAll('button[data-baseweb="tab"]');
        for (let i = 0; i < tabs.length; i++) {
            if (tabs[i].getAttribute('aria-selected') === 'true') {
                return i;
            }
        }
        return null;
    }

    /**
     * Switch to a specific tab by index
     * @param {number} index - The tab index to switch to
     */
    function switchToTab(index) {
        const tabs = document.querySelectorAll('button[data-baseweb="tab"]');
        if (index >= 0 && index < tabs.length) {
            tabs[index].click();
            return true;
        }
        return false;
    }

    /**
     * Focus on the search/query input field
     * Prioritizes the Speaker's corner query text area
     */
    function focusSearchInput() {
        // Try to find the main query text area in Speaker's corner
        const queryTextarea = document.querySelector('textarea[aria-label*="question"]');
        if (queryTextarea) {
            queryTextarea.focus();
            queryTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return true;
        }

        // Fallback: Try to find any visible text input or textarea
        const textInputs = document.querySelectorAll('input[type="text"]:not([disabled]), textarea:not([disabled])');
        for (const input of textInputs) {
            const rect = input.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                input.focus();
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return true;
            }
        }

        return false;
    }

    /**
     * Trigger ingestion button on ingestion tabs
     * @returns {boolean} True if button was found and clicked
     */
    function triggerIngestion() {
        // Look for buttons with ingestion-related text
        const buttons = document.querySelectorAll('button');
        for (const button of buttons) {
            const text = button.textContent.toLowerCase();
            if (text.includes('ingest') || text.includes('start') || text.includes('process')) {
                // Check if button is visible and not disabled
                const rect = button.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && !button.disabled) {
                    button.click();
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Toggle the keyboard shortcuts help dialog
     */
    function toggleHelpDialog() {
        helpDialogVisible = !helpDialogVisible;

        if (helpDialogVisible) {
            showHelpDialog();
        } else {
            hideHelpDialog();
        }
    }

    /**
     * Show the keyboard shortcuts help dialog
     */
    function showHelpDialog() {
        // Remove existing help dialog if present
        hideHelpDialog();

        const helpDialog = document.createElement('div');
        helpDialog.id = 'keyboard-shortcuts-help';
        helpDialog.innerHTML = `
            <div class="keyboard-help-overlay">
                <div class="keyboard-help-dialog">
                    <div class="keyboard-help-header">
                        <h2>⌨️ Keyboard Shortcuts</h2>
                        <button class="keyboard-help-close" onclick="document.getElementById('keyboard-shortcuts-help').remove(); return false;">&times;</button>
                    </div>
                    <div class="keyboard-help-content">
                        <div class="keyboard-help-section">
                            <h3>Navigation</h3>
                            <div class="keyboard-shortcut-item">
                                <kbd>Ctrl</kbd> + <kbd>1</kbd> to <kbd>5</kbd>
                                <span>Switch between tabs</span>
                            </div>
                        </div>
                        <div class="keyboard-help-section">
                            <h3>Search</h3>
                            <div class="keyboard-shortcut-item">
                                <kbd>Ctrl</kbd> + <kbd>K</kbd> or <kbd>/</kbd>
                                <span>Focus search/query input</span>
                            </div>
                        </div>
                        <div class="keyboard-help-section">
                            <h3>Actions</h3>
                            <div class="keyboard-shortcut-item">
                                <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
                                <span>Trigger ingestion</span>
                            </div>
                        </div>
                        <div class="keyboard-help-section">
                            <h3>Help</h3>
                            <div class="keyboard-shortcut-item">
                                <kbd>?</kbd> or <kbd>Ctrl</kbd> + <kbd>/</kbd>
                                <span>Show/hide this help</span>
                            </div>
                            <div class="keyboard-shortcut-item">
                                <kbd>Esc</kbd>
                                <span>Close help dialog</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(helpDialog);
        helpDialogVisible = true;

        // Add click handler to close on overlay click
        const overlay = helpDialog.querySelector('.keyboard-help-overlay');
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                hideHelpDialog();
            }
        });
    }

    /**
     * Hide the keyboard shortcuts help dialog
     */
    function hideHelpDialog() {
        const existingDialog = document.getElementById('keyboard-shortcuts-help');
        if (existingDialog) {
            existingDialog.remove();
            helpDialogVisible = false;
        }
    }

    /**
     * Check if an element should ignore keyboard shortcuts
     * @param {Element} element - The element to check
     * @returns {boolean} True if shortcuts should be ignored
     */
    function shouldIgnoreShortcut(element) {
        const tagName = element.tagName.toLowerCase();
        const isEditable = element.isContentEditable;
        const isInput = tagName === 'input' || tagName === 'textarea' || tagName === 'select';

        return isInput || isEditable;
    }

    /**
     * Main keyboard event handler
     *
     * Browser Conflict Prevention Strategy:
     * - Ctrl+1-5: ALWAYS preventDefault() - conflicts with browser tab switching
     * - Ctrl+K: ALWAYS preventDefault() - conflicts with browser search bar
     * - Ctrl+/: ALWAYS preventDefault() - may conflict in some browsers
     * - Ctrl+Enter: ALWAYS preventDefault() - ensure clean form submission override
     * - Standalone / or ?: Only preventDefault() when not typing in input fields
     * - Esc: Only preventDefault() when we handle it (close dialog, blur input)
     *
     * @param {KeyboardEvent} event - The keyboard event
     */
    function handleKeyboardEvent(event) {
        const { code, key, ctrlKey, metaKey, shiftKey, altKey } = event;
        const modifierKey = ctrlKey || metaKey;  // Support both Ctrl (Windows/Linux) and Cmd (Mac)
        const activeElement = document.activeElement;

        // Handle Escape key (always active)
        if (code === SHORTCUTS.ESCAPE) {
            if (helpDialogVisible) {
                hideHelpDialog();
                event.preventDefault();
                return;
            }
            // Blur active element if it's an input
            if (shouldIgnoreShortcut(activeElement)) {
                activeElement.blur();
                event.preventDefault();
                return;
            }
        }

        // Handle help dialog toggle (? or Ctrl+/)
        if ((shiftKey && code === 'Slash' && !modifierKey) ||
            (modifierKey && code === 'Slash')) {
            toggleHelpDialog();
            event.preventDefault();
            return;
        }

        // Handle Ctrl+Enter for ingestion
        // Always preventDefault to avoid any browser default behavior
        if (modifierKey && code === SHORTCUTS.INGESTION_TRIGGER && !shiftKey && !altKey) {
            event.preventDefault();
            triggerIngestion();
            return;
        }

        // For most shortcuts, ignore if user is typing in an input field
        // Exception: / and Ctrl+K can work from anywhere
        const isSearchShortcut = (code === 'Slash' && !shiftKey && !modifierKey) ||
                                 (modifierKey && code === 'KeyK');

        if (!isSearchShortcut && shouldIgnoreShortcut(activeElement)) {
            return;
        }

        // Handle search focus (Ctrl+K or /)
        if (isSearchShortcut) {
            // Always preventDefault for Ctrl+K to avoid browser search bar
            // Only preventDefault for / if not typing in an input field
            if (modifierKey && code === 'KeyK') {
                event.preventDefault();
                focusSearchInput();
            } else if (code === 'Slash' && !shouldIgnoreShortcut(activeElement)) {
                // Only prevent default for standalone / when not in input fields
                event.preventDefault();
                focusSearchInput();
            }
            return;
        }

        // Handle tab navigation (Ctrl+1 through Ctrl+5)
        // Always preventDefault to avoid browser tab switching
        if (modifierKey && !shiftKey && !altKey && code in SHORTCUTS.TAB_NAVIGATION) {
            event.preventDefault();
            const tabIndex = SHORTCUTS.TAB_NAVIGATION[code];
            switchToTab(tabIndex);
            return;
        }
    }

    /**
     * Initialize keyboard shortcuts
     */
    function initialize() {
        // Add keyboard event listener
        document.addEventListener('keydown', handleKeyboardEvent, true);

        // Add inline styles for help dialog (since external CSS might not be loaded yet)
        const style = document.createElement('style');
        style.textContent = `
            .keyboard-help-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                backdrop-filter: blur(4px);
            }

            .keyboard-help-dialog {
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                animation: slideIn 0.2s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .keyboard-help-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem;
                border-bottom: 2px solid #f0f0f0;
            }

            .keyboard-help-header h2 {
                margin: 0;
                font-size: 1.5rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .keyboard-help-close {
                background: none;
                border: none;
                font-size: 2rem;
                cursor: pointer;
                color: #999;
                line-height: 1;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: all 0.2s;
            }

            .keyboard-help-close:hover {
                background: #f0f0f0;
                color: #333;
            }

            .keyboard-help-content {
                padding: 1.5rem;
            }

            .keyboard-help-section {
                margin-bottom: 1.5rem;
            }

            .keyboard-help-section:last-child {
                margin-bottom: 0;
            }

            .keyboard-help-section h3 {
                margin: 0 0 0.75rem 0;
                font-size: 1rem;
                color: #667eea;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .keyboard-shortcut-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid #f5f5f5;
            }

            .keyboard-shortcut-item:last-child {
                border-bottom: none;
            }

            .keyboard-shortcut-item kbd {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-family: monospace;
                font-size: 0.85rem;
                font-weight: 600;
                margin: 0 0.25rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }

            .keyboard-shortcut-item span {
                color: #666;
                font-size: 0.95rem;
            }

            /* Dark mode support */
            @media (prefers-color-scheme: dark) {
                .keyboard-help-dialog {
                    background: #1e1e1e;
                    color: #e0e0e0;
                }

                .keyboard-help-header {
                    border-bottom-color: #333;
                }

                .keyboard-help-close {
                    color: #999;
                }

                .keyboard-help-close:hover {
                    background: #333;
                    color: #fff;
                }

                .keyboard-shortcut-item {
                    border-bottom-color: #333;
                }

                .keyboard-shortcut-item span {
                    color: #aaa;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // Add small visual indicator that shortcuts are active
    console.info('⌨️ Alexandria keyboard shortcuts loaded. Press ? for help.');
})();
