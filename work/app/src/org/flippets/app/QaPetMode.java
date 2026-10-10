package org.flippets.app;

import android.content.*;
import android.os.Build;
import java.util.Objects;

/** Emulator fixture: suspend a selected card while observing pet renderers. */
final class QaPetMode {
    final Context context;final SharedPreferences prefs;final boolean present;final String selected;
    QaPetMode(Context context){
        if(!(Build.HARDWARE.contains("ranchu")||Build.HARDWARE.contains("goldfish")))throw new IllegalStateException("Emulator only");
        this.context=context;prefs=MiniAppStore.prefs(context);present=prefs.contains("selected");selected=prefs.getString("selected",null);
        MiniAppStore.select(context,"none");
    }
    boolean restore(){
        SharedPreferences.Editor edit=prefs.edit().remove("selected");if(present)edit.putString("selected",selected);edit.apply();
        context.sendBroadcast(new Intent(Pets.EVENT).setPackage(context.getPackageName()));
        return present==prefs.contains("selected")&&Objects.equals(selected,prefs.getString("selected",null));
    }
}
