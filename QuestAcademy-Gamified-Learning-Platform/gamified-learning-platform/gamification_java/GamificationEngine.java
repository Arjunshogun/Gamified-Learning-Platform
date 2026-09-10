package gamification;

/**
 * GamificationEngine.java - High-performance Java Implementation of QuestAcademy
 * progression models, anti-farming mathematical verification, and reward calculators.
 */
public class GamificationEngine {

    /**
     * Quadratic Level Progression: Level = floor(sqrt(XP / 100)) + 1
     */
    public static int calculateLevel(int xp) {
        if (xp <= 0) return 1;
        return (int) Math.floor(Math.sqrt(xp / 100.0)) + 1;
    }

    public static int xpForLevelStart(int level) {
        if (level <= 1) return 0;
        return (level - 1) * (level - 1) * 100;
    }

    public static int xpForNextLevel(int level) {
        return level * level * 100;
    }

    public static double calculateLevelProgressPercent(int xp) {
        int level = calculateLevel(xp);
        int startXp = xpForLevelStart(level);
        int targetXp = xpForNextLevel(level);
        int currentInLevel = xp - startXp;
        int span = targetXp - startXp;
        if (span <= 0) return 100.0;
        return Math.min(100.0, Math.max(0.0, (currentInLevel / (double) span) * 100.0));
    }

    /**
     * Streak Multiplier: 1.0 + min((streak - 1) * 0.05, 0.50)
     */
    public static double calculateStreakMultiplier(int streakDays) {
        if (streakDays <= 1) return 1.0;
        double bonus = Math.min((streakDays - 1) * 0.05, 0.50);
        return Math.round((1.0 + bonus) * 100.0) / 100.0;
    }

    /**
     * Diminishing Returns Multiplier across repeat attempts
     */
    public static double getDiminishingReturnsMultiplier(int attemptNumber) {
        if (attemptNumber <= 1) return 1.0;  // 1st attempt = 100%
        if (attemptNumber == 2) return 0.50; // 2nd attempt = 50%
        if (attemptNumber == 3) return 0.20; // 3rd attempt = 20%
        return 0.0;                          // 4th+ attempt = 0%
    }

    /**
     * Speed-run Anti-Farming check
     */
    public static boolean isSpeedAbuse(int durationSeconds, int minThresholdSeconds) {
        return durationSeconds < minThresholdSeconds;
    }

    public static class RewardBreakdown {
        public final int finalXP;
        public final int finalGold;
        public final double streakMultiplier;
        public final double diminishingMultiplier;
        public final boolean isFlaggedAbuse;
        public final String statusMessage;

        public RewardBreakdown(int xp, int gold, double streakMult, double dimMult, boolean flagged, String msg) {
            this.finalXP = xp;
            this.finalGold = gold;
            this.streakMultiplier = streakMult;
            this.diminishingMultiplier = dimMult;
            this.isFlaggedAbuse = flagged;
            this.statusMessage = msg;
        }
    }

    /**
     * Full Reward Computation with Anti-Farming checks
     */
    public static RewardBreakdown calculateRewards(
            int baseXP,
            int baseGold,
            double scorePercent,
            int streakDays,
            int attemptNumber,
            int durationSeconds,
            int minThresholdSeconds,
            int hintsUsed
    ) {
        // Check Speed-Run Abuse
        if (isSpeedAbuse(durationSeconds, minThresholdSeconds)) {
            return new RewardBreakdown(
                    0, 0, 1.0, 0.0, true,
                    "SPEED_RUN_ABUSE: Activity completed faster than minimum threshold (" + durationSeconds + "s < " + minThresholdSeconds + "s)."
            );
        }

        double accuracyFactor = Math.max(0.0, Math.min(1.0, scorePercent / 100.0));
        double streakMult = calculateStreakMultiplier(streakDays);
        double dimMult = getDiminishingReturnsMultiplier(attemptNumber);
        double firstTryBonus = (attemptNumber == 1 && scorePercent >= 99.0) ? 1.25 : 1.0;
        int zeroHintsGold = (hintsUsed == 0 && scorePercent >= 80.0) ? 20 : 0;

        int rawXP = (int) (baseXP * accuracyFactor);
        int rawGold = (int) (baseGold * accuracyFactor);

        int finalXP = (int) ((rawXP * firstTryBonus * streakMult) * dimMult);
        int finalGold = (int) ((rawGold * streakMult + zeroHintsGold) * dimMult);

        return new RewardBreakdown(
                finalXP, finalGold, streakMult, dimMult, false,
                "Success: Attempt " + attemptNumber + " yields " + finalXP + " XP and " + finalGold + " Gold."
        );
    }
}
