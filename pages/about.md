---
layout: page
permalink: /about
---

## About the Author: Ariyañāṇa

![image](/assets/img/round-me-214.jpg)

**2003-2015**: flamenco dancer (Spain, Brazil, USA, PRC, South Korea, Netherlands, Canada, and others)

**2015-2022**: meditation (Myanmar) ([here](https://www.paaukforestmonastery.org/))

**2016-present**: Theravāda Buddhist monk for <span id="timer"></span> [(Calculate yours)](/monk-calculators)

<!-- ordination timer -->
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


<!-- Full Bio Link -->
<a href="#" id="bioLink" onclick="toggleBio(event)">📚Click here for Full Bio📚</a>

<!-- Full Bio Content -->
<div id="fullBio">
    <p>Bhante Ariyañāṇa, born Stefano Domit Cervo in Brazil, is a former <a href="https://en.wikipedia.org/wiki/Flamenco">flamenco</a> dancer who captivated global audiences with his performances until 2015, when he embarked on a transformative quest as a <a href="https://en.wikipedia.org/wiki/Theravada">Theravāda</a> Buddhist monk.</p>
    
  <h3>Artist Years</h3>
    <p>Inspired by his <a href="https://www.instagram.com/giseleclaudianedomit?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==">mother</a>, a flamenco dancer herself, he, at the age of 11, followed in her footsteps, initially playing percussion and then dancing, teaching, and choreographing. Later, at the age of 17, he moved to Spain, the homeland of Flamenco, where he achieved significant acclaim including first place at the <a href="https://youtu.be/UjTlp9rKxSQ?feature=shared">Festival Flamenco de Almería (2013)</a> and the <a href="https://www.eter.com/actualidad/noticia.php?id=17429">"Premio Extraordinario de Danza de la Comunidad de Madrid" (2015)</a>. As a choreographer and soloist, he participated in <a href="https://heartbeatofhome.com/">Heartbeat of Home</a>, a production of the creators of the global phenomenon Riverdance.</p>
    
  <p>In collaboration with top-notch flamenco artists, he performed in venues ranging from traditional tablaos such as <a href="https://tablaolascarboneras.com/">"Las Carboneras"</a> in Madrid to iconic concert halls such as Amsterdam's <a href="https://www.concertgebouw.nl/en/">Royal Concertgebouw</a> alongside <a href="https://en.wikipedia.org/wiki/Mar%C3%ADa_Juncal">Maria Juncal</a> and <a href="https://www.alfonsolosaonline.com">Alfonso Losa</a>. His short but dynamic career took him across the Americas, Europe, and Asia, with critics praising him as a dancer with "stately carriage" and "rapid-fire heelwork," combining "incredible rapidity and precision" in "passion filled, fiery flamenco numbers" that were "truly captivating" and "incredibly moving and powerful." In the words of the iconic dancer <a href="https://en.wikipedia.org/wiki/Antonio_Canales">Antonio Canales</a>: "He (Stefano) uses everything he has learned, thought, worked on, and felt to shatter it into a thousand pieces of emotion, making the viewer's heart skip a beat…"</p>
    
  <h3>Monkhood</h3>
    <p>In spite of the ever-growing artistic success, in 2015, seeking deeper meaning and inner peace, he embarked on a transformative inner journey. A retreat with <a href="https://www.dhammadipa.cz/en/">Thomas Dhammadīpa</a> in India introduced him to Theravāda teachings, leading him to the <a href="https://paaukforestmonastery.org">Pa Auk tradition</a> in Myanmar. There, he spent approximately seven years, first as a layperson, and then as a monastic as Ariyañāṇa, under the guidance of <a href="https://en.wikipedia.org/wiki/Bhaddanta_%C4%80ci%E1%B9%87a">Pa Auk Sayadaw</a>, his preceptor, and other teachers such as <a href="https://www.youtube.com/@DT-UKMRBVS">V. Kumārābhivaṁsa</a>.</p>
    
  <p>Continuing his spiritual path, in 2022, Bhante Ariyañāṇa joined the <a href="https://theravado.com">Nissayamuttaka course</a> at the <a href="https://theravado.com">International Institute of Theravāda</a> in Sri Lanka where he now deepens his traditional Theravāda Buddhist studies and leads the English Language studies for monastics.</p>
  <!-- PDF Download Links -->
    <p><b>Download the Bio</b> (includes longer and shorter versions):</p>
        <p><a href="/assets/docs/brazilianmonk_bio_english.pdf" download>in English ⏬</a> |
        <a href="/assets/docs/brazilianmonk_bio_espanol.pdf" download>en Español (soon) ⏬</a> |
        <a href="/assets/docs/brazilianmonk_bio_portugues.pdf" download>em Português (soon) ⏬</a>
    </p>
</div>

<style>
    #fullBio {
        display: none; /* Hides full bio initially */
    }
</style>

<script>
    function toggleBio(event) {
        event.preventDefault(); // Prevents the default link behavior (scrolling to top)
        var bio = document.getElementById("fullBio");
        var link = document.getElementById("bioLink");
        if (bio.style.display === "none" || bio.style.display === "") {
            bio.style.display = "block";
            link.textContent = "📚Click here to hide Full Bio📚";
        } else {
            bio.style.display = "none";
            link.textContent = "📚Click here for Full Bio📚";
        }
    }
</script>
---

## About the Site

I began this website as an **experiment**. I'm not sure how useful it will be, but I think that, among other things, it might help me:
- keep track of and further my Dhamma projects and that of others
- spread the Buddha Dhamma
- have a bigger positive impact and help more people

Let's see!