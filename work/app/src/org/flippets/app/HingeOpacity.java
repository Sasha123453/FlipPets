package org.flippets.app;

/** Hinge degrees and Xiaomi's documented-in-firmware discrete fold states are distinct. */
public final class HingeOpacity {
    public static float degrees(float angle){
        if(Float.isNaN(angle)||Float.isInfinite(angle))return 1;
        float x=Math.max(0,Math.min(1,(angle-5f)/170f));
        return x*x*(3-2*x);
    }
    public static float status(float value){
        if(Float.isNaN(value)||Float.isInfinite(value))return 1;
        return value<=0?0:value<=1?.08f:value<=2?.5f:1;
    }
}
