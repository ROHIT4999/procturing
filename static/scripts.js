document.addEventListener("DOMContentLoaded", () => {
    const setupCamera = (videoElement) => {
        navigator.mediaDevices
            .getUserMedia({ video: true })
            .then((stream) => {
                videoElement.srcObject = stream;
            })
            .catch((err) => console.error("Camera access denied:", err));
    };

    const capturePhoto = (videoElement, canvasElement, photoInputElement) => {
        const context = canvasElement.getContext("2d");
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        const photoData = canvasElement.toDataURL("image/png");
        if (photoInputElement) {
            photoInputElement.value = photoData;
        }
        return photoData;
    };

    // Signup Logic
    const signupForm = document.getElementById("signup-form");
    if (signupForm) {
        const video = document.getElementById("video");
        const canvas = document.getElementById("canvas");
        const photoInput = document.getElementById("photo");
        const captureButton = document.getElementById("capture");

        setupCamera(video);

        captureButton.addEventListener("click", () => {
            capturePhoto(video, canvas, photoInput);
        });

        signupForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(signupForm);
            fetch("/signup", {
                method: "POST",
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => alert(data.message || data.error))
                .catch((err) => console.error("Signup error:", err));
        });
    }

    // Login Logic
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        const video = document.getElementById("video");
        const canvas = document.getElementById("canvas-login");
        const photoInput = document.getElementById("photo-login");
        const captureButton = document.getElementById("capture-login");

        setupCamera(video);

        captureButton.addEventListener("click", () => {
            capturePhoto(video, canvas, photoInput);
        });

        loginForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            fetch("/login", {
                method: "POST",
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        alert(data.error || "Login failed!");
                        window.location.href = data.redirect_url;
                    }
                })
                .catch((err) => console.error("Login error:", err));
        });
    }

    // Post-Login Verification Logic
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas-verify");
    const photoInput = document.getElementById("photo-verify");
    const captureButton = document.getElementById("capture-verify");
    const verifyButton = document.getElementById("verify-btn");
    const resultDisplay = document.getElementById("verification-result");

    if (video) {
        setupCamera(video);

        captureButton.addEventListener("click", () => {
            capturePhoto(video, canvas, photoInput);
        });

        verifyButton.addEventListener("click", () => {
            const photoData = photoInput.value;
            if (!photoData) {
                alert("Please capture a photo first!");
                return;
            }

            fetch("/verify", {
                method: "POST",
                body: new URLSearchParams({ photo: photoData }),
            })
                .then((response) => response.json())
                .then((data) => {
                    resultDisplay.textContent = data.message;
                    if (data.success) {
                        resultDisplay.style.color = "green";
                        window.location.href = data.redirect_url;  // Redirect to live recognition page
                    } else {
                        resultDisplay.style.color = "red";
                    }
                })
                .catch((err) => console.error("Verification error:", err));
        });
    }

    

    // Logout Logic
    const logoutButton = document.getElementById("logout-btn");
    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            fetch("/logout", { method: "POST" })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        alert(data.message);
                        window.location.href = "/login"; // Redirect to login page
                    } else {
                        alert(data.error || "Logout failed!");
                    }
                })
                .catch((err) => console.error("Logout error:", err));
        });
    }
});
