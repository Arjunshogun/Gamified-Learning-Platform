/**
 * leaderboard.js - Real-Time Leaderboards (Individual, Batch Battle & Streaks)
 */

let currentLbType = "individual";
let currentLbTimeframe = "all";

function loadLeaderboards() {
    const container = document.getElementById("leaderboard-container");
    container.innerHTML = "<div style='text-align: center; color: var(--text-muted); padding: 2rem;'>Loading rankings...</div>";

    fetch(`/api/leaderboard?type=${currentLbType}&timeframe=${currentLbTimeframe}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;

            if (currentLbType === "individual") {
                renderIndividualLeaderboard(data.leaderboard, data.user_rank);
            } else if (currentLbType === "batch") {
                renderBatchLeaderboard(data.batches);
            } else if (currentLbType === "streak") {
                renderStreakLeaderboard(data.streaks);
            }
        });
}

function setLeaderboardType(type) {
    window.sound.playClick();
    currentLbType = type;
    document.querySelectorAll(".lb-tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-type") === type);
    });
    loadLeaderboards();
}

function renderIndividualLeaderboard(users, userRank) {
    const container = document.getElementById("leaderboard-container");
    
    // Podium for top 3
    const top3 = users.slice(0, 3);
    const rest = users.slice(3);

    let podiumHtml = `<div class="podium-container">`;
    if (top3[1]) {
        podiumHtml += `
            <div class="podium-card rank-2">
                <div class="podium-rank-badge">🥈 2nd</div>
                <div class="avatar-wrapper ${top3[1].equipped_frame || ''}" style="margin-bottom: 0.5rem;">
                    👤
                </div>
                <div style="font-weight: 700; color: #fff;">${top3[1].full_name}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${top3[1].equipped_title || 'Novice'}</div>
                <div style="font-size: 0.85rem; font-weight: bold; color: var(--primary); margin-top: 0.4rem;">${top3[1].xp.toLocaleString()} XP</div>
            </div>
        `;
    }
    if (top3[0]) {
        podiumHtml += `
            <div class="podium-card rank-1">
                <div class="podium-rank-badge">👑 1st</div>
                <div class="avatar-wrapper ${top3[0].equipped_frame || 'frame_dragon_gold'}" style="margin-bottom: 0.5rem;">
                    ⚡
                </div>
                <div style="font-weight: 800; color: #fff; font-size: 1.05rem;">${top3[0].full_name}</div>
                <div style="font-size: 0.75rem; color: var(--accent-gold); font-weight: bold;">${top3[0].equipped_title || 'Champion'}</div>
                <div style="font-size: 1rem; font-weight: 800; color: var(--accent-gold); margin-top: 0.4rem;">${top3[0].xp.toLocaleString()} XP</div>
            </div>
        `;
    }
    if (top3[2]) {
        podiumHtml += `
            <div class="podium-card rank-3">
                <div class="podium-rank-badge">🥉 3rd</div>
                <div class="avatar-wrapper ${top3[2].equipped_frame || ''}" style="margin-bottom: 0.5rem;">
                    👤
                </div>
                <div style="font-weight: 700; color: #fff;">${top3[2].full_name}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${top3[2].equipped_title || 'Scholar'}</div>
                <div style="font-size: 0.85rem; font-weight: bold; color: var(--primary); margin-top: 0.4rem;">${top3[2].xp.toLocaleString()} XP</div>
            </div>
        `;
    }
    podiumHtml += `</div>`;

    // Rest of table
    let tableHtml = `
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th style="width: 60px;">Rank</th>
                    <th>Student Learner</th>
                    <th>Batch / Cohort</th>
                    <th>Level</th>
                    <th>Streak</th>
                    <th>Badges</th>
                    <th style="text-align: right;">Total XP</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach(u => {
        const isSelf = u.id === window.activeUserId;
        const deltaColor = u.rank_delta > 0 ? "var(--accent-emerald)" : (u.rank_delta < 0 ? "var(--accent-rose)" : "var(--text-dim)");
        const deltaSymbol = u.rank_delta > 0 ? `▲ +${u.rank_delta}` : (u.rank_delta < 0 ? `▼ ${u.rank_delta}` : "• 0");

        tableHtml += `
            <tr class="${isSelf ? 'current-user' : ''}">
                <td>
                    <span style="font-weight: 800; font-size: 1rem; color: #fff;">#${u.rank}</span>
                    <span style="font-size: 0.7rem; color: ${deltaColor}; margin-left: 4px;">${deltaSymbol}</span>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div class="avatar-wrapper ${u.equipped_frame || ''}" style="width: 32px; height: 32px; font-size: 1rem;">
                            ${u.id === 1 ? '⚡' : '👤'}
                        </div>
                        <div>
                            <div style="font-weight: 700; color: #fff;">${u.full_name} ${isSelf ? '<span style="color: var(--primary); font-size: 0.75rem;">(You)</span>' : ''}</div>
                            <div style="font-size: 0.72rem; color: var(--text-muted);">${u.equipped_title || 'Novice'}</div>
                        </div>
                    </div>
                </td>
                <td><span style="font-size: 0.82rem; color: var(--text-muted);">${u.batch_cohort}</span></td>
                <td><span class="player-level-badge">Lvl ${u.level}</span></td>
                <td><span style="color: #f97316; font-weight: bold;">🔥 ${u.current_streak}d</span></td>
                <td><span style="color: var(--accent-gold);">🎖️ ${u.badge_count}</span></td>
                <td style="text-align: right;"><span style="font-weight: 800; color: var(--primary); font-size: 1rem;">${u.xp.toLocaleString()} XP</span></td>
            </tr>
        `;
    });

    tableHtml += `</tbody></table>`;
    container.innerHTML = podiumHtml + tableHtml;
}

function renderBatchLeaderboard(batches) {
    const container = document.getElementById("leaderboard-container");
    let html = `
        <div style="margin-bottom: 1.5rem; color: var(--text-muted); font-size: 0.9rem;">
            Batch Cohort Battle: Average XP per student determines cohort velocity and unlocked team perks!
        </div>
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th>Cohort Rank</th>
                    <th>Batch Name</th>
                    <th>Students</th>
                    <th>Avg XP / Student</th>
                    <th>Avg Streak</th>
                    <th>Activities Done</th>
                    <th style="text-align: right;">Velocity Score</th>
                </tr>
            </thead>
            <tbody>
    `;

    batches.forEach(b => {
        html += `
            <tr>
                <td><span style="font-weight: 800; font-size: 1.1rem; color: var(--accent-gold);">#${b.rank}</span></td>
                <td><span style="font-weight: 700; color: #fff; font-size: 1rem;">🛡️ ${b.batch_cohort}</span></td>
                <td>${b.student_count} Scholars</td>
                <td><span style="color: var(--primary); font-weight: bold;">${b.avg_xp_per_student.toLocaleString()} XP</span></td>
                <td><span style="color: #f97316; font-weight: bold;">🔥 ${b.avg_streak}d</span></td>
                <td>${b.total_activities_completed}</td>
                <td style="text-align: right;"><span style="font-weight: 800; color: var(--accent-emerald); font-size: 1.05rem;">${b.velocity_score} pts</span></td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderStreakLeaderboard(streaks) {
    const container = document.getElementById("leaderboard-container");
    let html = `
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th>Streak Rank</th>
                    <th>Learner</th>
                    <th>Batch</th>
                    <th>Current Streak</th>
                    <th style="text-align: right;">Best Record Streak</th>
                </tr>
            </thead>
            <tbody>
    `;

    streaks.forEach(s => {
        html += `
            <tr>
                <td><span style="font-weight: 800; font-size: 1rem; color: #fff;">#${s.rank}</span></td>
                <td>
                    <div style="font-weight: 700; color: #fff;">${s.full_name}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted);">${s.equipped_title || 'Scholar'}</div>
                </td>
                <td>${s.batch_cohort}</td>
                <td><span style="color: #f97316; font-weight: 800; font-size: 1.05rem;">🔥 ${s.current_streak} Days Active</span></td>
                <td style="text-align: right;"><span style="color: var(--accent-gold); font-weight: bold;">⚡ ${s.max_streak} Days</span></td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}
