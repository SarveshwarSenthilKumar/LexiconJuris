document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('noteSearch');
    const noResults = document.getElementById('noResults');
    let searchTimeout;
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(filterNotes, 300);
        });
        
        // Add keyboard shortcut to focus search (Cmd+K / Ctrl+K)
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            } else if (e.key === 'Escape' && document.activeElement === searchInput) {
                searchInput.blur();
            }
        });
    }
    
    function filterNotes() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        const noteCards = document.querySelectorAll('.note-card');
        let hasVisibleNotes = false;
        let hasVisibleUnits = false;
        
        if (!searchTerm) {
            // Show all notes if search is empty
            noteCards.forEach(card => card.style.display = '');
            document.querySelectorAll('.unit-section').forEach(section => {
                section.style.display = '';
                updateUnitVisibility(section);
            });
            
            // Always hide no notes message
            noResults.classList.add('hidden');
            return;
        }
        
        // Filter notes - search through all fields
        noteCards.forEach(card => {
            const title = card.getAttribute('data-title') || '';
            const content = card.getAttribute('data-content') || '';
            const unit = card.getAttribute('data-unit') || '';
            const tags = card.getAttribute('data-tags') || '';
            const date = card.getAttribute('data-date') || '';
            const favorite = card.getAttribute('data-favorite') || '';
            
            // Search through all fields
            if (title.includes(searchTerm) || 
                content.includes(searchTerm) || 
                unit.includes(searchTerm) ||
                tags.includes(searchTerm) ||
                date.includes(searchTerm) ||
                favorite.includes(searchTerm)) {
                card.style.display = '';
                hasVisibleNotes = true;
                
                // Highlight matching text
                const titleElement = card.querySelector('.title-text');
                const contentElement = card.querySelector('.content-preview');
                
                if (titleElement) {
                    titleElement.innerHTML = highlightText(titleElement.textContent, searchTerm);
                }
                if (contentElement) {
                    contentElement.innerHTML = highlightText(contentElement.textContent, searchTerm);
                }
            } else {
                card.style.display = 'none';
            }
        });
        
        // Update unit visibility
        document.querySelectorAll('.unit-section').forEach(section => {
            updateUnitVisibility(section);
            if (section.style.display !== 'none') {
                hasVisibleUnits = true;
            }
        });
        
        // Show appropriate messages
        if (noteCards.length > 0 && !hasVisibleNotes) {
            noResults.classList.remove('hidden');
        } else {
            noResults.classList.add('hidden');
        }
    }
    
    function updateUnitVisibility(section) {
        const unitId = section.getAttribute('data-unit');
        const hasVisibleNotes = Array.from(document.querySelectorAll(`.note-card[data-unit="${unitId}"]`))
            .some(card => card.style.display !== 'none');
        
        section.style.display = hasVisibleNotes ? '' : 'none';
        
        // Update unit count
        const unitCount = section.querySelector('.unit-count');
        if (unitCount) {
            const visibleCount = section.querySelectorAll('.note-card:not([style*="display: none"])').length;
            unitCount.textContent = `(${visibleCount} note${visibleCount !== 1 ? 's' : ''})`;
        }
    }
    
    function highlightText(text, term) {
        if (!term) return text;
        
        const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    
    // Initialize unit visibility
    document.querySelectorAll('.unit-section').forEach(updateUnitVisibility);
});
