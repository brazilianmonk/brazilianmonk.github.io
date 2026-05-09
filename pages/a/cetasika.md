---
layout: page
permalink: /summaries/abhidhamma/cetasika
---

## Cetasikas
### Definition
*Cetasibhavaṃ cetasikaṃ* — they are called cetasikas since they exist in consciousness.

Renderings: mental factors, mentalities, immaterial dhammas, mental elements.

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### 4 Main Activities Done by Cetasikas
- Bodily acts
- Verbal acts
- Mental acts
- Cognizing objects

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### Sampayogalakkhaṇas of Cetasikas
- **Ekuppāda**: they arise together with the associated citta
- **Ekanirodha**: they vanish together with citta
- **Ekālambana**: they take the same object as the associated citta
- **Ekavatthuka**: they depend on the same material base as the associated citta

> *Ekuppāda nirodhā ca / ekālambaṇavatthukā / cetoyuttā dvipaññāsa / dhammā cetasikā matā*

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### How Many Cetasikas in Total?
52

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### What is Cittuppāda?
One citta together with its concomitant cetasikas are collectively called cittuppāda or nāmakalāpa.

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### Nāma — Definition
*Namatīti nāmaṃ* — they are called nāma since they bend towards an object.

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### Minimum / Maximum Cetasikas in One Cittuppāda
- Min: 7
- Max: 36

<hr style="width: 40%; margin: 1rem auto; border: 1px solid #AD6100;">

### Minimum Number of Nāmas / Rūpas Occurring Together
- 8 nāmas
- 8 rūpas

---


---
<script>
document.addEventListener("DOMContentLoaded", function() {
  // Add styles for collapsible TOC
  const style = document.createElement("style");
  style.textContent = `
    .table-of-contents {
      background: #f5f5f0;
      padding: 1rem 1.5rem;
      border-radius: 8px;
      margin-bottom: 2rem;
      border-left: 4px solid #8B4513;
    }
    .table-of-contents h2 {
      margin-top: 0;
      font-size: 1.3rem;
    }
    .table-of-contents ul {
      margin-bottom: 0;
      padding-left: 1.2rem;
    }
    .table-of-contents li {
      margin: 0.3rem 0;
      list-style-type: none;
    }
    .table-of-contents a {
      text-decoration: none;
      color: #2c5e2e;
    }
    .table-of-contents a:hover {
      text-decoration: underline;
    }
    /* Collapsible section styles */
    .toc-h2-item {
      margin-top: 0.5rem;
    }
    .toc-h2-link {
      cursor: pointer;
      display: inline-block;
    }
    .toc-toggle {
      cursor: pointer;
      display: inline-block;
      width: 20px;
      font-size: 0.9rem;
      font-weight: bold;
      color: #8B4513;
      user-select: none;
      margin-right: 6px;
      text-align: center;
    }
    .toc-toggle:hover {
      color: #2c5e2e;
    }
    .toc-h3-list {
      margin-left: 26px;
      padding-left: 0;
      transition: all 0.2s ease;
    }
    .toc-h3-list.collapsed {
      display: none;
    }
  `;
  document.head.appendChild(style);
  
  // Generate TOC
  const headings = document.querySelectorAll("h2, h3");
  if (headings.length === 0) return;
  
  const toc = document.createElement("div");
  toc.className = "table-of-contents";
  toc.innerHTML = "<h2>📖</h2><ul></ul>";
  const tocList = toc.querySelector("ul");
  
  let currentH2Item = null;
  let currentH3List = null;
  
  headings.forEach(heading => {
    if (heading.closest(".table-of-contents")) return;
    
    if (!heading.id) {
      heading.id = heading.textContent
        .toLowerCase()
        .replace(/[🇧🇷🇪🇸🇬🇧]/g, "")
        .replace(/[^\w\s-]/g, "")
        .replace(/\s+/g, "-");
    }
    
    if (heading.tagName === "H2") {
      // Create container for this H2 section
      const li = document.createElement("li");
      li.className = "toc-h2-item";
      
      // Add toggle arrow
      const toggle = document.createElement("span");
      toggle.className = "toc-toggle";
	toggle.textContent = "▶";  // Collapsed by default
      toggle.setAttribute("aria-label", "Collapse section");
      
      // Add the H2 link
      const a = document.createElement("a");
      a.href = `#${heading.id}`;
      a.textContent = heading.textContent;
      a.className = "toc-h2-link";
      
      // Container for H3 items (to be filled later)
      const h3Container = document.createElement("ul");
      h3Container.className = "toc-h3-list";
	h3Container.classList.add("collapsed");
      
	// Assemble
      li.appendChild(toggle);
      li.appendChild(a);
      li.appendChild(h3Container);
      tocList.appendChild(li);
      
      // Store references
      currentH2Item = li;
      currentH3List = h3Container;
      
      // Add click toggle functionality
      const toggleSection = () => {
        const isCollapsed = h3Container.classList.contains("collapsed");
        if (isCollapsed) {
          h3Container.classList.remove("collapsed");
          toggle.textContent = "▼";
          toggle.setAttribute("aria-label", "Collapse section");
        } else {
          h3Container.classList.add("collapsed");
          toggle.textContent = "▶";
          toggle.setAttribute("aria-label", "Expand section");
        }
      };
      
      toggle.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleSection();
      });
      
      a.addEventListener("click", function(e) {
        // Allow normal anchor behavior, but also toggle if desired?
        // Comment out the next line if you want clicking the link to ALSO toggle
        // e.preventDefault(); 
        // Uncomment below to toggle when clicking the link text too
        // toggleSection();
        // Then scroll to heading
        // document.getElementById(heading.id).scrollIntoView({ behavior: "smooth" });
      });
      
    } else if (heading.tagName === "H3" && currentH3List) {
      // Add H3 item under current H2
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#${heading.id}`;
      a.textContent = heading.textContent;
      li.appendChild(a);
      currentH3List.appendChild(li);
    }
  });
  
  // Insert TOC at the beginning of the page
  const firstHeading = document.querySelector("h1, h2");
  if (firstHeading) {
    firstHeading.parentNode.insertBefore(toc, firstHeading);
  } else {
    document.body.insertBefore(toc, document.body.firstChild);
  }
});
</script>
