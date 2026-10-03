import android.graphics.*;
import dalvik.system.DexClassLoader;
import org.json.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.zip.*;

/** Real root-content padding test; no changing end-state playback or donor bytes. */
public final class HairPaddingProbe {
    static byte[] read(InputStream in)throws Exception{ByteArrayOutputStream o=new ByteArrayOutputStream();byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)o.write(b,0,n);return o.toByteArray();}
    public static void main(String[] args)throws Exception{
        if(!android.os.Build.HARDWARE.contains("ranchu")&&!android.os.Build.HARDWARE.contains("goldfish"))throw new SecurityException("Emulator required");
        ClassLoader loader=new DexClassLoader(args[0],null,args[1],HairPaddingProbe.class.getClassLoader());
        Class<?> file=loader.loadClass("org.libpag.PAGFile"),comp=loader.loadClass("org.libpag.PAGComposition"),layer=loader.loadClass("org.libpag.PAGLayer"),surface=loader.loadClass("org.libpag.PAGSurface"),player=loader.loadClass("org.libpag.PAGPlayer");
        JSONArray results=new JSONArray();byte[] data;try(ZipFile zip=new ZipFile(args[0])){data=read(zip.getInputStream(zip.getEntry("assets/pets/bird-pandora/pag_0.pag")));}
        for(int variant=0;variant<3;variant++){int padding=variant==0?0:64;
            Object f=file.getMethod("Load",byte[].class).invoke(null,(Object)data);int w=(Integer)comp.getMethod("width").invoke(f),h=(Integer)comp.getMethod("height").invoke(f);JSONArray layers=new JSONArray();
            int count=(Integer)comp.getMethod("numChildren").invoke(f);
            for(int i=0;i<count;i++){
                Object child=comp.getMethod("getLayerAt",int.class).invoke(f,i);JSONObject info=new JSONObject().put("name",layer.getMethod("layerName").invoke(child)).put("type",layer.getMethod("layerType").invoke(child)).put("bounds",String.valueOf(layer.getMethod("getBounds").invoke(child)));layers.put(info);
                int nested=comp.isInstance(child)?(Integer)comp.getMethod("numChildren").invoke(child):-1;info.put("children",nested);
                if(variant==2&&nested>=0){int cw=(Integer)comp.getMethod("width").invoke(child),ch=(Integer)comp.getMethod("height").invoke(child);comp.getMethod("setContentSize",int.class,int.class).invoke(child,cw+2*padding,ch+2*padding);for(int j=0;j<nested;j++){Object grand=comp.getMethod("getLayerAt",int.class).invoke(child,j);Matrix gm=(Matrix)layer.getMethod("matrix").invoke(grand);gm.postTranslate(padding,padding);layer.getMethod("setMatrix",Matrix.class).invoke(grand,gm);}if(nested>0){Matrix cm=(Matrix)layer.getMethod("matrix").invoke(child);cm.postTranslate(-padding,-padding);layer.getMethod("setMatrix",Matrix.class).invoke(child,cm);}}
                if(padding>0){Matrix m=(Matrix)layer.getMethod("matrix").invoke(child);m.postTranslate(padding,padding);layer.getMethod("setMatrix",Matrix.class).invoke(child,m);}
            }
            if(padding>0)comp.getMethod("setContentSize",int.class,int.class).invoke(f,w+2*padding,h+2*padding);
            int sw=w+2*padding,sh=h+2*padding;Object s=surface.getMethod("MakeOffscreen",int.class,int.class).invoke(null,sw,sh),p=player.getConstructor().newInstance();player.getMethod("setSurface",surface).invoke(p,s);player.getMethod("setComposition",comp).invoke(p,f);player.getMethod("setScaleMode",int.class).invoke(p,0);
            JSONArray frames=new JSONArray();try{for(double progress:new double[]{.55,.70,.98,.999,1}){
                player.getMethod("setProgress",double.class).invoke(p,progress);player.getMethod("flush").invoke(p);Bitmap b=(Bitmap)surface.getMethod("makeSnapshot").invoke(s);
                if(b.getConfig()==Bitmap.Config.HARDWARE){Bitmap copy=b.copy(Bitmap.Config.ARGB_8888,false);b.recycle();b=copy;}
                int[] pixels=new int[sw*sh];b.getPixels(pixels,0,sw,0,0,sw,sh);int recovered=0,top=sh;
                for(int y=0;y<sh;y++)for(int x=padding+(int)(w*.30f);x<padding+(int)(w*.84f);x++)if((pixels[y*sw+x]>>>24)>=8){top=Math.min(top,y);if(y<padding)recovered++;}
                frames.put(new JSONObject().put("progress",progress).put("topInSubjectColumns",top-padding).put("recoveredTopPixels",recovered));
                try(FileOutputStream out=new FileOutputStream("/data/local/tmp/flip-hair-variant"+variant+"-"+(int)(progress*1000)+".png")){b.compress(Bitmap.CompressFormat.PNG,100,out);}b.recycle();
            }}finally{player.getMethod("release").invoke(p);surface.getMethod("release").invoke(s);}
            results.put(new JSONObject().put("variant",variant).put("padding",padding).put("expandInner",variant==2).put("layers",layers).put("frames",frames));
        }
        System.out.println(new JSONObject().put("results",results).toString(2));System.exit(0);
    }
}
