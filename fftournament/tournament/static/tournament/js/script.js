/**
 * Free Fire Tournament - Client-side Interactive Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Hide Global Loading Spinner
    hideLoader();

    // 2. Back to Top Button Behavior
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 300) {
                backToTopBtn.style.display = 'flex';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });

        backToTopBtn.addEventListener('click', function () {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // 3. Leaderboard Search Filter
    const leaderboardSearch = document.getElementById('leaderboard-search');
    if (leaderboardSearch) {
        leaderboardSearch.addEventListener('keyup', function () {
            const query = this.value.toLowerCase();
            const rows = document.querySelectorAll('#leaderboard-table tbody tr');

            rows.forEach(row => {
                const teamName = row.querySelector('.team-name').textContent.toLowerCase();
                const captainName = row.querySelector('.captain-name').textContent.toLowerCase();
                if (teamName.includes(query) || captainName.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 4. Leaderboard AJAX Refresh Simulation
    const refreshBtn = document.getElementById('refresh-leaderboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function () {
            showLoader();
            // Simulate API request delay
            setTimeout(() => {
                hideLoader();
                showToast('Leaderboard updated successfully!', 'success');
                // Reload the page content (in real apps, we would fetch JSON)
                location.reload();
            }, 1000);
        });
    }

    // 5. Tournament Filter System (Client-side)
    const filterButtons = document.querySelectorAll('.tournament-filter-btn');
    if (filterButtons.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                // Toggle active button class
                filterButtons.forEach(b => b.classList.remove('btn-cyber-orange'));
                filterButtons.forEach(b => b.classList.add('btn-cyber-cyan'));
                this.classList.remove('btn-cyber-cyan');
                this.classList.add('btn-cyber-orange');

                const filterValue = this.getAttribute('data-filter');
                const cards = document.querySelectorAll('.tournament-card-col');

                cards.forEach(card => {
                    const cardStatus = card.getAttribute('data-status').toLowerCase();
                    if (filterValue === 'all' || cardStatus === filterValue) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // 6. Copy Registration Link
    const copyLinkBtn = document.getElementById('copy-registration-link');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', function () {
            const registerUrl = window.location.origin + '/register/';
            navigator.clipboard.writeText(registerUrl).then(() => {
                showToast('Registration URL copied to clipboard!', 'info');
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        });
    }

    // 7. Schedule PDF / Print Download
    const downloadScheduleBtn = document.getElementById('download-schedule');
    if (downloadScheduleBtn) {
        downloadScheduleBtn.addEventListener('click', function () {
            window.print();
        });
    }

    // 8. Form Validation for Registration page
    const registerForm = document.getElementById('registration-form');
    if (registerForm) {
        const passwordInput = document.getElementById('reg-password');
        const confirmPasswordInput = document.getElementById('reg-confirm-password');
        const phoneInput = document.getElementById('reg-phone');
        const gameIdInput = document.getElementById('reg-gameid');
        const strengthMeter = document.getElementById('password-strength-meter');
        const strengthText = document.getElementById('password-strength-text');

        // Password strength meter keyup
        if (passwordInput) {
            passwordInput.addEventListener('keyup', function () {
                const password = this.value;
                let strength = 0;
                
                if (password.length >= 6) strength += 20;
                if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 20;
                if (password.match(/\d/)) strength += 20;
                if (password.match(/[^a-zA-Z\d]/)) strength += 20;
                if (password.length >= 10) strength += 20;

                strengthMeter.style.width = strength + '%';
                
                if (strength <= 40) {
                    strengthMeter.className = 'progress-bar bg-danger';
                    strengthText.textContent = 'Weak';
                    strengthText.style.color = '#ef4444';
                } else if (strength <= 80) {
                    strengthMeter.className = 'progress-bar bg-warning';
                    strengthText.textContent = 'Medium';
                    strengthText.style.color = '#eab308';
                } else {
                    strengthMeter.className = 'progress-bar bg-success';
                    strengthText.textContent = 'Strong';
                    strengthText.style.color = '#22c55e';
                }
            });
        }

        registerForm.addEventListener('submit', function (e) {
            let valid = true;

            // Password matching
            if (passwordInput.value !== confirmPasswordInput.value) {
                showToast('Passwords do not match.', 'danger');
                confirmPasswordInput.classList.add('is-invalid');
                valid = false;
            } else {
                confirmPasswordInput.classList.remove('is-invalid');
            }

            // Password length check
            if (passwordInput.value.length < 6) {
                showToast('Password must be at least 6 characters long.', 'danger');
                passwordInput.classList.add('is-invalid');
                valid = false;
            } else {
                passwordInput.classList.remove('is-invalid');
            }

            // Game ID validation (numbers check)
            if (gameIdInput && !/^\d+$/.test(gameIdInput.value)) {
                showToast('Game ID must contain numbers only.', 'danger');
                gameIdInput.classList.add('is-invalid');
                valid = false;
            } else {
                gameIdInput.classList.remove('is-invalid');
            }

            // Phone validation
            if (phoneInput && !phoneInput.checkValidity()) {
                showToast('Please enter a valid phone number.', 'danger');
                phoneInput.classList.add('is-invalid');
                valid = false;
            } else {
                phoneInput.classList.remove('is-invalid');
            }

            if (!valid) {
                e.preventDefault();
            } else {
                showLoader();
            }
        });
    }

    // 9. Countdown Timer Function for Home page
    const countdownElement = document.getElementById('countdown-timer');
    if (countdownElement) {
        const targetDateStr = countdownElement.getAttribute('data-date');
        if (targetDateStr) {
            const targetDate = new Date(targetDateStr).getTime();

            const timerInterval = setInterval(function () {
                const now = new Date().getTime();
                const distance = targetDate - now;

                if (distance < 0) {
                    clearInterval(timerInterval);
                    countdownElement.innerHTML = "<span class='text-neon-orange font-heading fw-bold'>TOURNAMENT LIVE / ONGOING</span>";
                    return;
                }

                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);

                document.getElementById('days').innerText = String(days).padStart(2, '0');
                document.getElementById('hours').innerText = String(hours).padStart(2, '0');
                document.getElementById('minutes').innerText = String(minutes).padStart(2, '0');
                document.getElementById('seconds').innerText = String(seconds).padStart(2, '0');
            }, 1000);
        }
    }
    // 10. Home page Prize Pool Count Animation
    const prizeElements = document.querySelectorAll('.animate-prize');
    if (prizeElements.length > 0) {
        prizeElements.forEach(el => {
            const finalVal = parseInt(el.getAttribute('data-value'));
            let currentVal = 0;
            const duration = 1500; // 1.5s animation
            const stepTime = Math.abs(Math.floor(duration / finalVal));
            const increment = finalVal > 100 ? Math.ceil(finalVal / 100) : 1;

            const timer = setInterval(() => {
                currentVal += increment;
                if (currentVal >= finalVal) {
                    currentVal = finalVal;
                    clearInterval(timer);
                }
                el.innerText = '€' + currentVal;
            }, stepTime);
        });
    }
});
// Loading spinner functions
function showLoader() {
    const loader = document.getElementById('spinner-container');
    if (loader) {
        loader.style.opacity = '1';
        loader.style.visibility = 'visible';
    }
}

function hideLoader() {
    const loader = document.getElementById('spinner-container');
    if (loader) {
        loader.style.opacity = '0';
        // Wait for CSS transition
        setTimeout(() => {
            loader.style.visibility = 'hidden';
        }, 500);
    }
}

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container-area');
    if (!container) return;

    // Type mapping to bootstrap classes
    const alertClass = type === 'error' || type === 'danger' ? 'danger' : type;

    const toastHtml = `
        <div class="toast show border-neon-cyan mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-dark text-white border-bottom border-secondary d-flex justify-content-between align-items-center">
                <span class="fw-bold text-${alertClass}"><i class="fas fa-gamepad me-2"></i>ARENA ANNOUNCEMENT</span>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body text-white bg-dark-blue">
                ${message}
            </div>
        </div>
    `;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = toastHtml;
    const toastElement = wrapper.firstElementChild;
    container.appendChild(toastElement);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toastElement.classList.remove('show');
        toastElement.classList.add('hide');
        setTimeout(() => {
            toastElement.remove();
        }, 500);
    }, 4000);

    // Close button event
    const closeBtn = toastElement.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            toastElement.remove();
        });
    }
}
