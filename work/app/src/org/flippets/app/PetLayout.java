package org.flippets.app;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONObject;

/** Saved per-pet/per-mode profiles. Drafts belong only to the Main preview stage. */
final class PetLayout {
    private PetLayout(){}
    static boolean supported(JSONObject pet){return !pet.optString("kind").equals("composition")&&!pet.optString("name").equals("Flowing glitter")&&!pet.optString("id").equals("system-effects");}
    static PetLayoutProfile read(Context c,JSONObject pet){if(!supported(pet))return PetLayoutProfile.CLOCK;SharedPreferences p=SceneSettings.prefs(c,pet.optString("id"));return read(p,p.getBoolean("petClockless",false));}
    static PetLayoutProfile read(SharedPreferences p,boolean clockless){String k=clockless?"petLarge":"petClock";return new PetLayoutProfile(clockless,p.getFloat(k+"Scale",1),p.getFloat(k+"X",0),p.getFloat(k+"Y",0));}
    static void save(Context c,String id,boolean clockless,PetLayoutProfile clock,PetLayoutProfile large){
        SharedPreferences.Editor e=SceneSettings.prefs(c,id).edit().putBoolean("petClockless",clockless);
        put(e,"petClock",clock);put(e,"petLarge",large);e.apply();
        // Geometry listeners read preferences; no scene choice/playback revision change.
        c.sendBroadcast(new android.content.Intent(Pets.EVENT).setPackage(c.getPackageName()));
    }
    private static void put(SharedPreferences.Editor e,String k,PetLayoutProfile profile){
        if(profile.scale==1&&profile.x==0&&profile.y==0){e.remove(k+"Scale").remove(k+"X").remove(k+"Y");}
        else e.putFloat(k+"Scale",profile.scale).putFloat(k+"X",profile.x).putFloat(k+"Y",profile.y);
    }
}
