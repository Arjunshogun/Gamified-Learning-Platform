"""
database.py - Database Schema and Seed Data Initialization for QuestAcademy
Provides SQLite relational database setup with rich pre-populated data.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "eduquest.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reset=False):
    """Initializes the database schema and seeds initial data if not present."""
    if force_reset and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'student', -- 'student', 'faculty', 'admin'
        avatar_url TEXT DEFAULT 'avatar_1',
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 100,
        gems INTEGER DEFAULT 5,
        current_streak INTEGER DEFAULT 1,
        max_streak INTEGER DEFAULT 1,
        last_activity_date TEXT,
        streak_freezes_left INTEGER DEFAULT 1,
        batch_cohort TEXT DEFAULT 'Batch CS-2026-Alpha',
        equipped_title TEXT DEFAULT 'Novice Scholar',
        equipped_frame TEXT DEFAULT 'frame_default',
        equipped_theme TEXT DEFAULT 'theme_cyber',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Activity Types & Config
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type_code TEXT UNIQUE NOT NULL, -- 'quiz', 'code_quest', 'bug_hunt', 'peer_review'
        base_xp INTEGER DEFAULT 100,
        base_gold INTEGER DEFAULT 25,
        min_seconds_threshold INTEGER DEFAULT 10,
        cooldown_seconds INTEGER DEFAULT 30,
        daily_cap_xp INTEGER DEFAULT 800,
        diminishing_decay REAL DEFAULT 0.5
    )
    """)

    # 3. Learning Activities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL, -- 'quiz', 'code_quest', 'bug_hunt'
        topic TEXT NOT NULL, -- 'Algorithms', 'Data Structures', 'Web Tech', 'Databases', 'Clean Code'
        difficulty TEXT DEFAULT 'Medium', -- 'Easy', 'Medium', 'Hard', 'Legendary'
        estimated_minutes INTEGER DEFAULT 5,
        base_xp INTEGER DEFAULT 150,
        base_gold INTEGER DEFAULT 40,
        min_duration_seconds INTEGER DEFAULT 15,
        content_json TEXT NOT NULL, -- JSON formatted questions / code prompts / bugs
        test_cases_json TEXT, -- JSON test cases for coding quests
        hints_json TEXT, -- JSON hints available
        is_active INTEGER DEFAULT 1
    )
    """)

    # 4. User Activity Logs & Anti-Farming Audit
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        attempt_number INTEGER DEFAULT 1,
        duration_seconds INTEGER NOT NULL,
        score_percent REAL DEFAULT 100.0,
        raw_xp INTEGER NOT NULL,
        raw_gold INTEGER NOT NULL,
        streak_multiplier REAL DEFAULT 1.0,
        diminishing_multiplier REAL DEFAULT 1.0,
        anti_farming_penalty REAL DEFAULT 0.0, -- 1.0 if fully penalized (0 yield)
        final_xp INTEGER NOT NULL,
        final_gold INTEGER NOT NULL,
        hints_used INTEGER DEFAULT 0,
        reflection_text TEXT,
        flagged_abuse INTEGER DEFAULT 0,
        abuse_reason TEXT,
        completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (activity_id) REFERENCES activities (id)
    )
    """)

    # 5. Badges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        tier TEXT DEFAULT 'Bronze', -- 'Bronze', 'Silver', 'Gold', 'Mythic'
        category TEXT DEFAULT 'General',
        requirement_type TEXT NOT NULL, -- 'streak', 'quizzes_completed', 'code_solved', 'flawless_score', 'first_blood', 'shop_purchases'
        requirement_threshold INTEGER DEFAULT 1,
        xp_reward INTEGER DEFAULT 100,
        gold_reward INTEGER DEFAULT 50
    )
    """)

    # 6. User Badges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        badge_id INTEGER NOT NULL,
        unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_showcased INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (badge_id) REFERENCES badges (id),
        UNIQUE(user_id, badge_id)
    )
    """)

    # 7. Quests & Challenges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        quest_type TEXT DEFAULT 'daily', -- 'daily', 'weekly', 'raid_boss', 'milestone'
        criteria_type TEXT NOT NULL, -- 'complete_any_activity', 'solve_code_quest', 'maintain_streak', 'earn_xp', 'zero_hints_challenge', 'team_xp_contribution'
        target_count INTEGER DEFAULT 1,
        xp_reward INTEGER DEFAULT 150,
        gold_reward INTEGER DEFAULT 60,
        gem_reward INTEGER DEFAULT 0,
        badge_id_reward INTEGER,
        is_active INTEGER DEFAULT 1,
        expires_at TEXT
    )
    """)

    # 8. User Quest Progress Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_quest_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quest_id INTEGER NOT NULL,
        current_progress INTEGER DEFAULT 0,
        is_completed INTEGER DEFAULT 0,
        claimed INTEGER DEFAULT 0,
        completed_at TEXT,
        claimed_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (quest_id) REFERENCES quests (id),
        UNIQUE(user_id, quest_id)
    )
    """)

    # 9. Rewards & Cosmetics Shop Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shop_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- 'frame', 'theme', 'perk', 'title'
        cost_gold INTEGER DEFAULT 100,
        cost_gems INTEGER DEFAULT 0,
        icon TEXT NOT NULL,
        description TEXT NOT NULL,
        rarity TEXT DEFAULT 'Rare', -- 'Common', 'Rare', 'Epic', 'Legendary'
        effect_data_json TEXT
    )
    """)

    # 10. User Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_equipped INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (item_id) REFERENCES shop_items (id),
        UNIQUE(user_id, item_id)
    )
    """)

    # 11. Faculty Dynamic Scoring & Anti-Abuse Config Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scoring_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key TEXT UNIQUE NOT NULL,
        config_value TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'general',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 12. Anti-Farming Security Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anti_farming_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_id INTEGER,
        violation_type TEXT NOT NULL, -- 'SPEED_RUN_ABUSE', 'REPETITIVE_FARMING', 'COOLDOWN_VIOLATION', 'DAILY_CAP_EXCEEDED'
        detected_details TEXT NOT NULL,
        penalty_applied TEXT NOT NULL,
        status TEXT DEFAULT 'flagged', -- 'flagged', 'pardoned', 'confirmed'
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 13. Team Raid Boss Global State
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS team_raids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        boss_name TEXT NOT NULL,
        boss_avatar TEXT NOT NULL,
        total_hp INTEGER DEFAULT 10000,
        current_hp INTEGER DEFAULT 4250,
        batch_cohort TEXT NOT NULL,
        reward_badge_id INTEGER,
        reward_gold INTEGER DEFAULT 500,
        reward_xp INTEGER DEFAULT 1000,
        ends_at TEXT,
        is_defeated INTEGER DEFAULT 0
    )
    """)

    conn.commit()

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    """Seeds rich demonstration data into the database."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Seed Scoring Configurations
    configs = [
        ("base_quiz_xp", "120", "Base XP granted for 100% quiz completion", "scoring"),
        ("base_quiz_gold", "30", "Base Gold currency granted for quiz completion", "scoring"),
        ("base_code_xp", "250", "Base XP granted for coding quest completion", "scoring"),
        ("base_code_gold", "65", "Base Gold currency granted for coding quest", "scoring"),
        ("base_bug_xp", "180", "Base XP for finding and explaining bugs", "scoring"),
        ("base_bug_gold", "45", "Base Gold for debugging lab completion", "scoring"),
        ("streak_multiplier_step", "0.05", "Streak bonus percentage per active day (e.g. 5% per day)", "streak"),
        ("max_streak_multiplier", "1.50", "Maximum streak multiplier cap (1.50 = +50% max)", "streak"),
        ("first_try_multiplier", "1.25", "Bonus multiplier for 100% accuracy on first attempt", "scoring"),
        ("zero_hints_bonus_gold", "20", "Extra gold bonus awarded when 0 hints are requested", "scoring"),
        ("diminishing_attempt_2", "0.50", "Reward multiplier for 2nd attempt on same activity", "anti_farming"),
        ("diminishing_attempt_3", "0.20", "Reward multiplier for 3rd attempt on same activity", "anti_farming"),
        ("diminishing_attempt_4_plus", "0.00", "Reward multiplier for 4th+ attempt (0 rewards)", "anti_farming"),
        ("min_seconds_per_quiz_q", "3", "Minimum realistic seconds per quiz question", "anti_farming"),
        ("min_seconds_per_code_q", "12", "Minimum realistic seconds per code challenge submission", "anti_farming"),
        ("daily_xp_hard_cap", "1500", "Hard cap on XP earnable per day from repetitive activities", "anti_farming"),
        ("cooldown_seconds_retry", "20", "Mandatory cooldown in seconds before retrying the same task", "anti_farming")
    ]
    cursor.executemany("INSERT INTO scoring_config (config_key, config_value, description, category) VALUES (?, ?, ?, ?)", configs)

    # 2. Seed Badges
    badges_data = [
        ("first_blood", "Initiate of the Forge", "Completed your very first learning quest on QuestAcademy.", "badge_sword", "Bronze", "Milestone", "first_blood", 1, 100, 30),
        ("quiz_adept", "Quiz Vanguard", "Successfully completed 5 knowledge duel quizzes.", "badge_scroll", "Bronze", "Quiz", "quizzes_completed", 5, 200, 50),
        ("quiz_grandmaster", "Omniscient Scholar", "Aced 15 knowledge duel quizzes with 90%+ score.", "badge_crown", "Gold", "Quiz", "quizzes_completed", 15, 600, 150),
        ("code_ninja", "Syntax Sorcerer", "Solved 5 algorithm code challenges in the Code Arena.", "badge_code", "Silver", "Coding", "code_solved", 5, 350, 80),
        ("code_titan", "Algorithm Titan", "Solved 12 advanced code challenges with zero hints.", "badge_terminal", "Mythic", "Coding", "code_solved", 12, 1000, 300),
        ("bug_hunter", "Cyber Exterminator", "Located and resolved 5 critical bugs in the Concept Labs.", "badge_shield", "Silver", "Debugging", "bug_hunt", 5, 300, 70),
        ("streak_3", "Spark of Discipline", "Maintained an unbroken 3-day active learning streak.", "badge_flame_bronze", "Bronze", "Streak", "streak", 3, 150, 40),
        ("streak_7", "Blazing Momentum", "Maintained an unbroken 7-day active learning streak.", "badge_flame_silver", "Silver", "Streak", "streak", 7, 400, 100),
        ("streak_30", "Immortal Hearth", "Maintained a 30-day streak of relentless daily learning.", "badge_flame_mythic", "Mythic", "Streak", "streak", 30, 1500, 500),
        ("flawless_vector", "Flawless Execution", "Scored 100% accuracy on 3 challenges in a single session.", "badge_star", "Gold", "Skill", "flawless_score", 3, 500, 120),
        ("anti_farm_clean", "Integrity Sentinel", "Completed 20 activities with pristine speed and zero anti-abuse flags.", "badge_shield_gold", "Gold", "Integrity", "clean_record", 20, 450, 100),
        ("raid_conqueror", "Raid Boss Slayer", "Contributed over 500 XP to the Batch Collective Raid Boss defeat.", "badge_boss", "Mythic", "Cooperation", "raid_damage", 500, 800, 250)
    ]
    cursor.executemany("""
    INSERT INTO badges (slug, name, description, icon, tier, category, requirement_type, requirement_threshold, xp_reward, gold_reward)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, badges_data)

    # 3. Seed Shop Items (Cosmetics & Perks)
    shop_data = [
        ("frame_neon_cyan", "Cyber Cyberpunk Border", "frame", 150, 0, "icon_frame_cyan", "Luminous electric-cyan animated glowing HUD border.", "Rare", '{"border_color": "#00f2fe"}'),
        ("frame_dragon_gold", "Solar Dragon Crown", "frame", 350, 5, "icon_frame_gold", "Mythic gold-flame animated aura border.", "Legendary", '{"border_color": "#f59e0b"}'),
        ("frame_void_purple", "Void Weaver Halo", "frame", 200, 0, "icon_frame_purple", "Deep pulsating ultraviolet crystal border.", "Epic", '{"border_color": "#9d4edd"}'),
        ("title_bug_slayer", "Title: 'Bug Slayer'", "title", 100, 0, "icon_title_bug", "Equippable showcase title displayed across leaderboards.", "Common", '{"title": "Bug Slayer"}'),
        ("title_algo_master", "Title: 'Algorithm Alchemist'", "title", 250, 2, "icon_title_algo", "Prestigious title for verified coding conquerors.", "Epic", '{"title": "Algorithm Alchemist"}'),
        ("perk_streak_freeze", "Emergency Streak Freeze", "perk", 120, 0, "icon_streak_freeze", "Automatically protects your active streak if you miss a day.", "Rare", '{"freeze_count": 1}'),
        ("perk_xp_booster", "2x Overclock XP Capsule (24h)", "perk", 200, 3, "icon_xp_booster", "Doubles all XP earned from your next 3 activities.", "Epic", '{"xp_boost_multiplier": 2.0}')
    ]
    cursor.executemany("""
    INSERT INTO shop_items (item_code, title, category, cost_gold, cost_gems, icon, description, rarity, effect_data_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, shop_data)

    # 4. Seed Rich Activities (Quizzes, Code Quests, Bug Labs)
    activities_data = [
        # Activity 1: Python & Data Structures Mastery Quiz
        (
            "Data Structures & Big-O Sprint",
            "Test your algorithmic intuition on Time Complexity, Hash Maps, Trees, and Array memory layouts.",
            "quiz",
            "Data Structures",
            "Medium",
            4,
            140,
            35,
            12,
            json.dumps([
                {
                    "id": "q1",
                    "question": "What is the average-case time complexity of lookup and insertion in a balanced Hash Table?",
                    "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                    "correct_index": 0,
                    "explanation": "Hash tables compute array indices via hash functions in O(1) expected time, assuming a uniform distribution."
                },
                {
                    "id": "q2",
                    "question": "Which data structure operates on a Last-In, First-Out (LIFO) order?",
                    "options": ["Queue", "Stack", "Binary Heap", "Linked List"],
                    "correct_index": 1,
                    "explanation": "A Stack pushes and pops items from the top, making it strictly LIFO."
                },
                {
                    "id": "q3",
                    "question": "In a Balanced Binary Search Tree (AVL / Red-Black), searching for an element takes:",
                    "options": ["O(1)", "O(log n)", "O(n)", "O(n^2)"],
                    "correct_index": 1,
                    "explanation": "Because tree height is bounded by O(log n), search traverses at most log n levels."
                },
                {
                    "id": "q4",
                    "question": "Why does appending an item to a dynamically sized Array (e.g. Python list) have O(1) amortized time?",
                    "options": [
                        "Array memory is limitless in RAM",
                        "Memory doubling occurs infrequently enough that average cost per append is constant",
                        "Elements are stored as linked nodes",
                        "Garbage collection compresses memory instantly"
                    ],
                    "correct_index": 1,
                    "explanation": "When capacity is exhausted, the array doubles (cost O(n)), but this happens so rarely that the amortized cost per append is O(1)."
                }
            ]),
            None,
            json.dumps(["Remember the difference between worst-case rehashing and average hash table lookup.", "Think about stack call frames in recursion."])
        ),

        # Activity 2: Web Architecture & REST API Sprint
        (
            "Modern Web Protocols & HTTP/REST Duel",
            "Master HTTP status codes, idempotency, caching headers, and stateless client-server principles.",
            "quiz",
            "Web Systems",
            "Easy",
            3,
            110,
            25,
            10,
            json.dumps([
                {
                    "id": "w1",
                    "question": "Which HTTP method is defined as idempotent and used to replace an entire resource state?",
                    "options": ["POST", "PUT", "PATCH", "CONNECT"],
                    "correct_index": 1,
                    "explanation": "PUT is idempotent: sending the same PUT request multiple times produces the identical server state as sending it once."
                },
                {
                    "id": "w2",
                    "question": "What HTTP status code should be returned when a resource is successfully created?",
                    "options": ["200 OK", "201 Created", "204 No Content", "302 Found"],
                    "correct_index": 1,
                    "explanation": "HTTP 201 Created explicitly informs the client that a new resource URI has been generated."
                },
                {
                    "id": "w3",
                    "question": "What is the primary benefit of statelessness in REST architecture?",
                    "options": [
                        "Reduces client CPU usage",
                        "Allows servers to scale horizontally because any server can handle any request independently",
                        "Removes the need for database storage",
                        "Encrypts all headers automatically"
                    ],
                    "correct_index": 1,
                    "explanation": "Stateless servers don't store session state across requests, allowing easy load balancing across clusters."
                }
            ]),
            None,
            json.dumps(["Check difference between 200 and 201 status codes.", "Idempotency means repeated executions have identical side effects."])
        ),

        # Activity 3: Code Quest: Two-Sum Problem (Interactive Code Arena)
        (
            "Code Quest: The Two-Sum Target Lock",
            "Write an optimized algorithm in Python/JS to find indices of two numbers in an array that add up to a target sum.",
            "code_quest",
            "Algorithms",
            "Medium",
            8,
            260,
            70,
            20,
            json.dumps({
                "problem_statement": "Given an integer array `nums` and an integer `target`, return indices `[i, j]` of the two numbers such that `nums[i] + nums[j] == target`. You may assume exactly one solution exists and cannot use the same element twice.",
                "starter_code": {
                    "python": "def two_sum(nums, target):\n    # Optimized O(n) hash map solution\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []\n",
                    "javascript": "function twoSum(nums, target) {\n    const seen = new Map();\n    for (let i = 0; i < nums.length; i++) {\n        const complement = target - nums[i];\n        if (seen.has(complement)) {\n            return [seen.get(complement), i];\n        }\n        seen.set(nums[i], i);\n    }\n    return [];\n}"
                },
                "expected_complexity": "Time: O(n), Space: O(n)"
            }),
            json.dumps([
                {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1], "hidden": False},
                {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2], "hidden": False},
                {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1], "hidden": False},
                {"input": {"nums": [1, 5, 8, 12, 19], "target": 20}, "expected": [0, 4], "hidden": True}
            ]),
            json.dumps([
                "Hint 1: A brute-force nested loop is O(n^2). Can you use a Hash Map to store complements in O(n)?",
                "Hint 2: For each number `x`, check if `target - x` is already in your hash map before inserting `x`."
            ])
        ),

        # Activity 4: Code Quest: Palindrome Validator with Clean Code
        (
            "Code Quest: Palindrome Stream Sanitizer",
            "Validate whether a string is a palindrome, ignoring non-alphanumeric characters and case differences in O(n) time and O(1) extra space.",
            "code_quest",
            "Algorithms",
            "Easy",
            6,
            180,
            45,
            15,
            json.dumps({
                "problem_statement": "Write a function `is_palindrome(s)` that returns `True` if the string `s` is a palindrome after converting all uppercase letters into lowercase and removing all non-alphanumeric characters, otherwise `False`.",
                "starter_code": {
                    "python": "def is_palindrome(s: str) -> bool:\n    left, right = 0, len(s) - 1\n    while left < right:\n        while left < right and not s[left].isalnum():\n            left += 1\n        while left < right and not s[right].isalnum():\n            right -= 1\n        if s[left].lower() != s[right].lower():\n            return False\n        left += 1\n        right -= 1\n    return True\n",
                    "javascript": "function isPalindrome(s) {\n    let left = 0, right = s.length - 1;\n    while (left < right) {\n        while (left < right && !/[a-zA-Z0-9]/.test(s[left])) left++;\n        while (left < right && !/[a-zA-Z0-9]/.test(s[right])) right--;\n        if (s[left].toLowerCase() !== s[right].toLowerCase()) return false;\n        left++; right--;\n    }\n    return true;\n}"
                },
                "expected_complexity": "Time: O(n), Space: O(1)"
            }),
            json.dumps([
                {"input": {"s": "A man, a plan, a canal: Panama"}, "expected": True, "hidden": False},
                {"input": {"s": "race a car"}, "expected": False, "hidden": False},
                {"input": {"s": " "}, "expected": True, "hidden": False},
                {"input": {"s": "0P"}, "expected": False, "hidden": True}
            ]),
            json.dumps([
                "Hint: Use two pointers moving inward from both ends of the string.",
                "Hint: Skip characters that are not letters or digits (`isalnum()` in Python)."
            ])
        ),

        # Activity 5: Bug Hunter: Memory Leak & Async Race Condition
        (
            "Concept Lab: The Ghost Race Condition",
            "Identify the concurrency and state mutation bug in this reactive learner scoring counter.",
            "bug_hunt",
            "Problem Solving",
            "Hard",
            7,
            220,
            60,
            18,
            json.dumps({
                "scenario": "A student dashboard service updates points asynchronously. When multiple fast submissions occur, the total score gets corrupted due to non-atomic shared state updates.",
                "buggy_code": "let globalPoints = 0;\n\nasync function awardStudentPoints(userId, bonus) {\n    // BUGGY RACE CONDITION:\n    let current = await fetchUserPoints(userId); // asynchronous read\n    let updated = current + bonus;\n    await saveUserPoints(userId, updated); // asynchronous write overwrites concurrent updates\n    return updated;\n}",
                "correct_solution_explanation": "The read-modify-write cycle is not atomic. Multiple concurrent requests read the same initial value before either writes back. Fix: Use atomic database operations (e.g. `UPDATE users SET points = points + ? WHERE id = ?`) or distributed mutex locks.",
                "options": [
                    "The fetchUserPoints function takes too long",
                    "Non-atomic Read-Modify-Write creates a race condition where concurrent calls overwrite each other",
                    "The let keyword is deprecated in modern JS",
                    "Points must be stored as floating point numbers"
                ],
                "correct_option_index": 1
            }),
            None,
            json.dumps(["Look at what happens when two calls to awardStudentPoints arrive at the exact same millisecond.", "Is the write dependent on a stale read value?"])
        )
    ]

    cursor.executemany("""
    INSERT INTO activities (title, description, category, topic, difficulty, estimated_minutes, base_xp, base_gold, min_duration_seconds, content_json, test_cases_json, hints_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, activities_data)

    # 5. Seed Quests & Challenges
    quests_data = [
        ("Morning Scholar", "Complete at least 1 Knowledge Sprint or Quiz today.", "daily", "complete_any_activity", 1, 120, 40, 0, None, 1, None),
        ("Code Crafter", "Solve 1 algorithmic challenge in the Code Arena.", "daily", "solve_code_quest", 1, 200, 60, 1, None, 1, None),
        ("Streak Sustainer", "Log into QuestAcademy and complete any learning task to keep the fire alive.", "daily", "maintain_streak", 1, 100, 30, 0, None, 1, None),
        ("Sprint Prodigy", "Earn 350+ XP in a single day across any activities.", "daily", "earn_xp", 350, 250, 75, 2, None, 1, None),
        ("Weekly Marathoner", "Complete 5 distinct learning activities this week.", "weekly", "complete_any_activity", 5, 500, 150, 5, None, 1, None),
        ("Zero-Hint Mastery", "Solve 2 Code Quests or Quizzes without unlocking any hints.", "weekly", "zero_hints_challenge", 2, 450, 120, 3, None, 1, None),
        ("Batch Titan Collective Raid", "Collective Batch Goal: Contribute 5000 XP together to defeat the Algorithm Titan!", "raid_boss", "team_xp_contribution", 5000, 1000, 300, 10, 12, 1, None)
    ]
    cursor.executemany("""
    INSERT INTO quests (title, description, quest_type, criteria_type, target_count, xp_reward, gold_reward, gem_reward, badge_id_reward, is_active, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, quests_data)

    # 6. Seed Users (realistic students across 3 batches, plus faculty and admin)
    users_data = [
        # (username, full_name, email, role, avatar_url, level, xp, gold, gems, current_streak, max_streak, last_activity, freezes, batch, title, frame, theme)
        ("alex_hunter", "Alex Hunter (You)", "alex@questacademy.edu", "student", "avatar_cyber_ninja", 4, 1850, 420, 12, 5, 8, today_str, 2, "Batch CS-2026-Alpha", "Algorithm Alchemist", "frame_neon_cyan", "theme_cyber"),
        ("sarah_connor", "Sarah Connor", "sarah@questacademy.edu", "student", "avatar_sorceress", 7, 5200, 1150, 25, 14, 14, today_str, 3, "Batch CS-2026-Alpha", "Grandmaster Scholar", "frame_dragon_gold", "theme_cyber"),
        ("marcus_vance", "Marcus Vance", "marcus@questacademy.edu", "student", "avatar_paladin", 5, 2900, 680, 15, 9, 11, today_str, 1, "Batch CS-2026-Alpha", "Syntax Sorcerer", "frame_void_purple", "theme_cyber"),
        ("elena_rostova", "Elena Rostova", "elena@questacademy.edu", "student", "avatar_valkyrie", 6, 4100, 890, 20, 12, 12, today_str, 2, "Batch CS-2026-Beta", "Bug Slayer", "frame_neon_cyan", "theme_cyber"),
        ("kenji_sato", "Kenji Sato", "kenji@questacademy.edu", "student", "avatar_samurai", 5, 2750, 590, 14, 7, 9, yesterday_str, 1, "Batch CS-2026-Beta", "Code Vanguard", "frame_default", "theme_cyber"),
        ("priya_sharma", "Priya Sharma", "priya@questacademy.edu", "student", "avatar_mage", 6, 4400, 950, 22, 11, 15, today_str, 2, "Batch CS-2026-Beta", "Logic Oracle", "frame_dragon_gold", "theme_cyber"),
        ("david_kim", "David Kim", "david@questacademy.edu", "student", "avatar_cyborg", 4, 1950, 440, 10, 4, 6, today_str, 1, "Batch AI-2026-Sigma", "Neural Architect", "frame_void_purple", "theme_cyber"),
        ("maya_lin", "Maya Lin", "maya@questacademy.edu", "student", "avatar_ranger", 5, 3100, 710, 16, 8, 10, today_str, 2, "Batch AI-2026-Sigma", "Data Navigator", "frame_neon_cyan", "theme_cyber"),
        ("liam_o_connor", "Liam O'Connor", "liam@questacademy.edu", "student", "avatar_alchemist", 3, 1100, 260, 6, 3, 4, yesterday_str, 1, "Batch CS-2026-Alpha", "Novice Scholar", "frame_default", "theme_cyber"),
        ("zara_ahmed", "Zara Ahmed", "zara@questacademy.edu", "student", "avatar_oracle", 4, 2100, 480, 11, 6, 7, today_str, 2, "Batch AI-2026-Sigma", "Pattern Seeker", "frame_default", "theme_cyber"),
        ("jordan_reed", "Jordan Reed (Newbie)", "jordan@questacademy.edu", "student", "avatar_novice", 1, 150, 80, 2, 1, 1, today_str, 1, "Batch CS-2026-Alpha", "Novice Scholar", "frame_default", "theme_cyber"),
        ("prof_harrison", "Dr. Alan Harrison", "harrison@questacademy.edu", "faculty", "avatar_professor", 10, 15000, 5000, 100, 30, 30, today_str, 5, "Faculty Staff", "Dean of Computation", "frame_dragon_gold", "theme_cyber"),
        ("admin_root", "System Sentinel (Admin)", "admin@questacademy.edu", "admin", "avatar_admin", 10, 25000, 9999, 500, 50, 50, today_str, 10, "Administration", "Master Architect", "frame_dragon_gold", "theme_cyber")
    ]

    cursor.executemany("""
    INSERT INTO users (username, full_name, email, role, avatar_url, level, xp, gold, gems, current_streak, max_streak, last_activity_date, streak_freezes_left, batch_cohort, equipped_title, equipped_frame, equipped_theme)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # 7. Seed Initial Badges for Top Users
    user_badges_data = [
        (1, 1, yesterday_str, 1), # Alex: first_blood
        (1, 2, yesterday_str, 1), # Alex: quiz_adept
        (1, 4, today_str, 1),     # Alex: code_ninja
        (1, 7, today_str, 1),     # Alex: streak_3
        (2, 1, yesterday_str, 1), # Sarah
        (2, 3, today_str, 1),     # Sarah: quiz_grandmaster
        (2, 5, today_str, 1),     # Sarah: code_titan
        (2, 8, today_str, 1),     # Sarah: streak_7
        (3, 1, yesterday_str, 1), # Marcus
        (3, 4, today_str, 1),     # Marcus
        (4, 1, yesterday_str, 1), # Elena
        (4, 6, today_str, 1),     # Elena: bug_hunter
        (6, 1, yesterday_str, 1), # Priya
        (6, 5, today_str, 1)      # Priya
    ]
    cursor.executemany("INSERT OR IGNORE INTO user_badges (user_id, badge_id, unlocked_at, is_showcased) VALUES (?, ?, ?, ?)", user_badges_data)

    # 8. Seed User Inventory for Alex
    inventory_data = [
        (1, 1, yesterday_str, 1), # Cyber Cyberpunk Border (equipped)
        (1, 5, yesterday_str, 1), # Title: 'Algorithm Alchemist' (equipped)
        (1, 6, today_str, 0)      # Streak Freeze (in inventory)
    ]
    cursor.executemany("INSERT OR IGNORE INTO user_inventory (user_id, item_id, purchased_at, is_equipped) VALUES (?, ?, ?, ?)", inventory_data)

    # 9. Seed User Quest Progress for Alex (User ID 1)
    quest_progress_data = [
        (1, 1, 1, 1, 0, today_str, None), # Daily Morning Scholar completed, ready to claim
        (1, 2, 0, 0, 0, None, None),      # Daily Code Crafter in progress
        (1, 3, 1, 1, 1, today_str, today_str), # Daily Streak Sustainer claimed
        (1, 4, 140, 0, 0, None, None),    # Sprint Prodigy (140/350 XP)
        (1, 5, 3, 0, 0, None, None),      # Weekly Marathoner (3/5)
        (1, 6, 1, 0, 0, None, None),      # Zero-Hint Mastery (1/2)
        (1, 7, 1850, 0, 0, None, None)    # Raid Boss contribution
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO user_quest_progress (user_id, quest_id, current_progress, is_completed, claimed, completed_at, claimed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, quest_progress_data)

    # 10. Seed Realistic Activity Logs (Spanning past 30 days for Heatmaps & Analytics)
    activity_logs = []
    for day_offset in range(25, -1, -1):
        log_date = (now - timedelta(days=day_offset, hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        if day_offset in [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 20, 22, 24]:
            activity_logs.append((
                1, 1 if day_offset % 2 == 0 else 3, 1, 45 if day_offset % 2 == 0 else 120,
                100.0, 140 if day_offset % 2 == 0 else 260, 35 if day_offset % 2 == 0 else 70,
                1.2, 1.0, 0.0, int(140 * 1.2) if day_offset % 2 == 0 else int(260 * 1.2),
                int(35 * 1.2) if day_offset % 2 == 0 else int(70 * 1.2), 0, "Clean solution with hash map.", 0, None, log_date
            ))
        if day_offset in range(0, 20):
            activity_logs.append((
                2, (day_offset % 4) + 1, 1, 60, 100.0, 180, 50, 1.4, 1.0, 0.0, int(180 * 1.4), int(50 * 1.4), 0, "Good reflection.", 0, None, log_date
            ))

    cursor.executemany("""
    INSERT INTO user_activity_logs (
        user_id, activity_id, attempt_number, duration_seconds, score_percent,
        raw_xp, raw_gold, streak_multiplier, diminishing_multiplier, anti_farming_penalty,
        final_xp, final_gold, hints_used, reflection_text, flagged_abuse, abuse_reason, completed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, activity_logs)

    # 11. Seed Flagged Anti-Farming Audit Incidents
    audit_samples = [
        (9, 1, "SPEED_RUN_ABUSE", "Completed 4-question Data Structures Quiz in 1.4 seconds. Human threshold is 12s.", "Reduced XP/Gold to 0, logged warning flag.", "flagged", (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")),
        (9, 1, "REPETITIVE_FARMING", "Attempted the same quiz 5 times in 4 minutes with identical answers.", "Applied 0% diminishing return multiplier.", "confirmed", (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (5, 2, "COOLDOWN_VIOLATION", "Retried activity within 4 seconds of previous attempt (minimum 20s required).", "Blocked submission until cooldown cleared.", "pardoned", (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    cursor.executemany("""
    INSERT INTO anti_farming_audit_logs (user_id, activity_id, violation_type, detected_details, penalty_applied, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, audit_samples)

    # 12. Seed Team Raid Boss
    cursor.execute("""
    INSERT INTO team_raids (boss_name, boss_avatar, total_hp, current_hp, batch_cohort, reward_badge_id, reward_gold, reward_xp, ends_at, is_defeated)
    VALUES ('Algorithm Titan (Raid Boss)', 'boss_titan_golem', 10000, 3850, 'Batch CS-2026-Alpha', 12, 500, 1000, (datetime('now', '+3 days')), 0)
    """)

    conn.commit()

if __name__ == "__main__":
    init_db(force_reset=True)
    print("QuestAcademy SQLite database initialized & seeded successfully at:", DB_PATH)
