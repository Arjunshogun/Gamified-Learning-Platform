/**
 * demo_runner.js - 1-Click Interactive Guided Demo & Judge Walkthrough Tour
 */

let demoStepIndex = 0;
const demoSteps = [
    {
        title: "Step 1: Daily Operations & Claiming Rewards",
        desc: "Students start by checking daily quests, streaks, and collective raid boss status. Let's claim an active quest reward.",
        action: async () => {
            window.navigateToView("quests");
            const claimBtn = document.querySelector(".btn-claim");
            if (claimBtn) {
                claimBtn.click();
            } else {
                window.showToast("Daily Quests loaded and active!", "success");
            }
        }
    },
    {
        title: "Step 2: Interactive Knowledge Sprint & Multipliers",
        desc: "Let's launch a Knowledge Sprint Quiz. Solving with high accuracy and reflection awards streak and first-try multipliers.",
        action: async () => {
            window.navigateToView("arena");
            openQuizRunner(1);
        }
    },
    {
        title: "Step 3: Anti-Farming & Abuse Detection in Action",
        desc: "Simulating a bot / rapid-click attack (<2s completion). QuestAcademy automatically intercepts the speed anomaly and issues 0 XP.",
        action: async () => {
            closeQuizModal();
            const res = await fetch("/api/demo/simulate-activity", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ type: "speed_farm_block" })
            }).then(r => r.json());

            window.showRewardCelebrationModal(res.result);
            window.refreshUserHUD();
        }
    },
    {
        title: "Step 4: Code Quest Arena & Real-Time Test Runner",
        desc: "Opening Algorithmic Code Arena. Watch the live Python/JS sandbox execute test cases with syntax verification.",
        action: async () => {
            window.navigateToView("arena");
            openCodeQuestRunner(3);
            setTimeout(() => {
                runCodeTestCases();
            }, 800);
        }
    },
    {
        title: "Step 5: Batch Cohort Leaderboard & Skill Radar",
        desc: "Inspect real-time cohort velocity (Batch CS-Alpha vs CS-Beta) and the 5-Axis Skill Radar + 52-week activity heatmap.",
        action: async () => {
            closeCodeModal();
            window.navigateToView("leaderboard");
            setLeaderboardType("batch");
            setTimeout(() => {
                window.navigateToView("profile");
            }, 2000);
        }
    },
    {
        title: "Step 6: Faculty Control Room & Security Audit Logs",
        desc: "Faculty view showing dynamic scoring rule sliders, the anti-farming security log with the flagged attempt, and engagement graphs.",
        action: async () => {
            window.navigateToView("faculty");
            loadFacultyAdmin();
        }
    }
];

function openDemoTourModal() {
    window.sound.playClick();
    demoStepIndex = 0;
    renderDemoTourStep();
    document.getElementById("demo-tour-modal").classList.add("active");
}

function renderDemoTourStep() {
    const step = demoSteps[demoStepIndex];
    document.getElementById("demo-step-title").innerText = step.title;
    document.getElementById("demo-step-desc").innerText = step.desc;
    document.getElementById("demo-step-counter").innerText = `Step ${demoStepIndex + 1} of ${demoSteps.length}`;
}

function nextDemoStep() {
    window.sound.playClick();
    const step = demoSteps[demoStepIndex];
    step.action();

    if (demoStepIndex < demoSteps.length - 1) {
        demoStepIndex++;
        renderDemoTourStep();
    } else {
        document.getElementById("demo-tour-modal").classList.remove("active");
        window.showToast("Guided Demo Tour Completed! Feel free to explore any mode freely.", "success");
    }
}

function closeDemoTourModal() {
    document.getElementById("demo-tour-modal").classList.remove("active");
}
