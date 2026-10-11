package org.flippets.app;
import android.app.*;
import android.graphics.Rect;
import android.os.*;
import android.view.*;

/** Conservative observed MIX Flip display profile; native admission is separate. */
final class NativeCoverRoute {
    static final String EEA_BUILD="OS3.0.303.0.WNIEUXM";
    static boolean foldedIdentity(String build,int density,int displayId,int flags){
        return EEA_BUILD.equals(build)&&density==520&&displayId==Display.DEFAULT_DISPLAY&&flags==16523;
    }
    static boolean coverIdentity(String device,String build,int density,int displayId,int flags,int modeW,int modeH){
        int required=Display.FLAG_SECURE|Display.FLAG_SUPPORTS_PROTECTED_BUFFERS|Display.FLAG_PRESENTATION;
        boolean mode=Math.min(modeW,modeH)==1208&&Math.max(modeW,modeH)==1392;
        return "ruyi".equals(device)&&(displayId>Display.DEFAULT_DISPLAY||foldedIdentity(build,density,displayId,flags))
            &&(flags&required)==required&&(flags&Display.FLAG_PRIVATE)==0&&mode;
    }
    static boolean supportedWindow(int windowW,int windowH){
        int shortSide=Math.min(windowW,windowH),longSide=Math.max(windowW,windowH);
        // Xiaomi's documented basic app region is distinct from full-cover layout.
        // Do not widen this branch to arbitrary narrow or oversized windows.
        boolean basic=shortSide==809&&longSide==1392;
        boolean full=shortSide>=1208*4/5&&shortSide<=1208
            &&longSide>=1392*4/5&&longSide<=1392
            &&(long)windowW*windowH>=(long)1208*1392*4/5;
        return basic||full;
    }
    static boolean matches(String device,String build,int density,int displayId,int flags,int modeW,int modeH,int windowW,int windowH,boolean awake,boolean locked){
        // Actual folded EEA Main metrics: 809x1392 at OEM global scale 0.8,
        // exposed to the Activity as 1011x1740. Keep this an exact profile.
        boolean scaledBasic=foldedIdentity(build,density,displayId,flags)
            &&Math.min(windowW,windowH)==1011&&Math.max(windowW,windowH)==1740;
        return coverIdentity(device,build,density,displayId,flags,modeW,modeH)
            &&(supportedWindow(windowW,windowH)||scaledBasic)&&awake&&!locked;
    }
    static boolean isCover(Activity a){
        Display d=Build.VERSION.SDK_INT>=30?a.getDisplay():a.getWindowManager().getDefaultDisplay();if(d==null||!d.isValid()||d.getState()!=Display.STATE_ON)return false;
        Display.Mode mode=d.getMode();Rect bounds;
        if(Build.VERSION.SDK_INT>=30)bounds=a.getWindowManager().getCurrentWindowMetrics().getBounds();
        else{bounds=new Rect();a.getWindowManager().getDefaultDisplay().getRectSize(bounds);}
        PowerManager power=(PowerManager)a.getSystemService(Activity.POWER_SERVICE);
        KeyguardManager keyguard=(KeyguardManager)a.getSystemService(Activity.KEYGUARD_SERVICE);
        return matches(Build.DEVICE,Build.VERSION.INCREMENTAL,a.getResources().getDisplayMetrics().densityDpi,d.getDisplayId(),d.getFlags(),mode.getPhysicalWidth(),mode.getPhysicalHeight(),bounds.width(),bounds.height(),power!=null&&power.isInteractive(),keyguard==null||keyguard.isKeyguardLocked());
    }
}
