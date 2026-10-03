package org.flippets.app;

/** Pixel-independent cover placement using fixed per-pet normalized subject focus. */
public final class CoverGeometry {
    public static final int WIDTH=1208,HEIGHT=1392,DENSITY=520;
    public static final float CAMERA_FRACTION=.34f;
    public static final float SUBJECT_ZOOM=1.10f;
    private CoverGeometry(){}
    public static int previewHeight(int width,int coverWidth,int coverHeight){
        if(width<=0||coverWidth<=0||coverHeight<=0)return 0;
        return Math.max(1,Math.round(width*(coverHeight/(float)coverWidth)));
    }
    public static float cameraFraction(float requested){return Float.isNaN(requested)||Float.isInfinite(requested)?CAMERA_FRACTION:Math.max(CAMERA_FRACTION,Math.min(.55f,requested));}
    public static Placement fit(int width,int height,int sourceWidth,int sourceHeight,float[] envelope,float cameraRight,float fraction){
        if(width<=0||height<=0||sourceWidth<=0||sourceHeight<=0)throw new IllegalArgumentException("Positive canvas/source dimensions required");
        float l=0,t=0,r=1,b=1;
        if(envelope!=null&&envelope.length==4&&finite(envelope[0])&&finite(envelope[1])&&finite(envelope[2])&&finite(envelope[3])&&envelope[2]>envelope[0]&&envelope[3]>envelope[1]){l=Math.max(0,envelope[0]);t=Math.max(0,envelope[1]);r=Math.min(1,envelope[2]);b=Math.min(1,envelope[3]);}
        if(r<=l||b<=t){l=t=0;r=b=1;}
        float right=width*.98f,bottom=height;
        float inset=finite(cameraRight)&&cameraRight>=0&&cameraRight<width?cameraRight:0;
        float left=Math.min(right-Math.max(1,width*.005f),Math.max(width*cameraFraction(fraction),inset+width*.012f));
        float top=height*.31f;
        float scale=Math.min((right-left)/((r-l)*sourceWidth),(bottom-top)/((b-t)*sourceHeight));
        float x=right-r*sourceWidth*scale,y=bottom-b*sourceHeight*scale;
        return new Placement(scale,x,y,left,top,right,bottom);
    }
    /** Slightly larger subjects; the camera column is a placement guide, not a rectangular crop. */
    public static Placement focused(int width,int height,int sourceWidth,int sourceHeight,float[] envelope,float cameraRight,float fraction){
        Placement base=fit(width,height,sourceWidth,sourceHeight,envelope,cameraRight,fraction);
        float r=1,b=1;
        if(envelope!=null&&envelope.length==4&&finite(envelope[0])&&finite(envelope[1])&&finite(envelope[2])&&finite(envelope[3])&&envelope[2]>envelope[0]&&envelope[3]>envelope[1]){r=Math.min(1,envelope[2]);b=Math.min(1,envelope[3]);if(r<=Math.max(0,envelope[0])||b<=Math.max(0,envelope[1])){r=b=1;}}
        float scale=base.scale*SUBJECT_ZOOM;
        return new Placement(scale,base.right-r*sourceWidth*scale,base.bottom-b*sourceHeight*scale,base.left,base.top,base.right,base.bottom);
    }
    private static boolean finite(float v){return !Float.isNaN(v)&&!Float.isInfinite(v);}
    public static final class Placement {
        public final float scale,x,y,left,top,right,bottom;
        Placement(float scale,float x,float y,float left,float top,float right,float bottom){this.scale=scale;this.x=x;this.y=y;this.left=left;this.top=top;this.right=right;this.bottom=bottom;}
    }
}
