---
layout: page
title: About
permalink: /about
---
## To-the-point Bio:

**2003-2015**: flamenco dancer ([what?](https://www.google.com/search?q=Stefano+Domit+Flamenco))

**2015-2022**: meditation (MM) ([here](https://www.paaukforestmonastery.org/))

**2016-present**: Theravāda Buddhist monk for
<div id="timer"></div>

<script>
  // Set the date you want to count from
  var countDownDate = new Date("2016-10-07").getTime(); // Replace YYYY-MM-DD with your specific date

  // Update the timer every second
  var x = setInterval(function() {
    // Get the current date and time
    var now = new Date().getTime();

    // Calculate the time elapsed since the specified date
    var elapsed = now - countDownDate;

    // Calculate years, months, and days
    var years = new Date(elapsed).getUTCFullYear() - 1970; // Adjust for epoch year
    var months = new Date(elapsed).getUTCMonth(); // Get month (0-11)
    var days = new Date(elapsed).getUTCDate() - 1; // Get day of the month (1-31)

    // Display the result in the timer div
    document.getElementById("timer").innerHTML =
      years + "y " + months + "m " + days + "d ";



    Testing ordination time calculator:

    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ordination Duration Counter</title>
</head>
<body>
    <h1>Ordination Duration Counter</h1>
    <label for="ordinationDate">Enter your ordination date (YYYY/MM/DD):</label>
    <input type="date" id="ordinationDate">
    <button onclick="calculateDuration()">Calculate Duration</button>
    
    <h2 id="result"></h2>

    <script>
        function calculateDuration() {
            const ordinationDate = new Date(document.getElementById("ordinationDate").value);
            const today = new Date();
            
            const years = today.getFullYear() - ordinationDate.getFullYear();
            const months = today.getMonth() - ordinationDate.getMonth();
            const days = today.getDate() - ordinationDate.getDate();

            let totalYears = years;
            let totalMonths = months;
            let totalDays = days;

            if (totalDays < 0) {
                totalMonths--;
                totalDays += new Date(today.getFullYear(), today.getMonth(), 0).getDate();
            }

            if (totalMonths < 0) {
                totalYears--;
                totalMonths += 12;
            }

            document.getElementById("result").innerText = 
                `You have been ordained for ${totalYears} years, ${totalMonths} months, and ${totalDays} days.`;
        }
    </script>
</body>
</html>

  }, 1000);
</script>

**2022-present**: student at [Intl. Inst. of Theravāda](https://www.theravado.com/) (SL)
