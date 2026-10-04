package org.flippets.app;

/** Immutable manual adjustment relative to a mode's automatic subject placement. */
public final class PetLayoutProfile {
    public static final PetLayoutProfile CLOCK=new PetLayoutProfile(false,1,0,0);
    public final boolean clockless;
    public final float scale,x,y;
    public PetLayoutProfile(boolean clockless,float scale,float x,float y){
        this.clockless=clockless;this.scale=clamp(scale,.6f,1.6f,1);this.x=clamp(x,-.25f,.25f,0);this.y=clamp(y,-.25f,.25f,0);
    }
    private static float clamp(float v,float lo,float hi,float fallback){return Float.isNaN(v)||Float.isInfinite(v)?fallback:Math.max(lo,Math.min(hi,v));}
    public String key(){return clockless+"/"+scale+"/"+x+"/"+y;}
}
