/**
 * profile.js - Student Progress Profile, 5-Axis Radar Matrix, Activity Heatmap & Badges
 */

function loadUserProfile(userId) {
    const targetId = userId || window.activeUserId || 1;
    fetch(`/api/profile/${targetId}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success) return;
            renderProfileDetails(data);
            drawSkillRadar(data.skill_radar);
            renderHeatmap(data.heatmap);
            renderBadgesGrid(data.badges);
            renderInventory(data.inventory);
        });
}

function renderProfileDetails(data) {
    const u = data.user;
    const lvl = data.level_info;

    document.getElementById("profile-name").innerText = u.full_name;
    document.getElementById("profile-role-batch").innerText = `${u.batch_cohort} • Level ${u.level} ${lvl.tier_title}`;
    document.getElementById("profile-title-display").innerText = u.equipped_title || 'Novice Scholar';
    
    document.getElementById("profile-stat-xp").innerText = `${u.xp.toLocaleString()} XP`;
    document.getElementById("profile-stat-gold").innerText = `${u.gold.toLocaleString()} Gold`;
    document.getElementById("profile-stat-streak").innerText = `🔥 ${u.current_streak}d (Best: ${u.max_streak}d)`;
    document.getElementById("profile-stat-freezes").innerText = `🛡️ ${u.streak_freezes_left} Available`;

    // Avatar Frame
    const avatarWrapper = document.getElementById("profile-avatar-large");
    avatarWrapper.className = `avatar-wrapper ${u.equipped_frame || ''}`;
    avatarWrapper.style.width = "64px";
    avatarWrapper.style.height = "64px";
    avatarWrapper.style.fontSize = "2.2rem";
}

function drawSkillRadar(skills) {
    const canvas = document.getElementById("radar-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const radius = 100;

    ctx.clearRect(0, 0, w, h);

    const labels = ["Algorithms", "Data Structures", "Web Systems", "Problem Solving", "Consistency"];
    const values = labels.map(l => (skills[l] || 50) / 100.0);
    const numAxes = labels.length;

    // 1. Draw Web concentric polygons
    ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
    ctx.lineWidth = 1;
    for (let level = 1; level <= 4; level++) {
        const r = (radius / 4) * level;
        ctx.beginPath();
        for (let i = 0; i < numAxes; i++) {
            const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
            const x = cx + Math.cos(angle) * r;
            const y = cy + Math.sin(angle) * r;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
    }

    // 2. Draw Axes lines & Labels
    ctx.font = "11px Outfit, sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    for (let i = 0; i < numAxes; i++) {
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(x, y);
        ctx.stroke();

        // Label offset
        const lx = cx + Math.cos(angle) * (radius + 22);
        const ly = cy + Math.sin(angle) * (radius + 18);
        ctx.fillText(`${labels[i]} (${skills[labels[i]] || 50}%)`, lx, ly);
    }

    // 3. Draw Skill Data Polygon
    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const r = radius * values[i];
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(0, 242, 254, 0.25)";
    ctx.fill();
    ctx.strokeStyle = "#00f2fe";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Data points
    for (let i = 0; i < numAxes; i++) {
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const r = radius * values[i];
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#00f2fe";
        ctx.fill();
    }
}

function renderHeatmap(heatmapData) {
    const container = document.getElementById("profile-heatmap-container");
    container.innerHTML = "";
    
    const now = new Date();
    // Generate 60 days of activity cells
    for (let i = 59; i >= 0; i--) {
        const d = new Date();
        d.setDate(now.getDate() - i);
        const dateKey = d.toISOString().split("T")[0];
        const log = heatmapData[dateKey];
        const count = log ? log.count : 0;
        
        let level = "0";
        if (count >= 3) level = "3";
        else if (count === 2) level = "2";
        else if (count === 1) level = "1";

        const cell = document.createElement("div");
        cell.className = "heatmap-cell";
        cell.setAttribute("data-level", level);
        cell.title = `${dateKey}: ${count} activities completed (${log ? log.xp : 0} XP)`;
        container.appendChild(cell);
    }
}

function renderBadgesGrid(badges) {
    const container = document.getElementById("profile-badges-grid");
    let html = "";
    
    const iconsMap = {
        "badge_sword": "⚔️",
        "badge_scroll": "📜",
        "badge_crown": "👑",
        "badge_code": "⚡",
        "badge_terminal": "💻",
        "badge_shield": "🛡️",
        "badge_flame_bronze": "🔥",
        "badge_flame_silver": "🔥",
        "badge_flame_mythic": "✨",
        "badge_star": "⭐",
        "badge_shield_gold": "🌟",
        "badge_boss": "🐉"
    };

    badges.forEach(b => {
        const isUnlocked = b.is_unlocked;
        const iconEmoji = iconsMap[b.icon] || "🎖️";
        
        html += `
            <div class="badge-card ${isUnlocked ? 'unlocked' : 'locked'} ${b.tier}">
                <div class="badge-icon">${iconEmoji}</div>
                <div style="font-weight: 700; font-size: 0.88rem; color: #fff; margin-bottom: 2px;">${b.name}</div>
                <div style="font-size: 0.68rem; font-weight: 800; text-transform: uppercase; color: var(--accent-gold); margin-bottom: 6px;">${b.tier} • ${b.category}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${b.description}</div>
                <div style="margin-top: 8px; font-size: 0.72rem; color: ${isUnlocked ? 'var(--accent-emerald)' : 'var(--text-dim)'}; font-weight: bold;">
                    ${isUnlocked ? `✔ Unlocked ${b.unlocked_at || ''}` : `🔒 Incomplete`}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderInventory(inventory) {
    const container = document.getElementById("profile-inventory-container");
    if (!inventory || inventory.length === 0) {
        container.innerHTML = "<div style='color: var(--text-muted); font-size: 0.85rem;'>No equipped cosmetics yet. Visit the Reward Shop to unlock items!</div>";
        return;
    }

    let html = "<div style='display: flex; gap: 1rem; flex-wrap: wrap;'>";
    inventory.forEach(item => {
        html += `
            <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.5rem;">💎</span>
                <div>
                    <div style="font-size: 0.88rem; font-weight: bold; color: #fff;">${item.title}</div>
                    <div style="font-size: 0.72rem; color: var(--primary);">${item.is_equipped ? 'Equipped Active' : 'In Inventory'}</div>
                </div>
            </div>
        `;
    });
    html += "</div>";
    container.innerHTML = html;
}
