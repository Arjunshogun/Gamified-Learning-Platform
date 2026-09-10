# ⚔️ QuestAcademy: Gamified Student Learning Platform — Walkthrough & Deliverables

All project source code, database, assets, polyglot algorithms, tests, and launch scripts have been developed and packaged into the dedicated folder:
📂 **`c:\Users\arjun\Downloads\gamified-learning-platform\`**

A standalone distributable ZIP archive has also been created at:
📦 **[`QuestAcademy-Gamified-Learning-Platform.zip`](file:///c:/Users/arjun/Downloads/QuestAcademy-Gamified-Learning-Platform.zip)**

---

## 📁 Complete Folder Structure

```
c:\Users\arjun\Downloads\gamified-learning-platform\
├── run.bat                          # One-click Windows launch script
├── requirements.txt                 # Dependencies (Flask >= 3.0.0)
├── README.md                        # Comprehensive system documentation
├── app.py                           # Flask application server & full REST API
├── database.py                      # SQLite database schema & rich seed data
├── eduquest.db                      # Pre-seeded SQLite database file
├── gamification_engine.py           # Core XP, leveling, streak & anti-farming engine
├── test_system.py                   # Automated Python unit & integration test suite (8/8 Passed)
│
├── gamification_java/               # Polyglot Java 21 Engine & Verification Suite
│   ├── GamificationEngine.java      # Java implementation of progression formulas
│   └── ScoringRulesTest.java        # Java test suite (5/5 Passed)
│
├── templates/
│   └── index.html                   # Cyberpunk HUD, Topbar, Modals, Views & Canvas
│
└── static/
    ├── css/
    │   └── main.css                 # Cyber-RPG dark mode design system & animations
    └── js/
        ├── audio.js                 # Web Audio API synthesizers (zero external MP3 dependencies)
        ├── app.js                   # Main application state manager, routing & toasts
        ├── quizzes.js               # Knowledge Sprint Quiz runner with timer & combo meters
        ├── code_quest.js            # Algorithmic Code Arena with live test runner & hints
        ├── leaderboard.js           # Real-time Individual, Batch & Streak leaderboards
        ├── profile.js               # 5-Axis Skill Radar Canvas, 60-day heatmap & badges
        ├── admin.js                 # Faculty rule sliders, anti-farming audit & analytics
        └── demo_runner.js           # 1-Click Guided Demo tour runner for judges
```

---

## 🚀 How to Run the Platform

### 1. Launch the Application:
Double-click `run.bat` or run:
```powershell
cd c:\Users\arjun\Downloads\gamified-learning-platform
python app.py
```
Open **`http://127.0.0.1:5000`** in your web browser.

### 2. Run Automated Python Test Suite (8/8 Tests Passed):
```powershell
python test_system.py
```

### 3. Run Polyglot Java Verification Suite (5/5 Tests Passed):
```powershell
javac -d . gamification_java/GamificationEngine.java gamification_java/ScoringRulesTest.java
java gamification.ScoringRulesTest
```

---

## 🎯 Verification & Features Implemented

| Core Capability | Implementation Details | Status |
| :--- | :--- | :---: |
| **Points & Progression Engine** | Quadratic level curve $\text{Level} = \lfloor \sqrt{XP/100} \rfloor + 1$, Gold/Gems economy, and streak multipliers up to $+50\%$. | ✅ Verified |
| **Anti-Point Farming System** | Speed run anomaly detection ($\ge 12\text{s}$ threshold), diminishing returns across repeat attempts ($100\% \rightarrow 50\% \rightarrow 20\% \rightarrow 0\%$), 20s cooldowns, and daily hard caps. | ✅ Verified |
| **Interactive Learning Activities** | 1) *Knowledge Duel Quizzes* with feedback & reflections. 2) *Code Quest Arena* with live test runners (Two-Sum, Palindromes). 3) *Bug Hunter* labs. | ✅ Verified |
| **Cohort & Team Dynamics** | Batch Battle leaderboards (CS-Alpha vs CS-Beta vs AI-Sigma) ranked by learning velocity + collaborative *Algorithm Titan* Raid Boss. | ✅ Verified |
| **Student Profile Matrix** | Canvas-rendered 5-Axis Mastery Radar, 60-day activity heatmap, 12+ achievement badges (Bronze $\rightarrow$ Mythic), and cosmetics inventory. | ✅ Verified |
| **Faculty Governance Control** | Real-time scoring sliders, live anti-farming security audit logs, incident pardon/confirm actions, and cohort retention analytics. | ✅ Verified |
| **Game-Like Audio-Visual UX** | Cyberpunk dark mode, luminous borders, Web Audio synthesized sound effects, level-up fanfares, and particle confetti. | ✅ Verified |
| **1-Click Guided Demo Mode** | Automated 6-step guided walkthrough for hackathon judges demonstrating end-to-end flows in seconds. | ✅ Verified |
