---
layout: page
title: "Buddhism Introduction Course"
permalink: /course/
---

## Online Course: Introduction to Buddhism 
This course is designed to offer a thorough introduction to Buddhism in three depth-levels. Each lesson is followed by a short quiz, which, when overcome, gives you the key for the next lesson. 

### Level 1: The Essentials
study plan, hours, certificate, suitable for what person, level of understanding offered
<ul>
  {% assign sorted_lessons = site.level_1 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>

### Level 2
<ul>
  {% assign sorted_lessons = site.level_2 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>

### Level 3
<ul>
  {% assign sorted_lessons = site.level_3 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>
