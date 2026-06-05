---
layout: page
title: "Buddhism Courses"
permalink: /courses/
---

## Online Course: Introduction to Buddhism 

If we had to summarize the Buddha's teaching it could be:
**Sabbapāpassa akaraṇaṁ**
**Kusalassa upasampadā**
**Sacittapariyodapanaṁ**
**Etaṁ buddhāna sāsanaṁ.**

The non-doing of all evil,
the arousal of wholesome,
the purification of one's mind,
this is the dispensation of the Buddhas.

But what evil and wholesome actually are and how to purify the mind requires more information, and explaining this, among other things, is the main point of Buddhism.

I designed this course to offer a thorough introduction to Buddhism in three depth-levels. Each level is intended to cover the entire doctrine but in ever greater detail, including a few meditation subjects. Each lesson is followed by a short quiz, which, when overcome, gives you the key for the next lesson. It doesn't require signing up or logging in, so in order to keep your progress, make sure not to delete your browser's cache or store the keys you get along the way.

### Level 1
Content:
Hours: 

<ul>
  {% assign sorted_lessons = site.level_1 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>

### Level 2
Study plan:
Hours: 

<ul>
  {% assign sorted_lessons = site.level_2 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>

### Level 3
Study plan:
Hours: 

<ul>
  {% assign sorted_lessons = site.level_3 | sort: 'order' %}
  {% for lesson in sorted_lessons %}
    <li>
      <a href="{{ lesson.url | relative_url }}">{{ lesson.title | default: "Untitled Lesson" }}</a>
    </li>
  {% endfor %}
</ul>
