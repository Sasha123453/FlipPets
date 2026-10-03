package org.flippets.app;

/** Playback rules from the original MAML, independent of Android rendering. */
public final class PlaybackPolicy {
    public static boolean classic(String id) {
        return id.startsWith("bird-") || id.startsWith("seal-") || id.startsWith("sheep-")
            || id.startsWith("capybara-") || id.startsWith("otter-");
    }
    public static boolean repeats(String id, String kind, int scene, boolean calm) {
        if(classic(id)) return false;
        if(kind.equals("reactive")) return scene < 8 && !calm;
        return true;
    }
}
