"""
test_system.py - Comprehensive Automated Test Suite for QuestAcademy
Validates points engine, leveling formulas, anti-farming checks, diminishing returns, and REST API endpoints.
"""

import unittest
import json
from database import init_db, get_db_connection
import gamification_engine as engine
from app import app

class TestQuestAcademy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Fresh database init
        init_db(force_reset=True)
        cls.client = app.test_client()

    def setUp(self):
        self.conn = get_db_connection()

    def tearDown(self):
        self.conn.close()

    def test_01_level_progression_curve(self):
        """Test quadratic level progression formula: Level = floor(sqrt(XP/100)) + 1."""
        self.assertEqual(engine.calculate_level(0), 1)
        self.assertEqual(engine.calculate_level(99), 1)
        self.assertEqual(engine.calculate_level(100), 2)
        self.assertEqual(engine.calculate_level(399), 2)
        self.assertEqual(engine.calculate_level(400), 3)
        self.assertEqual(engine.calculate_level(900), 4)
        self.assertEqual(engine.calculate_level(2500), 6)

        prog = engine.get_level_progress(250)
        self.assertEqual(prog["level"], 2)
        self.assertEqual(prog["level_start_xp"], 100)
        self.assertEqual(prog["next_level_xp"], 400)
        self.assertEqual(prog["progress_percent"], 50.0)

    def test_02_streak_multiplier(self):
        """Test streak multiplier scaling with step and cap."""
        m1 = engine.get_streak_multiplier(1, self.conn)
        m5 = engine.get_streak_multiplier(5, self.conn)
        m15 = engine.get_streak_multiplier(15, self.conn)
        self.assertEqual(m1, 1.0)
        self.assertEqual(m5, 1.20)
        self.assertEqual(m15, 1.50) # Capped at 1.50

    def test_03_anti_farming_speed_run_detection(self):
        """Test that unrealistic fast completion triggers speed abuse and gives 0 XP."""
        # Activity 1 requires min 12 seconds. Test with 2 seconds:
        eval_result = engine.evaluate_anti_farming(
            user_id=1,
            activity_id=1,
            duration_seconds=2,
            hints_used=0,
            conn=self.conn
        )
        self.assertTrue(eval_result["flagged"])
        self.assertEqual(eval_result["violation_type"], "SPEED_RUN_ABUSE")
        self.assertEqual(eval_result["penalty_multiplier"], 0.0)

    def test_04_diminishing_returns(self):
        """Test that repeated attempts of the same task receive diminishing returns."""
        # Use user 11 (Jordan Reed) for isolated test
        uid = 11
        # 1st attempt
        r1 = engine.calculate_activity_rewards(uid, 2, 100.0, 30, 0, "", self.conn)
        self.assertEqual(r1["anti_farming_info"]["diminishing_mult"], 1.0)
        self.assertGreater(r1["final_xp"], 0)

        # Update log timestamp to simulate cooldown expiration
        cursor = self.conn.cursor()
        cursor.execute("UPDATE user_activity_logs SET completed_at = datetime('now', '-30 seconds') WHERE user_id = ?", (uid,))
        self.conn.commit()

        # 2nd attempt
        r2 = engine.calculate_activity_rewards(uid, 2, 100.0, 30, 0, "", self.conn)
        self.assertEqual(r2["anti_farming_info"]["diminishing_mult"], 0.50)

        cursor.execute("UPDATE user_activity_logs SET completed_at = datetime('now', '-30 seconds') WHERE user_id = ?", (uid,))
        self.conn.commit()

        # 3rd attempt
        r3 = engine.calculate_activity_rewards(uid, 2, 100.0, 30, 0, "", self.conn)
        self.assertEqual(r3["anti_farming_info"]["diminishing_mult"], 0.20)

        cursor.execute("UPDATE user_activity_logs SET completed_at = datetime('now', '-30 seconds') WHERE user_id = ?", (uid,))
        self.conn.commit()

        # 4th attempt -> Practice mode (0 rewards)
        r4 = engine.calculate_activity_rewards(uid, 2, 100.0, 30, 0, "", self.conn)
        self.assertEqual(r4["anti_farming_info"]["diminishing_mult"], 0.0)
        self.assertEqual(r4["final_xp"], 0)

    def test_05_api_hud_and_activities(self):
        """Test Flask REST API /api/user/hud and /api/activities."""
        res = self.client.get("/api/user/hud?user_id=1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["username"], "alex_hunter")

        res_act = self.client.get("/api/activities")
        self.assertEqual(res_act.status_code, 200)
        act_data = res_act.get_json()
        self.assertTrue(act_data["success"])
        self.assertGreater(len(act_data["activities"]), 0)

    def test_06_api_quiz_submission(self):
        """Test submitting answers to Knowledge Sprint Quiz."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 8 # Maya Lin
        
        # Clear previous logs for fresh attempt
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM user_activity_logs WHERE user_id = 8 AND activity_id = 1")
        self.conn.commit()

        payload = {
            "answers": {"q1": 0, "q2": 1, "q3": 1, "q4": 1}, # All 4 correct
            "duration_seconds": 45,
            "hints_used": 0,
            "reflection_text": "LIFO is stacks and Big-O hash table average is O(1)."
        }
        res = self.client.post("/api/activities/1/submit", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["score_percent"], 100.0)
        self.assertGreater(data["final_xp"], 0)

    def test_07_api_code_runner(self):
        """Test live execution of python code in Two-Sum Code Quest."""
        solution_code = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
"""
        payload = {
            "code": solution_code,
            "activity_id": 3,
            "language": "python"
        }
        res = self.client.post("/api/code/run", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["all_passed"])
        self.assertEqual(data["passed"], data["total"])

    def test_08_leaderboard_endpoints(self):
        """Test individual, batch, and streak leaderboards."""
        res_ind = self.client.get("/api/leaderboard?type=individual")
        self.assertEqual(res_ind.status_code, 200)
        self.assertTrue(res_ind.get_json()["success"])

        res_batch = self.client.get("/api/leaderboard?type=batch")
        self.assertEqual(res_batch.status_code, 200)
        self.assertTrue(res_batch.get_json()["success"])

        res_streak = self.client.get("/api/leaderboard?type=streak")
        self.assertEqual(res_streak.status_code, 200)
        self.assertTrue(res_streak.get_json()["success"])

if __name__ == "__main__":
    unittest.main()
