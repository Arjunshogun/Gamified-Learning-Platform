/**
 * quizzes.js - Knowledge Duel & Quiz Sprint Runner for QuestAcademy
 */

let activeQuiz = null;
let currentQuestionIndex = 0;
let userQuizAnswers = {};
let quizTimerInterval = null;
let quizElapsedSeconds = 0;
let hintsUsedCount = 0;

function openQuizRunner(activityId) {
    window.sound.playClick();
    fetch(`/api/activities/${activityId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            activeQuiz = data.activity;
            currentQuestionIndex = 0;
            userQuizAnswers = {};
            hintsUsedCount = 0;
            quizElapsedSeconds = 0;
            
            const modal = document.getElementById("quiz-modal");
            document.getElementById("quiz-modal-title").innerText = activeQuiz.title;
            document.getElementById("quiz-modal-topic").innerText = `${activeQuiz.topic} • ${activeQuiz.difficulty}`;
            
            startQuizTimer();
            renderCurrentQuestion();
            modal.classList.add("active");
        });
}

function startQuizTimer() {
    clearInterval(quizTimerInterval);
    const timerElem = document.getElementById("quiz-timer-text");
    quizElapsedSeconds = 0;
    quizTimerInterval = setInterval(() => {
        quizElapsedSeconds++;
        const mins = String(Math.floor(quizElapsedSeconds / 60)).padStart(2, "0");
        const secs = String(quizElapsedSeconds % 60).padStart(2, "0");
        if (timerElem) timerElem.innerText = `${mins}:${secs}`;
    }, 1000);
}

function renderCurrentQuestion() {
    const questions = activeQuiz.content;
    const q = questions[currentQuestionIndex];
    const container = document.getElementById("quiz-question-container");
    const progressElem = document.getElementById("quiz-progress-text");
    
    progressElem.innerText = `Question ${currentQuestionIndex + 1} of ${questions.length}`;

    let html = `
        <div style="margin-bottom: 1.5rem;">
            <h3 style="font-size: 1.15rem; color: #fff; margin-bottom: 1rem;">${q.question}</h3>
            <div class="options-list">
    `;

    q.options.forEach((opt, idx) => {
        const isSelected = userQuizAnswers[q.id] === idx;
        html += `
            <div class="quiz-option ${isSelected ? 'selected' : ''}" onclick="selectQuizOption('${q.id}', ${idx})">
                <span style="width: 24px; height: 24px; border-radius: 50%; border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold;">
                    ${String.fromCharCode(65 + idx)}
                </span>
                <span style="font-size: 0.95rem;">${opt}</span>
            </div>
        `;
    });

    html += `</div></div>`;
    container.innerHTML = html;

    // Update navigation buttons
    document.getElementById("btn-quiz-prev").style.display = currentQuestionIndex > 0 ? "block" : "none";
    const nextBtn = document.getElementById("btn-quiz-next");
    if (currentQuestionIndex === questions.length - 1) {
        nextBtn.innerText = "Submit Sprint ⚔️";
        nextBtn.onclick = submitQuizSprint;
    } else {
        nextBtn.innerText = "Next Question →";
        nextBtn.onclick = () => {
            window.sound.playClick();
            currentQuestionIndex++;
            renderCurrentQuestion();
        };
    }
}

function selectQuizOption(questionId, optionIndex) {
    window.sound.playClick();
    userQuizAnswers[questionId] = optionIndex;
    renderCurrentQuestion();
}

function submitQuizSprint() {
    clearInterval(quizTimerInterval);
    const reflectionText = document.getElementById("quiz-reflection-input")?.value || "";

    const payload = {
        answers: userQuizAnswers,
        duration_seconds: quizElapsedSeconds,
        hints_used: hintsUsedCount,
        reflection_text: reflectionText
    };

    fetch(`/api/activities/${activeQuiz.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(res => {
        if (!res.success) {
            window.showToast("Error submitting quiz", "error");
            return;
        }

        closeQuizModal();
        window.showRewardCelebrationModal(res);
        window.refreshUserHUD();
        window.loadActivities();
    });
}

function closeQuizModal() {
    clearInterval(quizTimerInterval);
    document.getElementById("quiz-modal").classList.remove("active");
}
