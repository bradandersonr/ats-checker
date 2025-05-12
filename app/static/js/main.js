document.addEventListener("DOMContentLoaded", function () {
	const form = document.getElementById("resume-form");
	const loadingIndicator = document.getElementById("loading");
	const errorDiv = document.getElementById("error");
	const resultsDiv = document.getElementById("results");
	const fileInput = document.querySelector(".file-input");
	const fileLabel = document.querySelector(".file-name");

	// Update file name when file is selected
	fileInput.addEventListener("change", function () {
		if (fileInput.files.length > 0) {
			fileLabel.textContent = fileInput.files[0].name;
		} else {
			fileLabel.textContent = "No file selected";
		}
	});

	form.addEventListener("submit", async function (e) {
		e.preventDefault();

		// Show loading state
		loadingIndicator.style.display = "inline-block";
		errorDiv.style.display = "none";
		resultsDiv.innerHTML = "Analysing your compatibility...";

		try {
			const formData = new FormData(form);
			const response = await fetch("/", {
				method: "POST",
				body: formData,
			});

			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error || "An error occurred");
			}

			const compatibility_score = data.compatibility_score.toFixed(2);
			const compatibility_rating = data.compatibility_rating;
			const skills = data.skills;
			const experience = data.experience;

			let compatibility_explaination = 'This is likely due to very few keywords mentioned in the Job Ad being present in your resune. Update your resume with keywords found in the Job Ad to improve your score.';
			if (compatibility_score > 80) {
				compatibility_explaination = 'This is an excellent result. No further updates are likely required.';
			} else if (compatibility_score > 60) {
				compatibility_explaination = 'This is likely due to some keywords mentioned in the Job Ad being present in your resume, but others missing. Update your resume with more keywords found in the Job Ad to improve your score.';
			}

			let soft_colour = 'rgba(255, 82, 82, 0.25)'; // Default: Red
			let hard_colour = 'rgba(255, 82, 82, 1)'; // Default: Red
			if (compatibility_score > 80) {
				soft_colour = 'rgba(76, 175, 80, 0.25)'; // Green
				hard_colour = 'rgba(76, 175, 80, 1)';
			} else if (compatibility_score > 60) {
				soft_colour = 'rgba(255, 193, 7, 0.25)'; // Yellow
				hard_colour = 'rgba(255, 193, 7, 1)'; // Yellow
			}

			// Display success results
			resultsDiv.innerHTML = `
				<h2 class="title is-4 has-text-centered">Compatability Rating: <span style="color: ${hard_colour}">${compatibility_rating.toUpperCase()}</span></h2>
				<h3 class="">Suggestions</h3>
				<p>${compatibility_explaination}</p>
				<p>Your Skills: <pre>${skills}</pre></p>
				<p>Your Experience: <pre>${experience}</pre></p>
				<h2 class="has-text-centered">Score: ${compatibility_score}%</h2>
				
				<div>
					<canvas id="compatibility-chart"></canvas>
				</div>
			`;

			const ctx = document.getElementById('compatibility-chart');

			new Chart(ctx, {
				type: 'bar',
				data: {
				  labels: ['Compatibility %'],
				  datasets: [{
					label: '%',
					data: [compatibility_score],
					backgroundColor: [soft_colour],
					borderColor: [hard_colour],
					borderWidth: 1
				  }]
				},
				options: {
					indexAxis: 'y',
					plugins: {
						datalabels: {
							display: false,
						},
						legend: {
							display: false,
							position: 'bottom'
						},
						tooltip: {
							enabled: false
						}
					},
					responsive: true,
					maintainAspectRatio: false,
					scales: {
						x: {
							max: 100,
						},
						y: {
							beginAtZero: true,
							display: false,
						}
					},
				}
			  });
		} catch (error) {
			console.error("Error:", error);
			errorDiv.textContent =
				error.message || "An error occurred. Please try again.";
			errorDiv.style.display = "block";
			resultsDiv.innerHTML = `<p>${
				error.message || "An error occurred. Please try again."
			}</p>`;
		} finally {
			loadingIndicator.style.display = "none";
		}
	});
});
