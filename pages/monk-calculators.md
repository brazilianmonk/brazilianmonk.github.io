---
layout: default
title: Monk Calculators
permalink: /monk-calculators/
---
<div class="container">
    <h1>Upasampadā Date Calculator</h1>
    <form id="calculatorForm">
        <div class="form-group">
            <label for="birthDate">Date of Birth:</label>
            <input type="date" id="birthDate" required>
        </div>

        <div class="form-group">
            <label>Gestation Period:</label>
            <div class="radio-group">
                <input type="radio" id="daysOption" name="gestationType" value="days" checked>
                <label for="daysOption">Enter days in mother's womb</label>
            </div>
            <div id="daysInput" class="input-section" style="display: block;">
                <input type="number" id="daysInWomb" placeholder="Enter number of days (default 180 days)" value="180" min="0" max="360">
            </div>

            <div class="radio-group">
                <input type="radio" id="dateOption" name="gestationType" value="date">
                <label for="dateOption">Enter date of conception</label>
            </div>
            <div id="dateInput" class="input-section">
                <input type="date" id="conceptionDate">
            </div>
        </div>

        <button type="submit">Calculate Ordination Date</button>
    </form>

    <div id="result"></div>
</div>
<script src="/assets/js/calculator.js"></script>
