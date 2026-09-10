/**
 * admin.js - Faculty Control Room, Dynamic Rule Configurator & Anti-Farming Audit
 */

function loadFacultyAdmin() {
    loadScoringRules();
    loadAntiFarmingAuditLogs();
    loadAnalyticsDashboard();
}

function loadScoringRules() {
    fetch("/api/admin/rules")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            renderScoringSliders(data.rules);
        });
}

function renderScoringSliders(rules) {
    const container = document.getElementById("admin-rules-container");
    let html = "";

    const ruleLabels = {
        "base_quiz_xp": { label: "Base Quiz XP", min: 50, max: 300, step: 10, unit: "XP" },
        "base_code_xp": { label: "Base Code Quest XP", min: 100, max: 500, step: 10, unit: "XP" },
        "streak_multiplier_step": { label: "Daily Streak Bonus Step", min: 0.01, max: 0.15, step: 0.01, unit: "per day", format: v => `${Math.round(v*100)}%` },
        "max_streak_multiplier": { label: "Max Streak Multiplier Cap", min: 1.2, max: 2.5, step: 0.05, unit: "x Max", format: v => `${v}x` },
        "diminishing_attempt_2": { label: "2nd Attempt Yield", min: 0.1, max: 0.9, step: 0.05, unit: "Yield", format: v => `${Math.round(v*100)}%` },
        "diminishing_attempt_3": { label: "3rd Attempt Yield", min: 0.0, max: 0.5, step: 0.05, unit: "Yield", format: v => `${Math.round(v*100)}%` },
        "min_seconds_per_quiz_q": { label: "Anti-Farming Min Time / Question", min: 1, max: 10, step: 1, unit: "seconds" },
        "daily_xp_hard_cap": { label: "Daily XP Hard Cap (Anti-Bot)", min: 500, max: 5000, step: 100, unit: "XP" },
        "cooldown_seconds_retry": { label: "Retry Cooldown Interval", min: 5, max: 60, step: 5, unit: "seconds" }
    };

    rules.forEach(r => {
        const meta = ruleLabels[r.config_key] || { label: r.config_key, min: 1, max: 100, step: 1, unit: "" };
        const displayVal = meta.format ? meta.format(parseFloat(r.config_value)) : `${r.config_value} ${meta.unit}`;
        
        html += `
            <div class="rule-slider-group">
                <div class="rule-label-row">
                    <span style="color: #fff;">${meta.label}</span>
                    <span id="display-${r.config_key}" style="color: var(--primary); font-family: var(--font-mono); font-weight: bold;">${displayVal}</span>
                </div>
                <input type="range" class="rule-slider" id="slider-${r.config_key}" 
                    min="${meta.min}" max="${meta.max}" step="${meta.step}" value="${r.config_value}"
                    oninput="updateRuleDisplay('${r.config_key}', this.value, '${meta.unit}', ${meta.format ? 'true' : 'false'})">
                <div style="font-size: 0.72rem; color: var(--text-dim);">${r.description || ''}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function updateRuleDisplay(key, val, unit, hasFormat) {
    const displayElem = document.getElementById(`display-${key}`);
    if (displayElem) {
        if (hasFormat) {
            if (key.includes("multiplier_step") || key.includes("diminishing")) {
                displayElem.innerText = `${Math.round(parseFloat(val)*100)}%`;
            } else {
                displayElem.innerText = `${val}x`;
            }
        } else {
            displayElem.innerText = `${val} ${unit}`.trim();
        }
    }
}

function saveFacultyRules() {
    window.sound.playClick();
    const sliders = document.querySelectorAll(".rule-slider");
    const rules = {};
    sliders.forEach(s => {
        const key = s.id.replace("slider-", "");
        rules[key] = s.value;
    });

    fetch("/api/admin/rules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rules: rules })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) {
            window.showToast("Scoring and Anti-Farming parameters saved!", "success");
            window.sound.playSuccess();
        }
    });
}

function loadAntiFarmingAuditLogs() {
    fetch("/api/admin/audit-logs")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            renderAuditTable(data.audit_logs);
        });
}

function renderAuditTable(logs) {
    const container = document.getElementById("admin-audit-table-body");
    if (!logs || logs.length === 0) {
        container.innerHTML = "<tr><td colspan='6' style='text-align: center; color: var(--text-muted);'>No security incidents logged.</td></tr>";
        return;
    }

    let html = "";
    logs.forEach(l => {
        const isResolved = l.status !== "flagged";
        html += `
            <tr>
                <td><span class="flag-badge ${l.violation_type}">${l.violation_type}</span></td>
                <td>
                    <div style="font-weight: bold; color: #fff;">${l.full_name}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">${l.batch_cohort}</div>
                </td>
                <td><span style="font-size: 0.8rem; color: #fff;">${l.activity_title || 'General Task'}</span></td>
                <td><span style="font-size: 0.78rem; color: var(--text-muted);">${l.detected_details}</span></td>
                <td><span style="font-size: 0.78rem; color: var(--accent-rose);">${l.penalty_applied}</span></td>
                <td style="text-align: right;">
                    ${isResolved ? `<span style="font-size: 0.75rem; color: var(--accent-emerald); font-weight: bold;">${l.status.toUpperCase()}</span>` : `
                        <button class="btn-secondary" style="padding: 2px 8px; font-size: 0.72rem; margin-right: 4px;" onclick="resolveAuditIncident(${l.id}, 'pardoned')">Pardon</button>
                        <button class="btn-secondary" style="padding: 2px 8px; font-size: 0.72rem; border-color: var(--accent-rose); color: var(--accent-rose);" onclick="resolveAuditIncident(${l.id}, 'confirmed')">Confirm</button>
                    `}
                </td>
            </tr>
        `;
    });

    container.innerHTML = html;
}

function resolveAuditIncident(logId, action) {
    window.sound.playClick();
    fetch(`/api/admin/audit-logs/${logId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: action })
    })
    .then(r => r.json())
    .then(res => {
        window.showToast(`Incident #${logId} marked as ${action}!`, "success");
        loadAntiFarmingAuditLogs();
    });
}

function loadAnalyticsDashboard() {
    fetch("/api/admin/analytics")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            document.getElementById("analytics-students-count").innerText = data.total_students;
            document.getElementById("analytics-activities-count").innerText = data.total_activities_completed.toLocaleString();
            document.getElementById("analytics-xp-count").innerText = `${data.total_xp_awarded.toLocaleString()} XP`;
            document.getElementById("analytics-abuse-count").innerText = `${data.abuse_attempts_prevented} Blocked`;

            renderAnalyticsComparison(data.gamification_impact);
        });
}

function renderAnalyticsComparison(impact) {
    const container = document.getElementById("analytics-impact-container");
    let html = `
        <div class="grid-2">
            <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">Course Retention Rate</div>
                <div style="display: flex; align-items: baseline; gap: 0.75rem;">
                    <span style="font-size: 1.6rem; font-weight: 800; color: var(--accent-emerald);">${impact.retention_rate.questacademy}%</span>
                    <span style="font-size: 0.85rem; color: var(--accent-emerald); font-weight: bold;">${impact.retention_rate.improvement_percent}</span>
                    <span style="font-size: 0.75rem; color: var(--text-dim);">(vs ${impact.retention_rate.traditional}% Trad.)</span>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">Weekly Learning Consistency</div>
                <div style="display: flex; align-items: baseline; gap: 0.75rem;">
                    <span style="font-size: 1.6rem; font-weight: 800; color: var(--primary);">${impact.weekly_completion_consistency.questacademy}%</span>
                    <span style="font-size: 0.85rem; color: var(--primary); font-weight: bold;">${impact.weekly_completion_consistency.improvement_percent}</span>
                    <span style="font-size: 0.75rem; color: var(--text-dim);">(vs ${impact.weekly_completion_consistency.traditional}% Trad.)</span>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}
