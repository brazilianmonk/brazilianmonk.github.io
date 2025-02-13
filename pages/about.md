---
layout: page
title: About
permalink: /about
---

## To-the-point Bio:

**2003-2015**: flamenco dancer (Spain, Brazil, others) ([what?](https://www.google.com/search?q=Stefano+Domit+Flamenco))

**2015-2022**: meditation (Myanmar) ([here](https://www.paaukforestmonastery.org/))

**2016-present**: Theravāda Buddhist monk for <span id="timer"></span>

<script>
  // Set the date you want to count from
  var countDownDate = new Date("2016-10-07").getTime(); // Ordination date

  // Update the timer every second
  setInterval(function() {
    var now = new Date().getTime();
    var elapsed = now - countDownDate;

    // Calculate years, months, and days
    var years = Math.floor(elapsed / (1000 * 60 * 60 * 24 * 365.25));
    var months = Math.floor((elapsed % (1000 * 60 * 60 * 24 * 365.25)) / (1000 * 60 * 60 * 24 * 30.4375));
    var days = Math.floor((elapsed % (1000 * 60 * 60 * 24 * 30.4375)) / (1000 * 60 * 60 * 24));

    // Display the result in the timer div
    document.getElementById("timer").innerHTML = years + "y " + months + "m " + days + "d ";
  }, 1000);
</script>

**2022-present**: student and English teacher at [Intl. Inst. of Theravāda](https://www.theravado.com/) (Sri Lanka)
