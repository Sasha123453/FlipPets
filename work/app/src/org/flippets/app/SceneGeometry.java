package org.flippets.app;

/** Original foreground occupies x=332..976 in the 976x596 design. */
public final class SceneGeometry {
    public static float scale(int w,int h,float safeLeft){return Math.min(Math.min(w/976f,h/596f),Math.max(1,w-safeLeft)/644f);}
    public static float x(int w,float scale){return w-976*scale;}
    public static float y(int h,float scale){return (h-596*scale)/2;}
}
