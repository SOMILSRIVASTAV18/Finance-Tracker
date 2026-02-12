/**
 * Main.js - Main JavaScript functionality for Personal Finance Tracker
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Toggle recurring frequency field based on is_recurring checkbox
    const recurringCheckbox = document.getElementById('is_recurring');
    const recurringFrequencyGroup = document.getElementById('recurring_frequency_group');
    
    if (recurringCheckbox && recurringFrequencyGroup) {
        recurringCheckbox.addEventListener('change', function() {
            if (this.checked) {
                recurringFrequencyGroup.style.display = 'block';
            } else {
                recurringFrequencyGroup.style.display = 'none';
            }
        });
        
        // Initial state
        if (!recurringCheckbox.checked) {
            recurringFrequencyGroup.style.display = 'none';
        }
    }
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
                        if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Delete confirmation
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });
    
    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value.replace(/[^\d.-]/g, ''));
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });
    
    // Date range picker initialization
    const dateRangePicker = document.getElementById('date-range');
    if (dateRangePicker) {
        new DateRangePicker(dateRangePicker, {
            format: 'yyyy-mm-dd'
        });
    }
    
    // Category color picker
    const colorPickers = document.querySelectorAll('.color-picker');
    colorPickers.forEach(picker => {
        picker.addEventListener('input', function() {
            const colorPreview = this.parentElement.querySelector('.color-preview');
            if (colorPreview) {
                colorPreview.style.backgroundColor = this.value;
            }
        });
    });
    
    // Expense form category color display
    const categorySelect = document.getElementById('category');
    const categoryColorIndicator = document.getElementById('category-color-indicator');
    
    if (categorySelect && categoryColorIndicator) {
        categorySelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const color = selectedOption.getAttribute('data-color') || '#cccccc';
            categoryColorIndicator.style.backgroundColor = color;
        });
        
        // Set initial color
        if (categorySelect.selectedIndex >= 0) {
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            const color = selectedOption.getAttribute('data-color') || '#cccccc';
            categoryColorIndicator.style.backgroundColor = color;
        }
    }
    
    // Handle mobile navigation
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('show');
        });
    }
    
    // Animate elements when they come into view
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        
        elements.forEach(element => {
            const position = element.getBoundingClientRect();
            
            // Check if element is in viewport
            if (position.top < window.innerHeight && position.bottom >= 0) {
                element.classList.add('animated');
            }
        });
    };
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run once on page load
});

