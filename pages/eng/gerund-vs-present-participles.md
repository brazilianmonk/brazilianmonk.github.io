---
layout: page
permalink: /summaries/eng/gerund-vs-present-participle
---

## Gerund vs Present Participle


### Gerunds

They **primarily** function as nouns, but they often carry traces of their verbal origin, which lets them behave in ways that blur the line between noun and verb.


#### 🧠 Core Role: Gerunds as Nouns

Gerunds are verb forms ending in **-ing** that act as nouns. For example:

-   **Meditating** calms the mind.
-   **Reading** canonical texts is part of my daily practice.

In these cases, the gerund is the subject of the sentence—clearly a noun role.


#### 🧩 But They Retain Verbal Properties Too

Even though gerunds are nouns, they can:

-   **Take objects**:  
    -   **Translating Pāli texts** requires precision.  
        → “Translating” is a gerund, but it still “acts on” the object “Pāli texts.”
-   **Be modified by adverbs**:  
    -   **Carefully preparing the metadata** improves export quality.  
        → “Carefully” modifies “preparing,” just like it would a verb.
-   **Have passive or perfect forms**:  
    -   **Having studied the Vinaya**, he felt more confident.  
        → “Having studied” is a perfect gerund phrase.


#### 🧘♂️ Think of Gerunds as Hybrid Forms

They’re nouns with verbal DNA. That’s why they can:

-   Be the subject or object of a sentence (noun role)
-   Still govern objects and be modified by adverbs (verb traits)

So while gerunds **function** as nouns grammatically, they don’t shed all their verbal behavior. They’re like monks who’ve renounced worldly life but still remember how the world works.

Would you like to explore how gerunds differ from participles next? Or maybe dive into how they behave in Pāli or Portuguese?


### Present Participles

On the other hand, present participles act as verbs in various tenses, as adjectives, or, can be used in present participle clause - as explained in this page above. For example:

I am walking. [ Present continous tense]

My friend is a walking disaster. [As an adjective]

What is the name of the celebrity walking on the red carpet? [Reduced relative clause of "What is the 
name of the celebrity *who is walking on the red carpet*?"]

Walking down the street, I saw a white dog. [Used in present participle clause]


### Perfect Gerund vs. Perfect Participle


#### 🧠 Form:

Both use: having + past participle (e.g., having eaten, having finished, having studied)


#### 🧩 Function & Role

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">Feature</th>
<th scope="col" class="org-left">Perfect Gerund</th>
<th scope="col" class="org-left">Perfect Participle</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-left"><b><b>Part of Speech</b></b></td>
<td class="org-left">Noun</td>
<td class="org-left">Adjective or verb modifier</td>
</tr>

<tr>
<td class="org-left"><b><b>Function</b></b></td>
<td class="org-left">Refers to a completed action as a noun</td>
<td class="org-left">Describes a completed action related to another verb</td>
</tr>

<tr>
<td class="org-left"><b><b>Example</b></b></td>
<td class="org-left"><b>He regrets <b>*having lied</b></b> to her.*</td>
<td class="org-left"><b><b>Having lied</b></b>, he felt ashamed.</td>
</tr>

<tr>
<td class="org-left"><b><b>Position</b></b></td>
<td class="org-left">Acts as subject, object, or complement</td>
<td class="org-left">Often introduces a clause or modifies a noun</td>
</tr>

<tr>
<td class="org-left"><b><b>Focus</b></b></td>
<td class="org-left">The action itself as a concept</td>
<td class="org-left">The actor and their state after the action</td>
</tr>
</tbody>
</table>


#### 🧘 Why It Matters in Usage

-   **Perfect Gerund** emphasizes the **fact** that something was done, and treats it as a thing or concept.
    -   “She denied **having stolen** the book.” → The denial is about the act itself.

-   **Perfect Participle** sets up **context** for another action.
    -   “\*Having stolen\* the book, she ran away.” → The stealing happened before the running.

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
