import android.graphics.Bitmap;
import dalvik.system.DexClassLoader;
import org.json.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.zip.*;

/** Emulator-only, offline scan of this APK's transparent PAG artwork. No UI/data/settings. */
public final class AssetEnvelopeProbe {
    static byte[] bytes(InputStream in)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[32768];int n;while((n=in.read(b))>=0)out.write(b,0,n);return out.toByteArray();}
    public static void main(String[] args)throws Exception {
        if(!android.os.Build.HARDWARE.contains("ranchu")&&!android.os.Build.HARDWARE.contains("goldfish"))throw new SecurityException("Emulator required");
        if(args.length<2||args.length>3)throw new IllegalArgumentException("APK path, isolated library directory, optional asset-only ZIP required");
        ClassLoader loader=new DexClassLoader(args[0],null,args[1],AssetEnvelopeProbe.class.getClassLoader());
        Class<?> file=loader.loadClass("org.libpag.PAGFile"),composition=loader.loadClass("org.libpag.PAGComposition"),surface=loader.loadClass("org.libpag.PAGSurface"),player=loader.loadClass("org.libpag.PAGPlayer");
        JSONArray results=new JSONArray();
        try(ZipFile apk=new ZipFile(args.length==3?args[2]:args[0])) {
            JSONArray pets=new JSONArray(new String(bytes(apk.getInputStream(apk.getEntry("assets/catalog.json"))),"UTF-8"));
            for(int i=0;i<pets.length();i++) {
                JSONObject pet=pets.getJSONObject(i);if("composition".equals(pet.optString("kind")))continue;
                JSONObject clips=pet.getJSONObject("clips");java.util.Iterator<String> keys=clips.keys();
                while(keys.hasNext()) {
                    String key=keys.next(),path=clips.getString(key);if(!path.endsWith(".pag"))continue;
                    JSONObject result=new JSONObject().put("pet",pet.getString("id")).put("clip",key).put("path",path);Object s=null,p=null;
                    try {
                        Object f=file.getMethod("Load",byte[].class).invoke(null,(Object)bytes(apk.getInputStream(apk.getEntry("assets/"+path))));
                        int w=(Integer)composition.getMethod("width").invoke(f),h=(Integer)composition.getMethod("height").invoke(f);
                        int sw=Math.max(1,w/2),sh=Math.max(1,h/2);s=surface.getMethod("MakeOffscreen",int.class,int.class).invoke(null,sw,sh);p=player.getConstructor().newInstance();
                        player.getMethod("setSurface",surface).invoke(p,s);player.getMethod("setComposition",composition).invoke(p,f);player.getMethod("setScaleMode",int.class).invoke(p,2);
                        JSONArray frames=new JSONArray();int left=sw,top=sh,right=0,bottom=0;
                        for(double progress:new double[]{0,.1,.25,.4,.55,.7,.85,.98}) {
                            player.getMethod("setProgress",double.class).invoke(p,progress);player.getMethod("flush").invoke(p);Bitmap b=(Bitmap)surface.getMethod("makeSnapshot").invoke(s);
                            if(b.getConfig()==Bitmap.Config.HARDWARE){Bitmap copy=b.copy(Bitmap.Config.ARGB_8888,false);b.recycle();b=copy;}
                            if(args.length==3&&progress==.4)try(FileOutputStream out=new FileOutputStream("/data/local/tmp/flip-pets-envelope-"+pet.getString("id")+"-"+key+".png")){b.compress(Bitmap.CompressFormat.PNG,100,out);}
                            int[] pixels=new int[sw*sh];b.getPixels(pixels,0,sw,0,0,sw,sh);b.recycle();int l=sw,t=sh,r=0,d=0;
                            for(int y=0;y<sh;y++)for(int x=0;x<sw;x++)if((pixels[y*sw+x]>>>24)>=8){l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x+1);d=Math.max(d,y+1);}
                            if(r>l&&d>t){left=Math.min(left,l);top=Math.min(top,t);right=Math.max(right,r);bottom=Math.max(bottom,d);frames.put(new JSONArray(new double[]{progress,l/(double)sw,t/(double)sh,r/(double)sw,d/(double)sh,java.util.Arrays.hashCode(pixels)}));}
                        }
                        result.put("width",w).put("height",h).put("samples",frames).put("bounds",new JSONArray(new double[]{left/(double)sw,top/(double)sh,right/(double)sw,bottom/(double)sh}));
                    } catch(Throwable e){result.put("error",e.toString());}
                    finally{if(p!=null)player.getMethod("release").invoke(p);if(s!=null)surface.getMethod("release").invoke(s);}
                    results.put(result);System.err.println("Envelope "+pet.getString("id")+" "+key);
                }
            }
        }
        System.out.println(new JSONObject().put("sampleFractions",new JSONArray(new double[]{0,.1,.25,.4,.55,.7,.85,.98})).put("alphaThreshold",8).put("results",results).toString(2));
        System.exit(0); // Native decoder threads must not leave a detached probe alive.
    }
}
