---
layout: lesson
title: "The Eightfold Path"
order: 2
level: 1
---

<!-- 1. The Password Gate -->
<div id="lesson-gate" style="background: #f4f4f4; padding: 25px; border-radius: 10px; text-align: center; border: 2px dashed #ccc;">
  <h3>Lesson Locked</h3>
  <p>To unlock this lesson, enter the code found at the end of Lesson 1:</p>
  <input type="text" id="lesson-pass" placeholder="Enter code..." style="padding: 10px;">
  <button onclick="unlockLesson()" style="padding: 10px 20px;">Unlock Lesson</button>
  <p id="err" style="color: red; display: none;">Incorrect code.</p>
</div>

<!-- 2. The Hidden Lesson Content -->
<div id="lesson-content" style="display: none;">

  ## Understanding the Path
  (This is where your actual lesson content goes...)
content of lesson 2 of level 1

  <hr>
  
  ### Lesson 2 Quiz
  <!-- Embed your Google Form for THIS lesson here -->
  <iframe src="YOUR_GOOGLE_FORM_LINK_FOR_LESSON_2" width="100%" height="500"></iframe>

</div>

<script>
function unlockLesson() {
  var pass = document.getElementById("lesson-pass").value.trim().toUpperCase();
  
  // THE KEY: Change it to the code from the PREVIOUS lesson's quiz
  if (pass === "CITTA") {
    document.getElementById("lesson-gate").style.display = "none";
    document.getElementById("lesson-content").style.display = "block";
    localStorage.setItem("unlocked_l1_s2", "true");
  } else {
    document.getElementById("err").style.display = "block";
  }
}

// Auto-unlock if they've done it before
if (localStorage.getItem("unlocked_l1_s2") === "true") {
  document.getElementById("lesson-gate").style.display = "none";
  document.getElementById("lesson-content").style.display = "block";
}
</script>
