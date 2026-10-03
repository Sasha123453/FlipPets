import org.flippets.app.CoverGeometry;

/** Geometric invariants: no Android device, screenshot or renderer mocks. */
public final class CoverGeometryTest {
    static int assertions;
    static void yes(boolean value,String label){assertions++;if(!value)throw new AssertionError(label);}
    static void near(float expected,float actual,float tolerance,String label){yes(Math.abs(expected-actual)<=tolerance,label+": "+expected+" != "+actual);}
    static void fitted(int w,int h,int sw,int sh,float[] bounds,float inset,float fraction){
        CoverGeometry.Placement p=CoverGeometry.fit(w,h,sw,sh,bounds,inset,fraction);
        near(p.right,p.x+bounds[2]*sw*p.scale,.02f,"right anchor");near(h,p.y+bounds[3]*sh*p.scale,.02f,"bottom anchor");
        yes(p.x+bounds[0]*sw*p.scale>=p.left-.02f,"content left respects safe viewport");yes(p.y+bounds[1]*sh*p.scale>=p.top-.02f,"content top respects viewport");
        yes(p.left>=w*.34f-.01f,"minimum camera column");yes(p.right<=w&&p.bottom<=h,"viewport inside panel");
        yes(p.scale>0&&!Float.isNaN(p.scale),"positive finite uniform scale");
    }
    public static void main(String[] args){
        float[][] envelopes={{0,0,1,1},{.15f,0,1,1},{.44f,.13f,.92f,.92f},{.28f,.08f,.95f,.95f}};
        int[][] screens={{1208,1392},{1392,1208},{640,738},{976,1125},{2560,1600},{1224,2912}};
        for(float[] bounds:envelopes)for(int[] screen:screens){fitted(screen[0],screen[1],976,596,bounds,screen[0]*.329f,.34f);fitted(screen[0],screen[1],904,572,bounds,screen[0]*.4f,.5f);}
        CoverGeometry.Placement a=CoverGeometry.fit(1208,1392,976,596,envelopes[2],398,.34f),b=CoverGeometry.fit(604,696,976,596,envelopes[2],199,.34f);
        near(a.scale/2,b.scale,.0001f,"resize scales uniformly");near(a.x/2,b.x,.01f,"resize keeps normalized horizontal position");near(a.y/2,b.y,.01f,"resize keeps normalized vertical position");
        CoverGeometry.Placement largerGap=CoverGeometry.fit(1208,1392,976,596,envelopes[2],398,.55f);yes(largerGap.scale<=a.scale,"more camera space cannot enlarge character");
        near(.34f,CoverGeometry.cameraFraction(Float.NaN),.0001f,"invalid preference defaults");near(.34f,CoverGeometry.cameraFraction(-1),.0001f,"negative preference clamped");near(.55f,CoverGeometry.cameraFraction(100),.0001f,"oversized preference clamped");
        for(int w:new int[]{1,100,640,976,1208,2560})near(w*1392f/1208,CoverGeometry.previewHeight(w,1208,1392),.51f,"exact preview aspect within pixel rounding");
        near(0,CoverGeometry.previewHeight(0,1208,1392),0,"zero-size preview");
        try{CoverGeometry.fit(0,1392,976,596,null,0,.34f);throw new AssertionError("zero canvas accepted");}catch(IllegalArgumentException expected){assertions++;}
        CoverGeometry.Placement fallback=CoverGeometry.fit(1208,1392,976,596,new float[]{Float.NaN,0,1,1},0,.34f);yes(fallback.scale>0,"bad envelope falls back to whole file");
        for(float inset:new float[]{-1,Float.NaN,Float.POSITIVE_INFINITY,2000}){CoverGeometry.Placement badInset=CoverGeometry.fit(1208,1392,976,596,null,inset,.34f);yes(badInset.scale>0&&!Float.isNaN(badInset.scale),"malformed cutout falls back safely");yes(badInset.left<badInset.right&&badInset.right<=1208,"malformed cutout keeps viewport on panel");}
        // Reviewed idle-pose face cores, not decorative branches/wings/ear tips.
        float[][] focus={{.30f,0,.84f,1},{.40f,.08f,.96f,.98f},{.34f,.10f,.90f,1},{.27f,.12f,.91f,.98f},{.43f,0,.95f,1},{.30f,0,.90f,1},{.34f,.10f,.94f,1}};
        float[][] faces={{.46f,.12f,.79f,.58f},{.47f,.17f,.85f,.63f},{.52f,.42f,.80f,.75f},{.45f,.20f,.78f,.55f},{.60f,.32f,.92f,.68f},{.46f,.12f,.85f,.45f},{.45f,.25f,.85f,.62f}};
        for(int i=0;i<focus.length;i++)for(int[] screen:screens){int w=screen[0],h=screen[1];CoverGeometry.Placement normal=CoverGeometry.fit(w,h,976,596,focus[i],w*.329f,.34f),natural=CoverGeometry.focused(w,h,976,596,focus[i],w*.329f,.34f);near(normal.scale*1.10f,natural.scale,.0001f,"fixed10percent enlargement");near(natural.right,natural.x+focus[i][2]*976*natural.scale,.02f,"focused right anchor");near(natural.bottom,natural.y+focus[i][3]*596*natural.scale,.02f,"focused bottom anchor");yes(natural.x+faces[i][0]*976*natural.scale>=natural.left-.01f,"reviewed face core remains right of camera guide");yes(natural.y+faces[i][1]*596*natural.scale>=0,"reviewed face top remains on panel");if(i==3||i==5)yes(faces[i][1]*596*natural.scale>48,"opaque-scenery idle face stays below48px decorative feather");}
        System.out.println("CoverGeometry: "+assertions+" assertions passed");
    }
}
