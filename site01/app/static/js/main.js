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
                    alert(t('messages.newsletter_success'));
                    newsletterForm.reset();
                } else {
                    alert(data.error || t('messages.newsletter_error'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert(t('messages.newsletter_error'));
            }
        });
    }
    
    // Initialize cart count from localStorage
    updateCartCount();
});

// Cart management
function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        const total = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
        cartCount.textContent = total;
    }
}

function addToCart(productId, productName, price) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        existingItem.quantity = (existingItem.quantity || 1) + 1;
    } else {
        cart.push({
            id: productId,
            name: productName,
            price: price,
            quantity: 1
        });
    }
    
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
    
    alert(t('messages.product_added'));
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
