import android.graphics.Bitmap;
import dalvik.system.DexClassLoader;
import java.io.*;
import java.security.MessageDigest;
import org.json.*;

/** Original pixels on a guarded emulator; never enters Xiaomi's editor or settings. */
public final class MixFlipPetProbe {
    static String sha(byte[] bytes)throws Exception {StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))s.append(String.format("%02x",b&255));return s.toString();}
    public static void main(String[] args)throws Exception {
        if(!android.os.Build.HARDWARE.matches(".*(ranchu|goldfish).*"))throw new SecurityException("Emulator required");
        if((args.length!=5&&args.length!=6)||!args[2].matches("/data/local/tmp/flippets-mixflip-[0-9a-f]{32}")||!args[3].matches("(shuitun|dewen|shuita|bixiong|xianluo|heibao|charlie)-[0-2]")||!args[4].matches("[0-7]")||(args.length==6&&!args[5].equals("full")))throw new SecurityException("Isolated staging required");
        ClassLoader loader=new DexClassLoader(args[0],null,args[1],MixFlipPetProbe.class.getClassLoader());
        Class<?> file=loader.loadClass("org.libpag.PAGFile"),comp=loader.loadClass("org.libpag.PAGComposition"),surface=loader.loadClass("org.libpag.PAGSurface"),player=loader.loadClass("org.libpag.PAGPlayer");
        JSONArray result=new JSONArray();
        // Fixed source names only, capybara first. No private/host paths accepted.
        String[] names={"shuitun","dewen","shuita","bixiong","xianluo","heibao","charlie"};
        for(String name:names)for(int action=0;action<(name.equals("charlie")?1:3);action++){
            String stem=name+"-"+action;if(!stem.equals(args[3]))continue;byte[] raw;
            try(InputStream in=new FileInputStream(args[2]+"/"+stem+".pag");ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)out.write(b,0,n);raw=out.toByteArray();}
            Object f=file.getMethod("Load",byte[].class).invoke(null,(Object)raw);if(f==null)throw new IOException("Load failed "+stem);
            int w=(Integer)comp.getMethod("width").invoke(f),h=(Integer)comp.getMethod("height").invoke(f);
            if(w<=0||h<=0||w>4096||h>4096)throw new IOException("Unbounded dimensions");
            int sourceW=w,sourceH=h;float renderScale=args.length==6?1:Math.min(1,696f/Math.max(w,h));w=Math.round(w*renderScale);h=Math.round(h*renderScale);
            Object s=surface.getMethod("MakeOffscreen",int.class,int.class).invoke(null,w,h),p=player.getConstructor().newInstance();
            JSONArray frames=new JSONArray();
            try {
                player.getMethod("setSurface",surface).invoke(p,s);player.getMethod("setComposition",comp).invoke(p,f);player.getMethod("setScaleMode",int.class).invoke(p,2);player.getMethod("setCacheEnabled",boolean.class).invoke(p,false);
                double[] samples={0,.1,.25,.4,.55,.7,.85,1};
                for(int index=0;index<samples.length;index++){
                    if(index!=Integer.parseInt(args[4]))continue;
                    double progress=samples[index];int[] pixels=new int[w*h];Bitmap image=null;String previous="";int stable=0;boolean ready=false;
                    long started=android.os.SystemClock.elapsedRealtime(),deadline=started+8000;
                    do {
                        player.getMethod("setProgress",double.class).invoke(p,progress);player.getMethod("prepare").invoke(p);player.getMethod("flush").invoke(p);
                        image=(Bitmap)surface.getMethod("makeSnapshot").invoke(s);if(image==null)throw new IOException("No snapshot");
                        if(image.getConfig()==Bitmap.Config.HARDWARE){Bitmap copy=image.copy(Bitmap.Config.ARGB_8888,false);image.recycle();image=copy;}
                        image.getPixels(pixels,0,w,0,0,w,h);byte[] rgba=new byte[w*h*4];int visible=0;
                        for(int i=0;i<pixels.length;i++){int v=pixels[i];rgba[i*4]=(byte)(v>>16);rgba[i*4+1]=(byte)(v>>8);rgba[i*4+2]=(byte)v;rgba[i*4+3]=(byte)(v>>>24);if((v>>>24)>=8)visible++;}
                        String digest=sha(rgba);stable=digest.equals(previous)?stable+1:0;previous=digest;
                        if(stable>=2&&(visible>100||android.os.SystemClock.elapsedRealtime()-started>=1000)){ready=true;break;}image.recycle();image=null;Thread.sleep(100);
                    }while(android.os.SystemClock.elapsedRealtime()<deadline);
                    if(!ready)throw new IOException("Pixels not ready "+stem+"/"+index);
                    int l=w,t=h,r=0,b=0;for(int y=0;y<h;y++)for(int x=0;x<w;x++)if((pixels[y*w+x]>>>24)>=8){l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x+1);b=Math.max(b,y+1);}
                    String png=stem+"-"+index+".png";try(OutputStream out=new FileOutputStream(args[2]+"/"+png)){if(!image.compress(Bitmap.CompressFormat.PNG,100,out))throw new IOException("PNG failed");}image.recycle();
                    frames.put(new JSONObject().put("progress",progress).put("png",png).put("decodedRgbaSha256",previous).put("empty",r<=l||b<=t).put("alphaBounds",r<=l||b<=t?JSONObject.NULL:new JSONArray(new int[]{l,t,r,b})).put("stableSnapshots",stable+1));
                }
            }finally{player.getMethod("release").invoke(p);surface.getMethod("release").invoke(s);}
            android.graphics.RectF bounds=(android.graphics.RectF)file.getMethod("getBounds").invoke(f);
            result.put(new JSONObject().put("source",stem).put("sourceSha256",sha(raw)).put("width",sourceW).put("height",sourceH).put("renderWidth",w).put("renderHeight",h).put("layerBounds",new JSONArray(new float[]{bounds.left,bounds.top,bounds.right,bounds.bottom})).put("durationUs",file.getMethod("duration").invoke(f)).put("frames",frames));
        }
        System.out.println(new JSONObject().put("clips",result).toString());System.exit(0);
    }
}
