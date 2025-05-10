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

	form.addEventListener("htmx:beforeRequest", function (evt) {
		loadingIndicator.style.display = "inline-block";
		errorDiv.style.display = "none";
		resultsDiv.innerHTML = "Analysing your compatibility...";
	});

	form.addEventListener("htmx:afterRequest", function (evt) {
		loadingIndicator.style.display = "none";
		if (evt.detail.failed) {
			errorDiv.textContent = "An error occurred. Please try again.";
			errorDiv.style.display = "block";
			resultsDiv.innerHTML =
				"<p>An error occurred. Please check your input and try again.</p>";
		}
	});

	form.addEventListener("htmx:responseError", function (evt) {
		errorDiv.textContent = "Server connection error. Please try again.";
		errorDiv.style.display = "block";
		resultsDiv.innerHTML = "<p>Server connection error. Please try again.</p>";
	});

	form.addEventListener("htmx:response", function (evt) {
		const response = JSON.parse(evt.detail.xhr.responseText);

		if (evt.detail.xhr.status === 400) {
			errorDiv.textContent = response.error;
			errorDiv.style.display = "block";
			resultsDiv.innerHTML = `<p>${response.error}</p>`;
		} else if (evt.detail.xhr.status === 200) {
			try {
				resultsDiv.innerHTML = `
                    <h2 class="title is-4 has-text-centered">${
											response.compatibility_message
										}</h2>
                    <p class="has-text-centered">Similarity Score: ${response.similarity_score.toFixed(
											2
										)}%</p>
                `;
			} catch (error) {
				console.error("Error parsing JSON:", error);
				errorDiv.textContent = "Error: Invalid response from server.";
				errorDiv.style.display = "block";
				resultsDiv.innerHTML = "<p>Error: Invalid response from server.</p>";
			}
		}
	});
});
