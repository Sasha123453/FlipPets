package org.flippets.app;
import android.app.*;
import android.graphics.Rect;
import android.os.*;
import android.view.*;

/** Conservative observed MIX Flip display profile; native admission is separate. */
final class NativeCoverRoute {
    static boolean matches(String device,int displayId,int flags,int modeW,int modeH,int windowW,int windowH,boolean awake,boolean locked){
        int required=Display.FLAG_SECURE|Display.FLAG_SUPPORTS_PROTECTED_BUFFERS|Display.FLAG_PRESENTATION;
        boolean mode=Math.min(modeW,modeH)==1208&&Math.max(modeW,modeH)==1392;
        return "ruyi".equals(device)&&displayId>Display.DEFAULT_DISPLAY
            &&(flags&required)==required&&(flags&Display.FLAG_PRIVATE)==0&&mode
            &&Math.min(windowW,windowH)>=1208*4/5&&Math.max(windowW,windowH)>=1392*4/5
            &&(long)windowW*windowH>=(long)modeW*modeH*4/5&&awake&&!locked;
    }
    static boolean isCover(Activity a){
        Display d=Build.VERSION.SDK_INT>=30?a.getDisplay():a.getWindowManager().getDefaultDisplay();if(d==null||!d.isValid()||d.getState()!=Display.STATE_ON)return false;
        Display.Mode mode=d.getMode();Rect bounds;
        if(Build.VERSION.SDK_INT>=30)bounds=a.getWindowManager().getCurrentWindowMetrics().getBounds();
        else{bounds=new Rect();a.getWindowManager().getDefaultDisplay().getRectSize(bounds);}
        PowerManager power=(PowerManager)a.getSystemService(Activity.POWER_SERVICE);
        KeyguardManager keyguard=(KeyguardManager)a.getSystemService(Activity.KEYGUARD_SERVICE);
        return matches(Build.DEVICE,d.getDisplayId(),d.getFlags(),mode.getPhysicalWidth(),mode.getPhysicalHeight(),bounds.width(),bounds.height(),power!=null&&power.isInteractive(),keyguard==null||keyguard.isKeyguardLocked());
    }
}
