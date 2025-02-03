---
layout: page
title: About
permalink: /about
---
To-the-point Bio:

2003-2015: flamenco dancer ([what?](add website))

2015-2022: meditation (MM) ([here](https://www.paaukforestmonastery.org/) 

2016-present: Theravāda Buddhist monk
<div id="timer"></div>

<script>
  // Set the date you want to count from
  var countDownDate = new Date("YYYY-MM-DD").getTime(); // Replace YYYY-MM-DD with your specific date

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

  }, 1000);
</script>

2022-present: student at [Intl. Inst. of Theravāda](https://www.theravado.com/) (SL)
