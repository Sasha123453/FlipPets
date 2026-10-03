import android.graphics.*;
import dalvik.system.DexClassLoader;
import org.json.*;
import org.flippets.app.CoverGeometry;
import java.io.*;
import java.lang.reflect.*;
import java.util.zip.*;

/** Test the real libpag nested-composition clip, not a Canvas screenshot substitute. */
public final class CoverGraphProbe {
    static byte[] read(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();}
    public static void main(String[] args)throws Exception{
        if(!android.os.Build.HARDWARE.contains("ranchu")&&!android.os.Build.HARDWARE.contains("goldfish"))throw new SecurityException("Emulator required");
        ClassLoader loader=new DexClassLoader(args[0],null,args[1],CoverGraphProbe.class.getClassLoader());
        Class<?> file=loader.loadClass("org.libpag.PAGFile"),comp=loader.loadClass("org.libpag.PAGComposition"),layer=loader.loadClass("org.libpag.PAGLayer"),surface=loader.loadClass("org.libpag.PAGSurface"),player=loader.loadClass("org.libpag.PAGPlayer");
        JSONArray results=new JSONArray();
        try(ZipFile zip=new ZipFile(args[2])){for(String id:new String[]{"charlie","bubbles"}){
            Object f=file.getMethod("Load",byte[].class).invoke(null,(Object)read(zip.getInputStream(zip.getEntry("assets/"+id+".pag"))));
            int w=(Integer)comp.getMethod("width").invoke(f),h=(Integer)comp.getMethod("height").invoke(f);
            CoverGeometry.Placement place=CoverGeometry.fit(1208,1392,w,h,id.equals("charlie")?new float[]{.30f,0,.84f,1}:new float[]{.40f,.08f,.96f,.98f},398,.34f);
            int left=(int)Math.ceil(place.left),top=(int)Math.ceil(place.top),right=(int)Math.floor(place.right),bottom=1392;
            Object inner=comp.getMethod("Make",int.class,int.class).invoke(null,right-left,bottom-top);
            Matrix transform=new Matrix();transform.setScale(place.scale,place.scale);transform.postTranslate(place.x-left,place.y-top);layer.getMethod("setMatrix",Matrix.class).invoke(f,transform);comp.getMethod("addLayer",layer).invoke(inner,f);
            Matrix position=new Matrix();position.setTranslate(left,top);layer.getMethod("setMatrix",Matrix.class).invoke(inner,position);
            Object root=comp.getMethod("Make",int.class,int.class).invoke(null,1208,1392);comp.getMethod("addLayer",layer).invoke(root,inner);
            Object s=surface.getMethod("MakeOffscreen",int.class,int.class).invoke(null,1208,1392),p=player.getConstructor().newInstance();player.getMethod("setSurface",surface).invoke(p,s);player.getMethod("setComposition",comp).invoke(p,root);player.getMethod("setScaleMode",int.class).invoke(p,0);
            JSONArray frames=new JSONArray();try{for(double progress:new double[]{0,.2,.4,.7,.98}){
                player.getMethod("setProgress",double.class).invoke(p,progress);player.getMethod("flush").invoke(p);Bitmap bitmap=(Bitmap)surface.getMethod("makeSnapshot").invoke(s);
                if(bitmap.getConfig()==Bitmap.Config.HARDWARE){Bitmap copy=bitmap.copy(Bitmap.Config.ARGB_8888,false);bitmap.recycle();bitmap=copy;}
                int[] pixels=new int[1208*1392];bitmap.getPixels(pixels,0,1208,0,0,1208,1392);int outside=0,visible=0;
                for(int y=0;y<1392;y++)for(int x=0;x<1208;x++)if((pixels[y*1208+x]>>>24)>=8){visible++;if(x<left||x>=right||y<top||y>=bottom)outside++;}
                frames.put(new JSONObject().put("progress",progress).put("outsideViewport",outside).put("visiblePixels",visible).put("frameHash",java.util.Arrays.hashCode(pixels)));
                if(progress==.4)try(FileOutputStream out=new FileOutputStream("/data/local/tmp/flip-pets-graph-"+id+".png")){bitmap.compress(Bitmap.CompressFormat.PNG,100,out);}bitmap.recycle();
            }}finally{player.getMethod("release").invoke(p);surface.getMethod("release").invoke(s);}
            results.put(new JSONObject().put("id",id).put("scale",place.scale).put("translateX",place.x).put("translateY",place.y).put("viewport",new JSONArray(new int[]{left,top,right,bottom})).put("frames",frames));
        }}
        System.out.println(new JSONObject().put("results",results).toString(2));System.exit(0);
    }
}
