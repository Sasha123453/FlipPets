package org.flippets.app;

/** Event ordering and walking cadence translated from Xiaomi pet MAML. */
public final class PetState {
    public boolean charging, lowBattery, music, rain;
    public long notificationUntil, stepUntil, overrideUntil, lastStep;
    public int stepIndex, overrideIndex = -1;
    private long lastSensorTimestamp;
    public void sensorStep(long timestamp, long now) {
        // Two resumed activities can receive the same physical step.
        if (timestamp <= lastSensorTimestamp) return;
        lastSensorTimestamp = timestamp;
        step(now);
    }
    public int index(long now) {
        if (overrideIndex >= 0 && now < overrideUntil) return overrideIndex;
        if (now < stepUntil) return stepIndex;
        if (music) return 3;
        if (now < notificationUntil) return 4;
        if (charging) return 5;
        if (lowBattery) return 6;
        if (rain) return 7;
        return 0;
    }
    public void step(long now) {
        stepIndex = lastStep > 0 && now-lastStep <= 375 ? 1 : 2;
        lastStep = now; stepUntil = now + 1900;
    }
}
