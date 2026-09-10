/**
 * app.js - Main Application Controller for QuestAcademy
 */

window.activeUserId = 1;

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    loadUserSwitcher();
    refreshUserHUD();
    loadQuestsView();
    setupConfettiCanvas();
    updateMuteButtonDisplay();
}

function updateMuteButtonDisplay() {
    const btn = document.getElementById("btn-toggle-sound");
    if (btn) {
        btn.innerHTML = window.sound.isMuted() ? "🔇" : "🔊";
    }
}

function toggleAudio() {
    const muted = window.sound.toggleMute();
    updateMuteButtonDisplay();
    showToast(muted ? "Sound Effects Muted" : "Sound Effects Enabled", "warning");
}

function loadUserSwitcher() {
    fetch("/api/users")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            const select = document.getElementById("user-switcher-select");
            select.innerHTML = "";
            data.users.forEach(u => {
                const opt = document.createElement("option");
                opt.value = u.id;
                opt.innerText = `${u.full_name} (${u.role.toUpperCase()} • Lvl ${u.level})`;
                if (u.id === data.active_user_id) {
                    opt.selected = true;
                    window.activeUserId = u.id;
                }
                select.appendChild(opt);
            });
        });
}

function handleUserSwitch(userId) {
    window.sound.playClick();
    fetch("/api/user/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: parseInt(userId) })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) {
            window.activeUserId = parseInt(userId);
            refreshUserHUD();
            // Reload current view
            const activeNav = document.querySelector(".nav-item.active");
            if (activeNav) {
                const viewName = activeNav.getAttribute("data-view");
                navigateToView(viewName);
            }
            showToast(`Switched user profile!`, "success");
        }
    });
}

function refreshUserHUD() {
    fetch(`/api/user/hud?user_id=${window.activeUserId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            const u = data.user;
            const lvl = data.level_progress;

            // Update Topbar HUD
            document.getElementById("hud-user-name").innerText = u.full_name;
            document.getElementById("hud-level-badge").innerText = `Lvl ${lvl.level}`;
            document.getElementById("hud-streak-count").innerText = `${u.current_streak}d`;
            document.getElementById("hud-gold-count").innerText = u.gold.toLocaleString();
            document.getElementById("hud-gems-count").innerText = u.gems;

            // XP Bar
            const xpFill = document.getElementById("hud-xp-fill");
            const xpText = document.getElementById("hud-xp-text");
            if (xpFill) xpFill.style.width = `${lvl.progress_percent}%`;
            if (xpText) xpText.innerText = `${lvl.current_xp.toLocaleString()} / ${lvl.next_level_xp.toLocaleString()} XP (${lvl.progress_percent}%)`;

            // Avatar Frame
            const avatarWrapper = document.getElementById("hud-avatar");
            if (avatarWrapper) {
                avatarWrapper.className = `avatar-wrapper ${u.equipped_frame || ''}`;
                avatarWrapper.innerHTML = u.id === 1 ? '⚡' : '👤';
            }

            // Quests Badge
            const questsBadge = document.getElementById("nav-badge-quests");
            if (questsBadge) {
                questsBadge.style.display = data.claimable_quests_count > 0 ? "inline-block" : "none";
                questsBadge.innerText = data.claimable_quests_count;
            }
        });
}

function navigateToView(viewName) {
    window.sound.playClick();
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.toggle("active", item.getAttribute("data-view") === viewName);
    });

    document.querySelectorAll(".view-section").forEach(sec => {
        sec.classList.toggle("active", sec.id === `view-${viewName}`);
    });

    if (viewName === "quests") loadQuestsView();
    else if (viewName === "arena") loadActivities();
    else if (viewName === "leaderboard") loadLeaderboards();
    else if (viewName === "profile") loadUserProfile(window.activeUserId);
    else if (viewName === "shop") loadShopView();
    else if (viewName === "faculty") loadFacultyAdmin();
}

function loadQuestsView() {
    fetch("/api/quests")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            renderRaidBanner(data.team_raid);
            renderQuestsList(data.quests);
        });
}

function renderRaidBanner(raid) {
    const banner = document.getElementById("raid-boss-container");
    if (!raid) {
        banner.style.display = "none";
        return;
    }
    banner.style.display = "flex";
    const hpPercent = Math.round((raid.current_hp / raid.total_hp) * 100);
    document.getElementById("raid-boss-title").innerText = `🐉 ${raid.boss_name}`;
    document.getElementById("raid-boss-cohort").innerText = `${raid.batch_cohort} Cooperative Raid`;
    document.getElementById("raid-boss-hp-fill").style.width = `${hpPercent}%`;
    document.getElementById("raid-boss-hp-text").innerText = `HP: ${raid.current_hp.toLocaleString()} / ${raid.total_hp.toLocaleString()} (${hpPercent}%)`;
}

function renderQuestsList(quests) {
    const container = document.getElementById("quests-list-container");
    let html = "";
    
    quests.forEach(q => {
        const canClaim = q.is_completed && !q.claimed;
        html += `
            <div class="glass-card quest-card ${canClaim ? 'highlight' : ''}">
                <div class="quest-header">
                    <div>
                        <div class="quest-title">${q.title}</div>
                        <div class="quest-desc">${q.description}</div>
                    </div>
                    <span class="badge-tag" style="text-transform: capitalize;">${q.quest_type}</span>
                </div>
                
                <div class="xp-bar-container">
                    <div class="xp-bar-bg" style="height: 8px;">
                        <div class="xp-bar-fill" style="width: ${q.progress_percent}%; background: ${q.is_completed ? 'var(--accent-emerald)' : 'var(--primary)'};"></div>
                    </div>
                    <div class="xp-bar-text">
                        <span>Progress: ${q.current_progress} / ${q.target_count}</span>
                        <span>${q.progress_percent}%</span>
                    </div>
                </div>

                <div class="quest-footer">
                    <div class="quest-rewards">
                        <span class="reward-badge xp">+${q.xp_reward} XP</span>
                        <span class="reward-badge gold">+${q.gold_reward} Gold</span>
                        ${q.gem_reward > 0 ? `<span class="reward-badge gem">+${q.gem_reward} Gems</span>` : ''}
                    </div>
                    ${canClaim ? `
                        <button class="btn-claim" onclick="claimQuest(${q.id})">Claim Loot ⭐</button>
                    ` : (q.claimed ? `
                        <span style="color: var(--text-dim); font-size: 0.8rem; font-weight: bold;">✔ Claimed</span>
                    ` : `
                        <span style="color: var(--text-muted); font-size: 0.8rem;">In Progress</span>
                    `)}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function claimQuest(questId) {
    window.sound.playCoin();
    fetch(`/api/quests/${questId}/claim`, { method: "POST" })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                showToast(res.message, "success");
                triggerConfetti();
                refreshUserHUD();
                loadQuestsView();
            } else {
                showToast(res.message, "error");
            }
        });
}

function loadActivities() {
    fetch("/api/activities")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            renderActivitiesGrid(data.activities);
        });
}

function renderActivitiesGrid(activities) {
    const container = document.getElementById("activities-grid");
    let html = "";

    activities.forEach(act => {
        const icon = act.category === "quiz" ? "📜" : (act.category === "code_quest" ? "💻" : "🔍");
        html += `
            <div class="glass-card activity-card" onclick="openActivity('${act.category}', ${act.id})">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span class="activity-topic">${icon} ${act.topic}</span>
                        <span class="difficulty-pill ${act.difficulty}">${act.difficulty}</span>
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 0.4rem;">${act.title}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">${act.description}</div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 0.75rem; margin-top: 0.5rem;">
                    <div style="display: flex; gap: 0.4rem;">
                        <span class="reward-badge xp">+${act.base_xp} XP</span>
                        <span class="reward-badge gold">+${act.base_gold} Gold</span>
                    </div>
                    <div>
                        ${act.is_completed ? `<span style="color: var(--accent-emerald); font-size: 0.8rem; font-weight: bold;">✔ Done (${act.best_score}%)</span>` : `<button class="btn-primary" style="padding: 0.35rem 0.8rem; font-size: 0.78rem;">Launch ⚔️</button>`}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function openActivity(category, id) {
    if (category === "quiz") openQuizRunner(id);
    else if (category === "code_quest") openCodeQuestRunner(id);
    else if (category === "bug_hunt") openQuizRunner(id); // Shares quiz format
}

function loadShopView() {
    fetch("/api/shop")
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            renderShopGrid(data.items);
        });
}

function renderShopGrid(items) {
    const container = document.getElementById("shop-grid");
    let html = "";

    items.forEach(item => {
        html += `
            <div class="glass-card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                        <span style="font-size: 2rem;">💎</span>
                        <span class="badge-tag" style="background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); border-color: rgba(245, 158, 11, 0.3);">${item.rarity}</span>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem;">${item.title}</div>
                    <div style="font-size: 0.82rem; color: var(--text-muted);">${item.description}</div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 0.75rem; margin-top: 1rem;">
                    <div style="font-weight: 800; color: var(--accent-gold); font-size: 0.95rem;">
                        🪙 ${item.cost_gold} Gold
                    </div>
                    <div>
                        ${item.is_owned ? (item.is_equipped ? `
                            <span style="color: var(--accent-emerald); font-weight: bold; font-size: 0.8rem;">Equipped</span>
                        ` : `
                            <button class="btn-secondary" style="padding: 0.35rem 0.8rem; font-size: 0.78rem;" onclick="equipItem(${item.id})">Equip</button>
                        `) : `
                            <button class="btn-primary" style="padding: 0.35rem 0.8rem; font-size: 0.78rem;" onclick="buyItem(${item.id})">Unlock</button>
                        `}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function buyItem(itemId) {
    window.sound.playCoin();
    fetch("/api/shop/buy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) {
            showToast(res.message, "success");
            refreshUserHUD();
            loadShopView();
        } else {
            showToast(res.message, "error");
            window.sound.playError();
        }
    });
}

function equipItem(itemId) {
    window.sound.playClick();
    fetch("/api/shop/equip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) {
            showToast(res.message, "success");
            refreshUserHUD();
            loadShopView();
        }
    });
}

function showRewardCelebrationModal(res) {
    const modal = document.getElementById("reward-modal");
    if (!modal) return;

    if (res.leveled_up) {
        window.sound.playLevelUp();
        triggerConfetti();
        document.getElementById("reward-modal-title").innerText = `🎉 LEVEL UP! Reached Level ${res.new_level}!`;
    } else if (res.flagged_abuse) {
        window.sound.playError();
        document.getElementById("reward-modal-title").innerText = `⚠️ Anti-Farming Security Notice`;
    } else {
        window.sound.playSuccess();
        triggerConfetti();
        document.getElementById("reward-modal-title").innerText = `⚔️ Quest Completed!`;
    }

    let html = `
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: center; gap: 1.5rem; margin: 1rem 0;">
                <div style="background: rgba(0, 242, 254, 0.1); border: 1px solid var(--primary); padding: 1rem 1.5rem; border-radius: var(--radius-md);">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">XP Earned</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: var(--primary);">+${res.final_xp} XP</div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid var(--accent-gold); padding: 1rem 1.5rem; border-radius: var(--radius-md);">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Gold Earned</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: var(--accent-gold);">+${res.final_gold} Gold</div>
                </div>
            </div>

            <div style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem;">
                ${res.anti_farming_info?.message || ''}
            </div>

            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.75rem; text-align: left; font-size: 0.8rem;">
                <div>Accuracy Score: <strong>${res.score_percent}%</strong></div>
                <div>Streak Multiplier: <strong>${res.streak_multiplier}x (${res.streak_days} days active)</strong></div>
                <div>Diminishing Multiplier: <strong>${res.diminishing_multiplier}x</strong></div>
                ${res.reflection_bonus ? `<div style="color: var(--accent-emerald);">💡 Thoughtful Reflection Bonus Applied (+30 XP)</div>` : ''}
            </div>
    `;

    if (res.unlocked_badges && res.unlocked_badges.length > 0) {
        html += `<div style="margin-top: 1rem; color: var(--accent-gold); font-weight: bold;">🎖️ Unlocked Badges:</div>`;
        res.unlocked_badges.forEach(b => {
            html += `<div style="font-size: 0.85rem; color: #fff;">⭐ <strong>${b.name}</strong> (${b.tier})</div>`;
        });
    }

    html += `</div>`;
    document.getElementById("reward-modal-body").innerHTML = html;
    modal.classList.add("active");
}

function closeRewardModal() {
    document.getElementById("reward-modal").classList.remove("active");
}

function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "✔" : (type === "warning" ? "⚠️" : "✖");
    toast.innerHTML = `<span style="font-weight: bold;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

/* Confetti Particle System */
let confettiParticles = [];
function setupConfettiCanvas() {
    const canvas = document.getElementById("confetti-canvas");
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    window.addEventListener("resize", () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

function triggerConfetti() {
    const canvas = document.getElementById("confetti-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const colors = ["#00f2fe", "#7928ca", "#f59e0b", "#10b981", "#f43f5e"];
    
    confettiParticles = [];
    for (let i = 0; i < 80; i++) {
        confettiParticles.push({
            x: window.innerWidth / 2,
            y: window.innerHeight / 2,
            vx: (Math.random() - 0.5) * 12,
            vy: (Math.random() - 0.8) * 12,
            size: Math.random() * 8 + 4,
            color: colors[Math.floor(Math.random() * colors.length)],
            alpha: 1.0,
            decay: Math.random() * 0.02 + 0.015
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let active = false;
        confettiParticles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.25; // gravity
            p.alpha -= p.decay;
            if (p.alpha > 0) {
                active = true;
                ctx.globalAlpha = p.alpha;
                ctx.fillStyle = p.color;
                ctx.fillRect(p.x, p.y, p.size, p.size);
            }
        });
        if (active) requestAnimationFrame(animate);
        else ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    animate();
}

window.showToast = showToast;
window.refreshUserHUD = refreshUserHUD;
window.loadActivities = loadActivities;
window.navigateToView = navigateToView;
window.showRewardCelebrationModal = showRewardCelebrationModal;
