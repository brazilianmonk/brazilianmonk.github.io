---
layout: page
title: About
permalink: /about
---
#To-the-point Bio:#

2003-2015: flamenco dancer ([what?](add website))

2015-2022: meditation (MM) ([here](https://www.paaukforestmonastery.org/) 

2016-present: Theravāda Buddhist monk
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

    // Convert elapsed time to days, hours, minutes, and seconds
    var days = Math.floor(elapsed / (1000 * 60 * 60 * 24));
    var hours = Math.floor((elapsed % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((elapsed % (1000 * 60)) / 1000);

    // Display the result in the timer div
    document.getElementById("timer").innerHTML = days + "d " + hours + "h " +
      minutes + "m " + seconds + "s ";

  }, 1000);
</script>

2022-present: student at [Intl. Inst. of Theravāda](https://www.theravado.com/) (SL)
