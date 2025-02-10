    document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('calculatorForm');
            const daysOption = document.getElementById('daysOption');
            const dateOption = document.getElementById('dateOption');
            const daysInput = document.getElementById('daysInput');
            const dateInput = document.getElementById('dateInput');
            const resultDiv = document.getElementById('result');

            // Toggle input sections based on radio selection
            daysOption.addEventListener('change', function() {
                daysInput.style.display = 'block';
                dateInput.style.display = 'none';
            });

            dateOption.addEventListener('change', function() {
                daysInput.style.display = 'none';
                dateInput.style.display = 'block';
            });

            form.addEventListener('submit', function(e) {
                e.preventDefault();

                const birthDate = new Date(document.getElementById('birthDate').value);
                let daysInWomb = 0;

                if (daysOption.checked) {
                    daysInWomb = parseInt(document.getElementById('daysInWomb').value) || 0;
                } else {
                    const conceptionDate = new Date(document.getElementById('conceptionDate').value);
                    daysInWomb = Math.floor((birthDate - conceptionDate) / (1000 * 60 * 60 * 24));
                }

                // Calculate ordination date: birth date + (7200 - days in womb)
                const daysToAdd = 7200 - daysInWomb;
                const ordinationDate = new Date(birthDate);
                ordinationDate.setDate(ordinationDate.getDate() + daysToAdd);

                // Format the date for display
                const formattedDate = ordinationDate.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });

                resultDiv.innerHTML = `<strong>Ordination Date:</strong> ${formattedDate}`;
                resultDiv.style.display = 'block';
                resultDiv.className = 'success';
            });
        });
