---
layout: lesson
title: lesson 4
order: 4
level: 1
---

<!-- 1. The Password Gate -->
<div id="lesson-gate" style="background: #f4f4f4; padding: 25px; border-radius: 10px; text-align: center; border: 2px dashed #ccc;">
  <h3>Lesson Locked</h3>
  <p>To unlock this lesson, enter the code found at the end of Lesson 3:</p>
  <input type="text" id="lesson-pass" placeholder="Enter code..." style="padding: 10px;">
  <button onclick="unlockLesson()" style="padding: 10px 20px;">Unlock Lesson</button>
  <p id="err" style="color: red; display: none;">Incorrect code.</p>
</div>

<!-- 2. The Hidden Lesson Content -->
<div id="lesson-content" style="display: none;">

  ## lesson 4
  (This is where your actual lesson content goes...)
content of lesson 4 of level 1

  <hr>
  
  ### Lesson 4 Quiz
  <!-- Embed your Google Form for THIS lesson here -->
  <iframe src="https://docs.google.com/forms/d/e/1FAIpQLSfUOYMAsBouTwNr3nX2zvS8n8KB68ogCHgB2nDXiu6Vhm2vtQ/viewform?embedded=true" width="100%" height="1702" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>

</div>

<script>
function unlockLesson() {
  var pass = document.getElementById("lesson-pass").value.trim().toUpperCase();
  
  // THE KEY: Change it to the code from the PREVIOUS lesson's quiz
  if (pass === "DUKKHA") {
    document.getElementById("lesson-gate").style.display = "none";
    document.getElementById("lesson-content").style.display = "block";
    localStorage.setItem("unlocked_lvl1_l4", "true");
  } else {
    document.getElementById("err").style.display = "block";
  }
}

// Auto-unlock if they've done it before
if (localStorage.getItem("unlocked_lvl1_l4") === "true") {
  document.getElementById("lesson-gate").style.display = "none";
  document.getElementById("lesson-content").style.display = "block";
}
</script>
