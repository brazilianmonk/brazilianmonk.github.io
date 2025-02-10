---
layout: default
title: Monk Calculators
permalink: /monk-calculators/
---

<h1>Monk Ordination Calculator</h1>
<p>Enter your birth date and optionally adjust the days in the womb (default is 180 days).</p>

<label for="birthdate">Birth Date:</label>
<input type="date" id="birthdate">

<label for="wombDays">Days in Womb:</label>
<input type="number" id="wombDays" placeholder="Days in womb (default 180)">

<button onclick="calculateOrdinationDate()">Calculate</button>

<p id="result"></p>

<script src="/assets/js/ordination-date-calculator.js"></script>
