package org.flippets.app;
import android.view.Display;
public final class NativeCoverRouteTest {
    static int count;
    static final int F=Display.FLAG_SECURE|Display.FLAG_SUPPORTS_PROTECTED_BUFFERS|Display.FLAG_PRESENTATION;
    static void check(String name,boolean value){if(!value)throw new AssertionError(name);count++;System.out.println(name);}
    static boolean route(String device,int id,int flags,int mw,int mh,int ww,int wh,boolean awake,boolean locked){return NativeCoverRoute.matches(device,id,flags,mw,mh,ww,wh,awake,locked);}
    public static void main(String[] args){
        check("observed_cover_context",route("ruyi",1,F,1208,1392,1208,1392,true,false));
        check("display_id_not_hardcoded",route("ruyi",7,F,1208,1392,1208,1392,true,false));
        check("rotated_cover_bounds",route("ruyi",7,F,1208,1392,1392,1208,true,false));
        check("main_display_rejected",!route("ruyi",0,F,1208,1392,1208,1392,true,false));
        check("narrow_main_rejected",!route("ruyi",7,F,1224,2912,600,1392,true,false));
        check("narrow_cover_window_rejected",!route("ruyi",7,F,1208,1392,300,5568,true,false));
        check("unknown_device_rejected",!route("other",7,F,1208,1392,1208,1392,true,false));
        check("private_display_rejected",!route("ruyi",7,F|Display.FLAG_PRIVATE,1208,1392,1208,1392,true,false));
        check("incomplete_flags_rejected",!route("ruyi",7,Display.FLAG_PRESENTATION,1208,1392,1208,1392,true,false));
        check("unknown_mode_rejected",!route("ruyi",7,F,1080,1920,1080,1920,true,false));
        check("sleep_rejected",!route("ruyi",7,F,1208,1392,1208,1392,false,false));
        check("lock_rejected",!route("ruyi",7,F,1208,1392,1208,1392,true,true));
        check("invalid_id_rejected",!route("ruyi",-2,F,1208,1392,1208,1392,true,false));
        check("zero_window_rejected",!route("ruyi",7,F,1208,1392,0,0,true,false));
        if(count!=14)throw new AssertionError("Expected 14 cases");
    }
}
