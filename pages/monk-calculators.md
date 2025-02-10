---
layout: default
title: Monk Calculators
permalink: /monk-calculators/
---

function calculateOrdinationDate() {
    // Get user inputs
    let birthDateInput = document.getElementById("birthdate").value;
    let wombDaysInput = document.getElementById("wombDays").value;
    
    // Convert birthdate to Date object
    let birthDate = new Date(birthDateInput);
    
    // Ensure valid input
    if (isNaN(birthDate.getTime())) {
        alert("Please enter a valid birth date.");
        return;
    }
    
    // Determine days in the womb (default 180 if empty or invalid)
    let wombDays = parseInt(wombDaysInput);
    if (isNaN(wombDays) || wombDays < 0) {
        wombDays = 180;
    }
    
    // Total days to ordain (7200 from conception)
    let totalDays = 7200;
    
    // Calculate conception date
    let conceptionDate = new Date(birthDate);
    conceptionDate.setDate(conceptionDate.getDate() - wombDays);
    
    // Calculate ordination date
    let ordinationDate = new Date(conceptionDate);
    ordinationDate.setDate(ordinationDate.getDate() + totalDays);
    
    // Format result
    let result = `You can ordain on: ${ordinationDate.toDateString()}`;
    document.getElementById("result").innerText = result;
}

// HTML Structure (for reference)
/*
<input type="date" id="birthdate">
<input type="number" id="wombDays" placeholder="Days in womb (default 180)">
<button onclick="calculateOrdinationDate()">Calculate</button>
<p id="result"></p>
*/
