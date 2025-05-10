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

			// Display success results
			resultsDiv.innerHTML = `
				<h2 class="title is-4 has-text-centered">${data.compatibility_message}</h2>
				<p class="has-text-centered">Similarity Score: ${data.similarity_score.toFixed(
					2
				)}%</p>
			`;
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
