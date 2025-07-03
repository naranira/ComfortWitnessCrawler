// Main JavaScript file for Comfort Women News Aggregator

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if any
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Search form enhancements
    const searchForm = document.querySelector('form[action*="search"]');
    if (searchForm) {
        // Add search suggestions (could be enhanced in future)
        const searchInput = searchForm.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.addEventListener('focus', function() {
                this.select();
            });
        }
    }
    
    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        if (button.type === 'submit' || button.onclick) {
            button.addEventListener('click', function() {
                // Add loading state
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Loading...';
                this.disabled = true;
                
                // Remove loading state after form submission or timeout
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.disabled = false;
                }, 3000);
            });
        }
    });
});

// Function to refresh articles
async function refreshArticles() {
    const refreshBtn = document.getElementById('refreshBtn');
    const originalHtml = refreshBtn.innerHTML;
    
    try {
        // Show loading state
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        const response = await fetch('/refresh');
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // Reload page after 2 seconds to show new articles
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            showAlert(data.message, 'danger');
        }
    } catch (error) {
        console.error('Error refreshing articles:', error);
        showAlert('Failed to refresh articles. Please try again.', 'danger');
    } finally {
        // Restore button state
        refreshBtn.innerHTML = originalHtml;
        refreshBtn.disabled = false;
    }
}

// Function to show alerts
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alertMessage = document.getElementById('alertMessage');
    
    if (alertContainer && alertMessage) {
        // Update alert content
        alertMessage.className = `alert alert-${type} alert-dismissible fade show`;
        alertMessage.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--accent-color');
        alertMessage.style.color = getComputedStyle(document.documentElement).getPropertyValue('--text-color');
        alertMessage.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Show alert
        alertContainer.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const alert = new bootstrap.Alert(alertMessage);
            alert.close();
            alertContainer.style.display = 'none';
        }, 5000);
    }
}

// Function to copy text to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success');
        }).catch(() => {
            showAlert('Failed to copy to clipboard', 'warning');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('Copied to clipboard!', 'success');
        } catch (err) {
            showAlert('Failed to copy to clipboard', 'warning');
        }
        document.body.removeChild(textArea);
    }
}

// Function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

// Function to get statistics and update display
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update stats display if elements exist
        const totalArticlesEl = document.querySelector('[data-stat="total-articles"]');
        if (totalArticlesEl) {
            totalArticlesEl.textContent = stats.total_articles;
        }
        
        const lastUpdateEl = document.querySelector('[data-stat="last-update"]');
        if (lastUpdateEl && stats.last_update) {
            lastUpdateEl.textContent = formatDate(stats.last_update);
        }
        
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Search functionality enhancements
function highlightSearchTerms(text, searchTerm) {
    if (!searchTerm) return text;
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark class="search-highlight">$1</mark>');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput && searchInput === document.activeElement) {
            searchInput.value = '';
        }
    }
});

// Progressive Web App features (future enhancement)
if ('serviceWorker' in navigator) {
    // Service worker registration could be added here
    console.log('Service Worker support detected');
}

// Analytics and tracking (if needed)
function trackEvent(eventName, eventData) {
    // Placeholder for analytics tracking
    console.log('Event tracked:', eventName, eventData);
}

// Export functions for global use
window.refreshArticles = refreshArticles;
window.showAlert = showAlert;
window.copyToClipboard = copyToClipboard;
window.trackEvent = trackEvent;
