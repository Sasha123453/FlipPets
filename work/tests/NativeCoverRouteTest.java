package org.flippets.app;
import android.view.Display;
public final class NativeCoverRouteTest {
    static int count;
    static final int F=Display.FLAG_SECURE|Display.FLAG_SUPPORTS_PROTECTED_BUFFERS|Display.FLAG_PRESENTATION;
    static void check(String name,boolean value){if(!value)throw new AssertionError(name);count++;System.out.println(name);}
    static boolean route(String device,int id,int flags,int mw,int mh,int ww,int wh,boolean awake,boolean locked){return NativeCoverRoute.matches(device,NativeCoverRoute.EEA_BUILD,520,id,flags,mw,mh,ww,wh,awake,locked);}
    static boolean folded(String build,int density,int flags,int ww,int wh,boolean awake,boolean locked){return NativeCoverRoute.matches("ruyi",build,density,0,flags,1208,1392,ww,wh,awake,locked);}
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
        check("documented_basic_region",route("ruyi",7,F,1208,1392,809,1392,true,false));
        check("documented_basic_region_rotated",route("ruyi",7,F,1208,1392,1392,809,true,false));
        check("rotated_mode_basic_region",route("ruyi",7,F,1392,1208,809,1392,true,false));
        check("rotated_mode_and_basic_region",route("ruyi",7,F,1392,1208,1392,809,true,false));
        check("basic_main_display_rejected",!route("ruyi",0,F,1208,1392,809,1392,true,false));
        check("basic_unknown_mode_rejected",!route("ruyi",7,F,1224,2912,809,1392,true,false));
        check("basic_incomplete_flags_rejected",!route("ruyi",7,Display.FLAG_PRESENTATION,1208,1392,809,1392,true,false));
        check("basic_private_display_rejected",!route("ruyi",7,F|Display.FLAG_PRIVATE,1208,1392,809,1392,true,false));
        check("basic_locked_rejected",!route("ruyi",7,F,1208,1392,809,1392,true,true));
        check("basic_asleep_rejected",!route("ruyi",7,F,1208,1392,809,1392,false,false));
        check("near_basic_unverified_rejected",!route("ruyi",7,F,1208,1392,808,1392,true,false));
        check("oversized_window_rejected",!route("ruyi",7,F,1208,1392,1208,2000,true,false));
        check("negative_window_rejected",!route("ruyi",7,F,1208,1392,-1208,-1392,true,false));
        check("basic_wrong_device_rejected",!route("other",7,F,1208,1392,809,1392,true,false));
        check("folded_default_scaled_basic",folded(NativeCoverRoute.EEA_BUILD,520,16523,1011,1740,true,false));
        check("folded_default_scaled_basic_rotated",folded(NativeCoverRoute.EEA_BUILD,520,16523,1740,1011,true,false));
        check("folded_rotated_mode_scaled_basic",route("ruyi",0,16523,1392,1208,1740,1011,true,false));
        check("folded_default_physical_basic",folded(NativeCoverRoute.EEA_BUILD,520,16523,809,1392,true,false));
        check("folded_default_full",folded(NativeCoverRoute.EEA_BUILD,520,16523,1208,1392,true,false));
        check("folded_default_build_guard",!folded("unknown",520,16523,1011,1740,true,false));
        check("folded_default_density_guard",!folded(NativeCoverRoute.EEA_BUILD,416,16523,1011,1740,true,false));
        check("folded_default_exact_flags_guard",!folded(NativeCoverRoute.EEA_BUILD,520,F,1011,1740,true,false));
        check("near_scaled_basic_rejected",!folded(NativeCoverRoute.EEA_BUILD,520,16523,1010,1740,true,false));
        check("scaled_basic_on_external_context_rejected",!route("ruyi",7,16523,1208,1392,1011,1740,true,false));
        check("folded_default_locked_rejected",!folded(NativeCoverRoute.EEA_BUILD,520,16523,1011,1740,true,true));
        check("folded_default_asleep_rejected",!folded(NativeCoverRoute.EEA_BUILD,520,16523,1011,1740,false,false));
        if(count!=40)throw new AssertionError("Expected 40 cases");
    }
}
