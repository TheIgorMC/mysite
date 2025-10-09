// Main JavaScript for Orion Project

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Newsletter form
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('newsletter-email').value;
            
            try {
                const response = await fetch('/api/newsletter/subscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email: email })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showNotification(t('messages.newsletter_success'), 'success');
                    newsletterForm.reset();
                } else {
                    showNotification(data.error || t('messages.newsletter_error'), 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification(t('messages.newsletter_error'), 'error');
            }
        });
    }
    
    // Initialize cart count from localStorage
    updateCartCount();
    
    // Update cart count when page becomes visible (e.g., returning from another tab)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            updateCartCount();
        }
    });
    
    // Listen for storage changes (when cart is updated in another tab/window)
    window.addEventListener('storage', function(e) {
        if (e.key === 'shopping_cart') {
            updateCartCount();
        }
    });
});

// Cart management
function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('shopping_cart') || '[]');
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        const total = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
        cartCount.textContent = total;
    }
}

function addToCart(productId, productName, price, imageUrl = '', description = '') {
    let cart = JSON.parse(localStorage.getItem('shopping_cart') || '[]');
    
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        existingItem.quantity = (existingItem.quantity || 1) + 1;
    } else {
        cart.push({
            id: productId,
            name: productName,
            price: price,
            quantity: 1,
            image: imageUrl,
            description: description
        });
    }
    
    localStorage.setItem('shopping_cart', JSON.stringify(cart));
    updateCartCount();
    
    // Show notification instead of alert
    showNotification(t('messages.product_added'), 'success');
}

// Helper function to add to cart from button with data attributes
function addToCartFromButton(button) {
    const id = parseInt(button.dataset.productId);
    const name = button.dataset.productName;
    const price = parseFloat(button.dataset.productPrice);
    const image = button.dataset.productImage;
    const description = button.dataset.productDesc || '';
    
    addToCart(id, name, price, image, description);
}

// Toast Notification System
function showNotification(message, type = 'success', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.style.pointerEvents = 'auto';
    
    // Set color scheme based on type
    let bgColor, borderColor, iconClass;
    switch(type) {
        case 'success':
            bgColor = 'bg-green-500 dark:bg-green-600';
            borderColor = 'border-green-600 dark:border-green-700';
            iconClass = 'fa-check-circle';
            break;
        case 'error':
            bgColor = 'bg-red-500 dark:bg-red-600';
            borderColor = 'border-red-600 dark:border-red-700';
            iconClass = 'fa-exclamation-circle';
            break;
        case 'warning':
            bgColor = 'bg-yellow-500 dark:bg-yellow-600';
            borderColor = 'border-yellow-600 dark:border-yellow-700';
            iconClass = 'fa-exclamation-triangle';
            break;
        case 'info':
            bgColor = 'bg-blue-500 dark:bg-blue-600';
            borderColor = 'border-blue-600 dark:border-blue-700';
            iconClass = 'fa-info-circle';
            break;
        default:
            bgColor = 'bg-gray-700 dark:bg-gray-800';
            borderColor = 'border-gray-800 dark:border-gray-900';
            iconClass = 'fa-bell';
    }
    
    notification.className = `${bgColor} text-white px-6 py-4 rounded-lg shadow-lg border-l-4 ${borderColor} flex items-center gap-3 min-w-[300px] max-w-md transform transition-all duration-300 ease-out opacity-0 translate-x-full`;
    
    notification.innerHTML = `
        <i class="fas ${iconClass} text-xl"></i>
        <span class="flex-1 font-medium">${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-2 hover:bg-white/20 rounded p-1 transition-colors">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.remove('opacity-0', 'translate-x-full');
    }, 10);
    
    // Auto remove after duration
    setTimeout(() => {
        notification.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Utility functions
function showLoading(element, message) {
    // Use default message if not provided
    const loadingMessage = message || t('common.loading');
    
    if (element) {
        const isDarkMode = document.documentElement.classList.contains('dark');
        const textColor = isDarkMode ? 'text-gray-300' : 'text-gray-700';
        const spinnerColor = isDarkMode ? 'text-primary' : 'text-primary';
        
        element.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12">
                <div class="relative">
                    <div class="w-16 h-16 border-4 border-gray-200 dark:border-gray-700 border-t-primary rounded-full animate-spin"></div>
                </div>
                <p class="mt-4 text-sm font-medium ${textColor}">${loadingMessage}</p>
            </div>
        `;
    }
}

function hideLoading(element) {
    // This function is called when content is ready to be displayed
    // The calling code should immediately replace the content
}

function showError(element, message) {
    if (element) {
        element.innerHTML = `
            <div class="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg">
                <div class="flex items-center">
                    <i class="fas fa-exclamation-triangle mr-3"></i>
                    <span>${message}</span>
                </div>
            </div>
        `;
    }
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

// Format currency
function formatCurrency(amount, currency = 'EUR') {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: currency
    }).format(amount);
}
