---
layout: page
title: "Buddhism Intro Course"
permalink: /course/
---

## Welcome to the Path
This course is designed in three levels to guide you through the essentials of Buddhist thought.

### Level 1: The Essentials
<ul>
  {% assign sorted_lessons = site.level_1 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>

### Level 2: Coming Soon
<ul>
  {% assign sorted_lessons = site.level_2 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>
### Level 3: Coming Soon
<ul>
  {% assign sorted_lessons = site.level_3 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>
