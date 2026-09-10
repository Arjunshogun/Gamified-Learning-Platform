package gamification;

/**
 * ScoringRulesTest.java - Standalone Java verification suite for QuestAcademy rules.
 */
public class ScoringRulesTest {

    public static void main(String[] args) {
        System.out.println("================================================================================");
        System.out.println("           QUESTACADEMY GAMIFICATION ENGINE - JAVA VERIFICATION SUITE           ");
        System.out.println("================================================================================");

        int passed = 0;
        int total = 0;

        // Test 1: Level Progression Curve
        total++;
        int lvl0 = GamificationEngine.calculateLevel(0);
        int lvl150 = GamificationEngine.calculateLevel(150);
        int lvl400 = GamificationEngine.calculateLevel(400);
        int lvl900 = GamificationEngine.calculateLevel(900);
        int lvl2500 = GamificationEngine.calculateLevel(2500);
        if (lvl0 == 1 && lvl150 == 2 && lvl400 == 3 && lvl900 == 4 && lvl2500 == 6) {
            System.out.println(" [PASS] Level Curve Calculations (0 XP=Lvl 1, 150 XP=Lvl 2, 900 XP=Lvl 4, 2500 XP=Lvl 6)");
            passed++;
        } else {
            System.err.println(" [FAIL] Level Curve mismatch!");
        }

        // Test 2: Streak Multipliers
        total++;
        double s1 = GamificationEngine.calculateStreakMultiplier(1);
        double s5 = GamificationEngine.calculateStreakMultiplier(5);
        double s15 = GamificationEngine.calculateStreakMultiplier(15);
        if (s1 == 1.0 && s5 == 1.20 && s15 == 1.50) {
            System.out.println(" [PASS] Streak Multiplier Scaling (1 day=1.0x, 5 days=1.20x, 15 days=1.50x Max Cap)");
            passed++;
        } else {
            System.err.println(" [FAIL] Streak Multipliers: " + s1 + ", " + s5 + ", " + s15);
        }

        // Test 3: Diminishing Returns across Repeat Attempts
        total++;
        double d1 = GamificationEngine.getDiminishingReturnsMultiplier(1);
        double d2 = GamificationEngine.getDiminishingReturnsMultiplier(2);
        double d3 = GamificationEngine.getDiminishingReturnsMultiplier(3);
        double d4 = GamificationEngine.getDiminishingReturnsMultiplier(4);
        if (d1 == 1.0 && d2 == 0.50 && d3 == 0.20 && d4 == 0.0) {
            System.out.println(" [PASS] Diminishing Returns Curve (Att. 1=100%, Att. 2=50%, Att. 3=20%, Att. 4+=0%)");
            passed++;
        } else {
            System.err.println(" [FAIL] Diminishing Returns mismatch!");
        }

        // Test 4: Speed-Run Abuse Blocker
        total++;
        GamificationEngine.RewardBreakdown abuse = GamificationEngine.calculateRewards(
                200, 50, 100.0, 5, 1, 3, 15, 0
        );
        if (abuse.isFlaggedAbuse && abuse.finalXP == 0 && abuse.finalGold == 0) {
            System.out.println(" [PASS] Speed-Run Abuse Blocker (3s < 15s Threshold -> 0 XP / Flagged Incident)");
            passed++;
        } else {
            System.err.println(" [FAIL] Speed-Run Abuse Blocker failed!");
        }

        // Test 5: Full Reward Calculation with First-Try & Streak Bonus
        total++;
        GamificationEngine.RewardBreakdown normal = GamificationEngine.calculateRewards(
                200, 50, 100.0, 5, 1, 45, 15, 0
        );
        // Base XP 200 * 1.25 (first try) * 1.20 (5d streak) * 1.0 = 300 XP
        // Base Gold (50 * 1.20 + 20 zero-hints) * 1.0 = 80 Gold
        if (!normal.isFlaggedAbuse && normal.finalXP == 300 && normal.finalGold == 80) {
            System.out.println(" [PASS] Full Effort Reward Calculation (300 XP, 80 Gold with +25% First-Try and +20% Streak)");
            passed++;
        } else {
            System.err.println(" [FAIL] Reward Calculation mismatch: XP=" + normal.finalXP + ", Gold=" + normal.finalGold);
        }

        System.out.println("--------------------------------------------------------------------------------");
        System.out.println(" Test Summary: " + passed + " / " + total + " Java Verification Tests Passed!");
        System.out.println("================================================================================");
    }
}
