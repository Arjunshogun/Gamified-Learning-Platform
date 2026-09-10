"""
gamification_engine.py - Core Gamification, Progression, Anti-Farming & Rewards Logic for QuestAcademy
Implements mathematical progression models, anti-abuse heuristics, and badge evaluation.
"""

import math
import json
from datetime import datetime, timezone, timedelta
import sqlite3

def get_config_val(conn, key, default_val):
    """Retrieves a configuration value from scoring_config or returns default."""
    cursor = conn.cursor()
    cursor.execute("SELECT config_value FROM scoring_config WHERE config_key = ?", (key,))
    row = cursor.fetchone()
    if row:
        val = row["config_value"]
        try:
            if "." in val:
                return float(val)
            return int(val)
        except ValueError:
            return val
    return default_val

# -------------------------------------------------------------
# 1. Level & XP Progression Curve
# -------------------------------------------------------------

def calculate_level(xp: int) -> int:
    """Calculates user level based on quadratic scaling curve: Level = floor(sqrt(XP / 100)) + 1."""
    if xp <= 0:
        return 1
    return int(math.floor(math.sqrt(xp / 100.0))) + 1

def xp_for_level_start(level: int) -> int:
    """Returns minimum XP required to reach a given level."""
    if level <= 1:
        return 0
    return (level - 1) ** 2 * 100

def xp_for_next_level(level: int) -> int:
    """Returns XP threshold for the next level."""
    return level ** 2 * 100

def get_level_progress(xp: int):
    """
    Returns level details, current level base XP, next level target XP,
    and percentage progress through the current level.
    """
    level = calculate_level(xp)
    start_xp = xp_for_level_start(level)
    target_xp = xp_for_next_level(level)
    current_in_level = xp - start_xp
    span = target_xp - start_xp
    percent = min(100.0, max(0.0, (current_in_level / span) * 100.0))
    
    tier_title = get_tier_title(level)
    
    return {
        "level": level,
        "current_xp": xp,
        "level_start_xp": start_xp,
        "next_level_xp": target_xp,
        "xp_needed": target_xp - xp,
        "progress_percent": round(percent, 1),
        "tier_title": tier_title
    }

def get_tier_title(level: int) -> str:
    """Returns rank tier title based on level."""
    if level < 3:
        return "Novice Scholar"
    elif level < 5:
        return "Apprentice Coder"
    elif level < 7:
        return "Adept Engineer"
    elif level < 9:
        return "Master Architect"
    else:
        return "Grandmaster Titan"

# -------------------------------------------------------------
# 2. Streak Engine & Freeze Protection
# -------------------------------------------------------------

def update_streak(user_id: int, conn: sqlite3.Connection):
    """
    Evaluates and updates user's daily learning streak.
    Supports automatic streak freeze usage if a day was missed.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT current_streak, max_streak, last_activity_date, streak_freezes_left FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return {"current_streak": 1, "streak_changed": False, "freeze_used": False}

    current_streak = user["current_streak"]
    max_streak = user["max_streak"]
    last_act = user["last_activity_date"]
    freezes = user["streak_freezes_left"]
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    day_before = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    
    streak_changed = False
    freeze_used = False

    if not last_act:
        current_streak = 1
        streak_changed = True
    elif last_act == today:
        # Already active today, streak intact
        pass
    elif last_act == yesterday:
        # Consecutive day activity!
        current_streak += 1
        streak_changed = True
    elif last_act == day_before and freezes > 0:
        # Missed yesterday, but auto-freeze saved the streak!
        freezes -= 1
        current_streak += 1
        freeze_used = True
        streak_changed = True
    else:
        # Streak broken
        current_streak = 1
        streak_changed = True

    if current_streak > max_streak:
        max_streak = current_streak

    cursor.execute("""
    UPDATE users 
    SET current_streak = ?, max_streak = ?, last_activity_date = ?, streak_freezes_left = ?
    WHERE id = ?
    """, (current_streak, max_streak, today, freezes, user_id))
    
    conn.commit()
    
    return {
        "current_streak": current_streak,
        "max_streak": max_streak,
        "streak_changed": streak_changed,
        "freeze_used": freeze_used,
        "freezes_left": freezes
    }

def get_streak_multiplier(streak: int, conn: sqlite3.Connection) -> float:
    """Calculates streak reward multiplier: 1.0 + min(streak * step, max_multiplier - 1.0)."""
    step = get_config_val(conn, "streak_multiplier_step", 0.05)
    max_mult = get_config_val(conn, "max_streak_multiplier", 1.50)
    bonus = min((streak - 1) * step if streak > 1 else 0.0, max_mult - 1.0)
    return round(1.0 + bonus, 2)

# -------------------------------------------------------------
# 3. Anti-Farming & Abuse Prevention Engine
# -------------------------------------------------------------

def evaluate_anti_farming(user_id: int, activity_id: int, duration_seconds: int, hints_used: int, conn: sqlite3.Connection):
    """
    Comprehensive anti-farming and abuse detection heuristics:
    1. Speed Run Abuse: checks if completion was unrealistically fast.
    2. Cooldown Violation: checks if retried too soon after prior attempt.
    3. Diminishing Returns: reduces rewards across repeat attempts of the same task.
    4. Daily XP Hard Cap: enforces daily ceiling on repetitive tasks.
    """
    cursor = conn.cursor()
    
    # Fetch activity metadata
    cursor.execute("SELECT category, min_duration_seconds, base_xp, base_gold FROM activities WHERE id = ?", (activity_id,))
    act = cursor.fetchone()
    if not act:
        return {"allowed": False, "diminishing_mult": 0.0, "flagged": True, "reason": "Activity Not Found"}

    min_threshold = act["min_duration_seconds"]
    category = act["category"]
    
    # 1. Speed Run Check
    if duration_seconds < min_threshold:
        details = f"Completed {category} in {duration_seconds}s (minimum human threshold is {min_threshold}s)."
        cursor.execute("""
        INSERT INTO anti_farming_audit_logs (user_id, activity_id, violation_type, detected_details, penalty_applied, status)
        VALUES (?, ?, 'SPEED_RUN_ABUSE', ?, 'Rewards set to 0 XP / 0 Gold. Warning logged.', 'flagged')
        """, (user_id, activity_id, details))
        conn.commit()
        return {
            "allowed": True,
            "flagged": True,
            "violation_type": "SPEED_RUN_ABUSE",
            "penalty_multiplier": 0.0,
            "diminishing_mult": 0.0,
            "message": f"⚠️ Anti-Farming Triggered: Completion time ({duration_seconds}s) was faster than human minimum threshold ({min_threshold}s). No XP or Gold awarded for this attempt.",
            "audit_logged": True
        }

    # 2. Cooldown Check (only if retried within cooldown_limit seconds of prior attempt)
    cooldown_limit = get_config_val(conn, "cooldown_seconds_retry", 20)
    cursor.execute("""
    SELECT completed_at FROM user_activity_logs 
    WHERE user_id = ? AND activity_id = ?
    ORDER BY id DESC LIMIT 1
    """, (user_id, activity_id))
    last_log = cursor.fetchone()
    if last_log and last_log["completed_at"]:
        try:
            last_time = datetime.strptime(last_log["completed_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            now_time = datetime.now(timezone.utc)
            elapsed = (now_time - last_time).total_seconds()
            if 0 < elapsed < cooldown_limit:
                details = f"Retried task within {int(elapsed)}s of previous completion (minimum cooldown is {cooldown_limit}s)."
                cursor.execute("""
                INSERT INTO anti_farming_audit_logs (user_id, activity_id, violation_type, detected_details, penalty_applied, status)
                VALUES (?, ?, 'COOLDOWN_VIOLATION', ?, 'Cooldown penalty applied. No rewards.', 'flagged')
                """, (user_id, activity_id, details))
                conn.commit()
                return {
                    "allowed": True,
                    "flagged": True,
                    "violation_type": "COOLDOWN_VIOLATION",
                    "penalty_multiplier": 0.0,
                    "diminishing_mult": 0.0,
                    "message": f"⏳ Cooldown Active: You completed this task {int(elapsed)}s ago. Please wait at least {cooldown_limit}s between retries.",
                    "audit_logged": True
                }
        except Exception:
            pass

    # 3. Diminishing Returns on Repetition
    cursor.execute("""
    SELECT COUNT(*) as attempt_count FROM user_activity_logs
    WHERE user_id = ? AND activity_id = ? AND flagged_abuse = 0
    """, (user_id, activity_id))
    past_attempts = cursor.fetchone()["attempt_count"]
    
    mult_attempt_2 = get_config_val(conn, "diminishing_attempt_2", 0.50)
    mult_attempt_3 = get_config_val(conn, "diminishing_attempt_3", 0.20)
    mult_attempt_4 = get_config_val(conn, "diminishing_attempt_4_plus", 0.00)

    if past_attempts == 0:
        diminishing_mult = 1.0
        attempt_note = "1st Completion (100% Rewards)"
    elif past_attempts == 1:
        diminishing_mult = mult_attempt_2
        attempt_note = f"2nd Completion (Diminishing Return: {int(mult_attempt_2*100)}% Rewards)"
    elif past_attempts == 2:
        diminishing_mult = mult_attempt_3
        attempt_note = f"3rd Completion (Diminishing Return: {int(mult_attempt_3*100)}% Rewards)"
    else:
        diminishing_mult = mult_attempt_4
        attempt_note = "4th+ Completion (Practice Mode: 0 XP/Gold, only skill mastery counts)"

    # 4. Daily Hard Cap Check
    today_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT COALESCE(SUM(final_xp), 0) as today_xp FROM user_activity_logs
    WHERE user_id = ? AND completed_at LIKE ?
    """, (user_id, f"{today_prefix}%"))
    today_xp = cursor.fetchone()["today_xp"]
    daily_cap = get_config_val(conn, "daily_xp_hard_cap", 1500)
    
    is_daily_capped = today_xp >= daily_cap
    daily_cap_remaining = max(0, daily_cap - today_xp)

    return {
        "allowed": True,
        "flagged": False,
        "violation_type": None,
        "penalty_multiplier": 1.0,
        "diminishing_mult": diminishing_mult,
        "past_attempts": past_attempts,
        "attempt_note": attempt_note,
        "today_xp": today_xp,
        "daily_cap": daily_cap,
        "daily_cap_remaining": daily_cap_remaining,
        "is_daily_capped": is_daily_capped,
        "message": attempt_note
    }

# -------------------------------------------------------------
# 4. Reward Calculation Engine
# -------------------------------------------------------------

def calculate_activity_rewards(
    user_id: int,
    activity_id: int,
    score_percent: float,
    duration_seconds: int,
    hints_used: int = 0,
    reflection_text: str = "",
    conn: sqlite3.Connection = None
):
    """
    Computes transparent XP, Gold rewards, and applies effort bonuses & anti-farming checks.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    activity = cursor.fetchone()
    if not activity:
        return None

    # 1. Update streak first
    streak_info = update_streak(user_id, conn)
    current_streak = streak_info["current_streak"]
    streak_mult = get_streak_multiplier(current_streak, conn)

    # 2. Run anti-farming heuristics
    anti_farm = evaluate_anti_farming(user_id, activity_id, duration_seconds, hints_used, conn)
    
    base_xp = activity["base_xp"]
    base_gold = activity["base_gold"]
    
    # 3. Accuracy scaling
    accuracy_factor = max(0.0, min(1.0, score_percent / 100.0))
    raw_xp = int(base_xp * accuracy_factor)
    raw_gold = int(base_gold * accuracy_factor)
    
    # 4. Effort Bonuses
    first_try_bonus_mult = 1.0
    if anti_farm.get("past_attempts", 0) == 0 and score_percent >= 99.0:
        first_try_bonus_mult = get_config_val(conn, "first_try_multiplier", 1.25)

    zero_hints_gold_bonus = 0
    if hints_used == 0 and score_percent >= 80.0:
        zero_hints_gold_bonus = get_config_val(conn, "zero_hints_bonus_gold", 20)

    reflection_xp_bonus = 0
    if reflection_text and len(reflection_text.strip()) >= 15:
        reflection_xp_bonus = 30 # Thoughtful reflection rewarded!

    # 5. Combine multipliers
    if anti_farm.get("flagged", False):
        final_xp = 0
        final_gold = 0
        flagged_abuse = 1
        abuse_reason = anti_farm.get("violation_type", "ANTI_FARMING_TRIGGER")
    else:
        dim_mult = anti_farm["diminishing_mult"]
        calculated_xp = int((raw_xp * first_try_bonus_mult * streak_mult + reflection_xp_bonus) * dim_mult)
        calculated_gold = int((raw_gold * streak_mult + zero_hints_gold_bonus) * dim_mult)
        
        # Enforce daily cap if applicable
        if anti_farm["is_daily_capped"]:
            final_xp = 0
            final_gold = 0
            abuse_reason = "DAILY_HARD_CAP_REACHED"
        else:
            final_xp = min(calculated_xp, anti_farm["daily_cap_remaining"])
            final_gold = calculated_gold
            abuse_reason = None
        
        flagged_abuse = 0

    # 6. Record Activity Log in Database
    cursor.execute("SELECT COUNT(*) FROM user_activity_logs WHERE user_id = ? AND activity_id = ?", (user_id, activity_id))
    attempt_num = cursor.fetchone()[0] + 1
    
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO user_activity_logs (
        user_id, activity_id, attempt_number, duration_seconds, score_percent,
        raw_xp, raw_gold, streak_multiplier, diminishing_multiplier, anti_farming_penalty,
        final_xp, final_gold, hints_used, reflection_text, flagged_abuse, abuse_reason, completed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, activity_id, attempt_num, duration_seconds, score_percent,
        raw_xp, raw_gold, streak_mult, anti_farm.get("diminishing_mult", 1.0),
        1.0 if flagged_abuse else 0.0, final_xp, final_gold, hints_used,
        reflection_text, flagged_abuse, abuse_reason, now_str
    ))

    # 7. Update User XP, Gold, Level
    cursor.execute("SELECT xp, gold, level FROM users WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    old_xp = u["xp"]
    old_level = u["level"]
    new_xp = old_xp + final_xp
    new_gold = u["gold"] + final_gold
    new_level = calculate_level(new_xp)
    leveled_up = new_level > old_level

    cursor.execute("""
    UPDATE users 
    SET xp = ?, gold = ?, level = ?
    WHERE id = ?
    """, (new_xp, new_gold, new_level, user_id))
    
    conn.commit()

    # 8. Check Badges and Quests
    unlocked_badges = check_and_unlock_badges(user_id, conn)
    completed_quests = update_quest_progress(user_id, activity["category"], final_xp, hints_used, conn)
    
    # 9. Update Team Raid Boss HP if in CS-Alpha
    update_team_raid(user_id, final_xp, conn)

    level_info = get_level_progress(new_xp)

    return {
        "success": True,
        "activity_title": activity["title"],
        "category": activity["category"],
        "score_percent": score_percent,
        "duration_seconds": duration_seconds,
        "raw_xp": raw_xp,
        "raw_gold": raw_gold,
        "streak_multiplier": streak_mult,
        "streak_days": current_streak,
        "first_try_bonus": first_try_bonus_mult > 1.0,
        "zero_hints_bonus": zero_hints_gold_bonus > 0,
        "reflection_bonus": reflection_xp_bonus > 0,
        "diminishing_multiplier": anti_farm.get("diminishing_mult", 1.0),
        "final_xp": final_xp,
        "final_gold": final_gold,
        "old_xp": old_xp,
        "new_xp": new_xp,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": leveled_up,
        "level_info": level_info,
        "anti_farming_info": anti_farm,
        "flagged_abuse": bool(flagged_abuse),
        "abuse_reason": abuse_reason,
        "unlocked_badges": unlocked_badges,
        "completed_quests": completed_quests,
        "streak_info": streak_info
    }

# -------------------------------------------------------------
# 5. Badge Unlocking Engine
# -------------------------------------------------------------

def check_and_unlock_badges(user_id: int, conn: sqlite3.Connection):
    """
    Evaluates milestone requirements and awards badges automatically.
    Returns list of newly unlocked badge dictionaries.
    """
    cursor = conn.cursor()
    
    # Fetch already unlocked badge IDs
    cursor.execute("SELECT badge_id FROM user_badges WHERE user_id = ?", (user_id,))
    unlocked_ids = set([row["badge_id"] for row in cursor.fetchall()])

    # Fetch user stats
    cursor.execute("SELECT current_streak, max_streak, xp, level FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    cursor.execute("""
    SELECT 
        COUNT(*) as total_activities,
        SUM(CASE WHEN a.category = 'quiz' AND l.score_percent >= 80 THEN 1 ELSE 0 END) as passed_quizzes,
        SUM(CASE WHEN a.category = 'code_quest' AND l.score_percent >= 90 THEN 1 ELSE 0 END) as passed_code,
        SUM(CASE WHEN a.category = 'bug_hunt' AND l.score_percent >= 90 THEN 1 ELSE 0 END) as passed_bugs,
        SUM(CASE WHEN l.score_percent = 100.0 THEN 1 ELSE 0 END) as flawless_count,
        SUM(CASE WHEN l.flagged_abuse = 0 THEN 1 ELSE 0 END) as clean_count
    FROM user_activity_logs l
    JOIN activities a ON l.activity_id = a.id
    WHERE l.user_id = ?
    """, (user_id,))
    stats = cursor.fetchone()

    total_activities = stats["total_activities"] or 0
    passed_quizzes = stats["passed_quizzes"] or 0
    passed_code = stats["passed_code"] or 0
    passed_bugs = stats["passed_bugs"] or 0
    flawless_count = stats["flawless_count"] or 0
    clean_count = stats["clean_count"] or 0
    max_streak = max(user["current_streak"], user["max_streak"])

    # Fetch all badges
    cursor.execute("SELECT * FROM badges")
    all_badges = cursor.fetchall()

    newly_unlocked = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for b in all_badges:
        b_id = b["id"]
        if b_id in unlocked_ids:
            continue

        req_type = b["requirement_type"]
        threshold = b["requirement_threshold"]
        should_unlock = False

        if req_type == "first_blood" and total_activities >= 1:
            should_unlock = True
        elif req_type == "streak" and max_streak >= threshold:
            should_unlock = True
        elif req_type == "quizzes_completed" and passed_quizzes >= threshold:
            should_unlock = True
        elif req_type == "code_solved" and passed_code >= threshold:
            should_unlock = True
        elif req_type == "bug_hunt" and passed_bugs >= threshold:
            should_unlock = True
        elif req_type == "flawless_score" and flawless_count >= threshold:
            should_unlock = True
        elif req_type == "clean_record" and clean_count >= threshold:
            should_unlock = True

        if should_unlock:
            cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id, unlocked_at) VALUES (?, ?, ?)", (user_id, b_id, now_str))
            
            # Award badge XP and Gold
            cursor.execute("UPDATE users SET xp = xp + ?, gold = gold + ? WHERE id = ?", (b["xp_reward"], b["gold_reward"], user_id))
            
            newly_unlocked.append({
                "id": b["id"],
                "slug": b["slug"],
                "name": b["name"],
                "description": b["description"],
                "icon": b["icon"],
                "tier": b["tier"],
                "xp_reward": b["xp_reward"],
                "gold_reward": b["gold_reward"]
            })

    conn.commit()
    return newly_unlocked

# -------------------------------------------------------------
# 6. Quest & Daily/Weekly Challenge Progress Engine
# -------------------------------------------------------------

def update_quest_progress(user_id: int, activity_category: str, xp_earned: int, hints_used: int, conn: sqlite3.Connection):
    """
    Updates active daily, weekly, and milestone quest counters.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quests WHERE is_active = 1")
    active_quests = cursor.fetchall()
    
    completed_quests = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for q in active_quests:
        q_id = q["id"]
        criteria = q["criteria_type"]
        target = q["target_count"]

        # Fetch existing progress
        cursor.execute("SELECT * FROM user_quest_progress WHERE user_id = ? AND quest_id = ?", (user_id, q_id))
        prog = cursor.fetchone()
        
        current_progress = prog["current_progress"] if prog else 0
        is_completed = prog["is_completed"] if prog else 0
        claimed = prog["claimed"] if prog else 0

        if is_completed:
            continue

        increment = 0
        if criteria == "complete_any_activity":
            increment = 1
        elif criteria == "solve_code_quest" and activity_category == "code_quest":
            increment = 1
        elif criteria == "maintain_streak":
            increment = 1
        elif criteria == "earn_xp":
            increment = xp_earned
        elif criteria == "zero_hints_challenge" and hints_used == 0:
            increment = 1

        if increment > 0:
            new_prog = current_progress + increment
            just_completed = new_prog >= target
            
            cursor.execute("""
            INSERT INTO user_quest_progress (user_id, quest_id, current_progress, is_completed, claimed, completed_at)
            VALUES (?, ?, ?, ?, 0, ?)
            ON CONFLICT(user_id, quest_id) DO UPDATE SET
                current_progress = ?,
                is_completed = ?,
                completed_at = CASE WHEN ? = 1 AND is_completed = 0 THEN ? ELSE completed_at END
            """, (user_id, q_id, new_prog, 1 if just_completed else 0, now_str if just_completed else None,
                  new_prog, 1 if just_completed else 0, 1 if just_completed else 0, now_str))

            if just_completed:
                completed_quests.append({
                    "id": q["id"],
                    "title": q["title"],
                    "description": q["description"],
                    "quest_type": q["quest_type"],
                    "xp_reward": q["xp_reward"],
                    "gold_reward": q["gold_reward"],
                    "gem_reward": q["gem_reward"]
                })

    conn.commit()
    return completed_quests

# -------------------------------------------------------------
# 7. Team Raid Boss Damage Engine
# -------------------------------------------------------------

def update_team_raid(user_id: int, xp_earned: int, conn: sqlite3.Connection):
    """Inflicts collaborative damage to active Team Raid Boss."""
    cursor = conn.cursor()
    cursor.execute("SELECT batch_cohort FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return
    cohort = user["batch_cohort"]

    cursor.execute("SELECT * FROM team_raids WHERE batch_cohort = ? AND is_defeated = 0 LIMIT 1", (cohort,))
    raid = cursor.fetchone()
    if raid:
        damage = max(10, int(xp_earned * 0.8))
        new_hp = max(0, raid["current_hp"] - damage)
        is_defeated = 1 if new_hp == 0 else 0
        cursor.execute("UPDATE team_raids SET current_hp = ?, is_defeated = ? WHERE id = ?", (new_hp, is_defeated, raid["id"]))
        conn.commit()
