document.addEventListener('DOMContentLoaded', function () {
    var dropdowns = document.querySelectorAll('.dropdown-submenu');
    dropdowns.forEach(function (dropdown) {
        dropdown.addEventListener('mouseenter', function () {
            this.querySelector('.dropdown-menu').classList.add('show');
        });
        dropdown.addEventListener('mouseleave', function () {
            this.querySelector('.dropdown-menu').classList.remove('show');
        });
    });
});

const toggle = document.getElementById('toggleTranslation');
const translations = document.querySelectorAll('.gemini-trans');

function updateVisibility() {
    translations.forEach(p => {
        p.style.display = toggle.checked ? 'block' : 'none';
    });
}

toggle.addEventListener('change', updateVisibility);
updateVisibility();

function generateTOC() {
    const toc = document.getElementById('toc');
    if (!toc) {
        console.error("Error: No element with ID 'toc' found in the HTML.");
        return;
    }

    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    if (headings.length === 0) return;

    const tocTitle = document.createElement('h2');
    tocTitle.textContent = 'Table of Contents';
    tocTitle.className = 'toggle-btn';
    toc.appendChild(tocTitle);
    
    const tocContent = document.createElement('div');
    tocContent.className = 'toc-content';
    toc.appendChild(tocContent);

    const ul = document.createElement('ul');
    tocContent.appendChild(ul);

    let currentUl = ul;
    let stack = [ul];

    headings.forEach((heading, index) => {
        if (!heading.id) {
            heading.id = 'heading-' + index;
        }

        const level = parseInt(heading.tagName.charAt(1));
        const li = document.createElement('li');
        const a = document.createElement('a');
        li.className = `level-${level}`;
        
        a.href = '#' + heading.id;
        a.textContent = heading.textContent;
        li.appendChild(a);

        // Adjust nesting: Move up the stack if level decreases
        while (stack.length > level) {
            stack.pop();
            currentUl = stack[stack.length - 1];
        }

        // Adjust nesting: Move down the stack if level increases
        while (stack.length < level) {
            const newUl = document.createElement('ul');
            // If currentUl has a last child, append newUl to it; otherwise, we'll append li first
            if (currentUl.lastElementChild) {
                currentUl.lastElementChild.appendChild(newUl);
            }
            stack.push(newUl);
            currentUl = newUl;
        }

        // Append the current li to the appropriate ul
        //if (level <= 3) {
            li.classList.add('collapsible');
        //}
        currentUl.appendChild(li);
    });

    // Toggle main TOC
    tocTitle.addEventListener('click', function(e) {
        e.stopPropagation();
        const content = this.nextElementSibling;
        toggleCollapse(this, content);
    });

    // Toggle collapsible items
    document.querySelectorAll('.collapsible').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            const ul = this.querySelector('ul');
            if (ul) {
                toggleCollapse(this, ul);
            }
        });
    });

    // Close TOC when clicking outside
    document.addEventListener('click', function(e) {
        if (!toc.contains(e.target)) {
            tocContent.style.display = 'none';
            tocTitle.classList.remove('open');
            document.querySelectorAll('.collapsible').forEach(item => {
                item.classList.remove('open');
                const ul = item.querySelector('ul');
                if (ul) ul.classList.add('collapsed');
            });
        }
    });
}

function toggleCollapse(element, content) {
    const isOpen = element.classList.contains('open');
    if (isOpen) {
        content.style.display = 'none';
        content.classList.add('collapsed');
        element.classList.remove('open');
    } else {
        content.style.display = 'block';
        content.classList.remove('collapsed');
        element.classList.add('open');
    }
}

window.onload = generateTOC;