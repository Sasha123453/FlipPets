package org.flippets.app;
import android.content.*;
/** Shell-only receiver. Finishes only sessions launched by our controller. */
public final class StopCover extends BroadcastReceiver {
    public void onReceive(Context c,Intent i){if("org.flippets.app.STOP_COVER".equals(i.getAction()))PetActivity.closeCovers();}
}
