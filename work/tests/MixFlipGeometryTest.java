package org.flippets.app;
public final class MixFlipGeometryTest {
    public static void main(String[] args){
        int[][] translation={{0,0,0},{100,100,0},{100,100,0},{90,0,0},{30,30,30},{90,30,30}};int checked=0;
        for(int type=1;type<=6;type++)for(int scene=0;scene<3;scene++){
            if(MixFlipGeometry.translation(type,scene)!=translation[type-1][scene])throw new AssertionError("Table");
            for(int rotation:new int[]{0,2})for(int w:new int[]{1208,604}){
                float[] m=MixFlipGeometry.matrix(w,w*1392/1208,1208,1392,type,scene,rotation);float scale=w/1208f;
                boolean mirror=rotation==0&&!(type==4&&scene==0);
                if(Math.abs(m[0]-(mirror?-scale:scale))>.001||Math.abs(m[1]-scale)>.001)throw new AssertionError("Orientation");
                float x=rotation==2?0:mirror?w+translation[type-1][scene]*scale:90*scale;
                if(Math.abs(m[2]-x)>.001||Math.abs(m[3])>.001)throw new AssertionError("Translation");
                if(PlaybackPolicy.repeats("mixflip-test","ambient",scene,false))throw new AssertionError("Stock loop");checked++;
            }
        }
        if(!PlaybackPolicy.classic("bird-pandora")||PlaybackPolicy.repeats("bird-pandora","ambient",0,false)||!PlaybackPolicy.repeats("koala-pandora","reactive",0,false))throw new AssertionError("Donor regression");
        System.out.println(checked+" stock matrices / finite policies passed; donor rules retained");
    }
}
