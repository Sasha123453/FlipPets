package org.flippets.app;

/** Stock PetsPagView translation table and Zoom transform, isolated from donor placement. */
final class MixFlipGeometry {
    static boolean stock(String id){return id!=null&&id.startsWith("mixflip-");}
    static int translation(int type,int scene){
        switch((type-1)*3+scene+1){
            case 4:case 5:case 7:case 8:return 100;
            case 10:case 16:return 90;
            case 13:case 14:case 15:case 17:case 18:return 30;
            default:return 0;
        }
    }
    static float[] matrix(int width,int height,int sourceW,int sourceH,int type,int scene,int rotation){
        if(width<=0||height<=0||sourceW<=0||sourceH<=0||type<1||type>6||scene<0||scene>2||(rotation!=0&&rotation!=2))throw new IllegalArgumentException("Stock pet geometry");
        float scale=Math.max(width/(float)sourceW,height/(float)sourceH),x=(width-sourceW*scale)/2,y=(height-sourceH*scale)/2;
        if(rotation==0){int index=(type-1)*3+scene+1;if(index==10)x+=translation(type,scene)*scale;else return new float[]{-scale,scale,width-x+translation(type,scene)*scale,y};}
        return new float[]{scale,scale,x,y};
    }
}
