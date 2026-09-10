/**
 * code_quest.js - Interactive Code Arena & Algorithmic Challenge Runner
 */

let activeCodeQuest = null;
let codeTimerInterval = null;
let codeElapsedSeconds = 0;
let codeHintsUnlocked = 0;

function openCodeQuestRunner(activityId) {
    window.sound.playClick();
    fetch(`/api/activities/${activityId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            activeCodeQuest = data.activity;
            codeElapsedSeconds = 0;
            codeHintsUnlocked = 0;

            const modal = document.getElementById("code-modal");
            document.getElementById("code-modal-title").innerText = activeCodeQuest.title;
            document.getElementById("code-modal-desc").innerText = activeCodeQuest.content.problem_statement;
            document.getElementById("code-modal-complexity").innerText = `Target: ${activeCodeQuest.content.expected_complexity || 'O(n)'}`;

            // Load starter code
            const lang = document.getElementById("code-lang-select").value;
            const starter = activeCodeQuest.content.starter_code?.[lang] || "# Write solution here\n";
            document.getElementById("code-editor").value = starter;
            
            document.getElementById("code-terminal-output").innerHTML = "Ready. Click 'Run Tests' to verify solution against test cases.";
            document.getElementById("code-hints-drawer").innerHTML = "";

            startCodeTimer();
            modal.classList.add("active");
        });
}

function startCodeTimer() {
    clearInterval(codeTimerInterval);
    const timerElem = document.getElementById("code-timer-text");
    codeElapsedSeconds = 0;
    codeTimerInterval = setInterval(() => {
        codeElapsedSeconds++;
        const mins = String(Math.floor(codeElapsedSeconds / 60)).padStart(2, "0");
        const secs = String(codeElapsedSeconds % 60).padStart(2, "0");
        if (timerElem) timerElem.innerText = `${mins}:${secs}`;
    }, 1000);
}

function runCodeTestCases() {
    window.sound.playClick();
    const code = document.getElementById("code-editor").value;
    const lang = document.getElementById("code-lang-select").value;
    const terminal = document.getElementById("code-terminal-output");
    
    terminal.innerHTML = "<span style='color: var(--primary);'>Executing test cases in sandbox...</span>";

    fetch("/api/code/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            code: code,
            activity_id: activeCodeQuest.id,
            language: lang
        })
    })
    .then(r => r.json())
    .then(res => {
        if (!res.success) {
            terminal.innerHTML = `<span style='color: var(--accent-rose);'>Execution Error: ${res.message || 'Check syntax'}</span>`;
            window.sound.playError();
            return;
        }

        let outputHtml = `<div style='margin-bottom: 6px; font-weight: bold;'>Results: ${res.passed}/${res.total} Test Cases Passed</div>`;
        res.results.forEach(t => {
            const statusColor = t.passed ? "var(--accent-emerald)" : "var(--accent-rose)";
            const statusIcon = t.passed ? "✔ PASS" : "✖ FAIL";
            outputHtml += `
                <div style="margin-bottom: 4px; font-size: 0.8rem;">
                    <span style="color: ${statusColor}; font-weight: bold;">[${statusIcon}]</span> 
                    Test ${t.test_index}: Input: <code>${t.input}</code> | Expected: <code>${t.expected}</code> | Output: <code>${t.output || t.error}</code>
                </div>
            `;
        });

        terminal.innerHTML = outputHtml;

        if (res.all_passed) {
            window.sound.playSuccess();
        } else {
            window.sound.playError();
        }
    });
}

function unlockNextHint() {
    window.sound.playClick();
    const hints = activeCodeQuest.hints || [];
    if (codeHintsUnlocked >= hints.length) {
        window.showToast("All available hints unlocked!", "warning");
        return;
    }

    codeHintsUnlocked++;
    const drawer = document.getElementById("code-hints-drawer");
    let html = "<div style='font-size: 0.85rem; color: var(--accent-gold); font-weight: bold; margin-bottom: 4px;'>Unlocked Hints (Costs first-try bonus):</div>";
    for (let i = 0; i < codeHintsUnlocked; i++) {
        html += `<div style="font-size: 0.82rem; background: rgba(245, 158, 11, 0.1); padding: 6px 10px; border-radius: 4px; border: 1px solid rgba(245, 158, 11, 0.3); margin-bottom: 4px;">💡 ${hints[i]}</div>`;
    }
    drawer.innerHTML = html;
}

function submitCodeQuest() {
    clearInterval(codeTimerInterval);
    const code = document.getElementById("code-editor").value;
    const lang = document.getElementById("code-lang-select").value;
    const reflectionText = document.getElementById("code-reflection-input")?.value || "";

    const payload = {
        code: code,
        language: lang,
        duration_seconds: codeElapsedSeconds,
        hints_used: codeHintsUnlocked,
        reflection_text: reflectionText
    };

    fetch(`/api/activities/${activeCodeQuest.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(res => {
        if (!res.success) {
            window.showToast("Submission failed", "error");
            return;
        }

        closeCodeModal();
        window.showRewardCelebrationModal(res);
        window.refreshUserHUD();
        window.loadActivities();
    });
}

function closeCodeModal() {
    clearInterval(codeTimerInterval);
    document.getElementById("code-modal").classList.remove("active");
}
