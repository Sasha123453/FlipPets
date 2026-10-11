import android.graphics.Bitmap;
import dalvik.system.DexClassLoader;
import java.io.*;
import java.security.MessageDigest;
import java.util.zip.ZipFile;
import org.json.*;

/** Full-resolution source decoding only. Never loads an OEM host or changes settings. */
public final class NativePetProbe {
    static byte[] bytes(InputStream in)throws Exception{
        try(InputStream source=in;ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[32768];int n;while((n=source.read(b))!=-1)out.write(b,0,n);return out.toByteArray();
        }
    }
    static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02x",v&255));return s.toString();}
    static boolean donorReady(int[] pixels,int width,byte[] reference,int index){
        int count=0,bad=0,max=0;long total=0;
        for(int y=0;y<596;y++)for(int x=0;x<976;x++){
            int offset=(y*976+x)*4;
            if((reference[offset+3]&255)!=255)continue;
            int pixel=pixels[(y+796)*width+x];
            int error=Math.max(Math.abs(((pixel>>16)&255)-(reference[offset]&255)),
                      Math.max(Math.abs(((pixel>>8)&255)-(reference[offset+1]&255)),Math.abs((pixel&255)-(reference[offset+2]&255))));
            count++;if(error>1)bad++;max=Math.max(max,error);total+=error;
        }
        return count>=100000 && bad<=count*.005 && total<=count*.1 && (index!=0||max==0);
    }
    public static void main(String[] args)throws Exception{
        if(!android.os.Build.HARDWARE.contains("ranchu")&&!android.os.Build.HARDWARE.contains("goldfish"))throw new SecurityException("Emulator required");
        if(args.length!=3 && args.length!=4)throw new IllegalArgumentException("APK, libraries, isolated output directory, optional candidate required");
        ClassLoader loader=new DexClassLoader(args[0],null,args[1],NativePetProbe.class.getClassLoader());
        Class<?> file=loader.loadClass("org.libpag.PAGFile"),composition=loader.loadClass("org.libpag.PAGComposition"),surface=loader.loadClass("org.libpag.PAGSurface"),player=loader.loadClass("org.libpag.PAGPlayer");
        byte[] source;
        if(args.length==4){
            if(!args[2].matches("/data/local/tmp/flippets-native-pet-[0-9a-f]{32}") || !args[3].equals(args[2]+"/candidate.pag"))throw new SecurityException("Isolated emulator candidate required");
            source=bytes(new FileInputStream(args[3]));
        }else{try(ZipFile apk=new ZipFile(args[0])){source=bytes(apk.getInputStream(apk.getEntry("assets/pets/bird-pandora/pag_0.pag")));}}
        Object f=file.getMethod("Load",byte[].class).invoke(null,(Object)source);if(f==null)throw new IOException("PAG load failed");
        int w=(Integer)composition.getMethod("width").invoke(f),h=(Integer)composition.getMethod("height").invoke(f);
        if(args.length==3?(w!=976||h!=596):(w!=1208||h!=1392))throw new IOException("Unexpected geometry");
        Object s=surface.getMethod("MakeOffscreen",int.class,int.class).invoke(null,w,h),p=player.getConstructor().newInstance();
        JSONArray frames=new JSONArray();int left=w,top=h,right=0,bottom=0;
        try{
            player.getMethod("setSurface",surface).invoke(p,s);player.getMethod("setComposition",composition).invoke(p,f);
            player.getMethod("setScaleMode",int.class).invoke(p,0); // No scaling, padding or resampling.
            double[] samples={0,.1,.25,.4,.55,.7,.85,.999999};
            for(int index=0;index<samples.length;index++){
                double progress=samples[index];player.getMethod("setProgress",double.class).invoke(p,progress);
                player.getMethod("prepare").invoke(p);player.getMethod("flush").invoke(p);
                byte[] reference=args.length==4?bytes(new FileInputStream(new File(args[2],String.format("reference-%02d.rgba",index)))):null;
                if(reference!=null&&reference.length!=976*596*4)throw new IOException("Invalid original-pose reference");
                Bitmap b=null;int[] pixels=new int[w*h];boolean ready=false;
                long deadline=android.os.SystemClock.elapsedRealtime()+5000;
                do{
                    b=(Bitmap)surface.getMethod("makeSnapshot").invoke(s);if(b==null)throw new IOException("No decoded snapshot");
                    if(b.getConfig()==Bitmap.Config.HARDWARE){Bitmap copy=b.copy(Bitmap.Config.ARGB_8888,false);b.recycle();b=copy;}
                    b.getPixels(pixels,0,w,0,0,w,h);
                    ready=reference==null||donorReady(pixels,w,reference,index);
                    if(ready)break;
                    b.recycle();b=null;
                    Thread.sleep(100);
                    player.getMethod("setProgress",double.class).invoke(p,Math.min(.999999,progress+1.0/180));
                    player.getMethod("prepare").invoke(p);player.getMethod("flush").invoke(p);
                    player.getMethod("setProgress",double.class).invoke(p,progress);
                    player.getMethod("prepare").invoke(p);player.getMethod("flush").invoke(p);
                }while(android.os.SystemClock.elapsedRealtime()<deadline);
                if(!ready)throw new IOException("Donor pose not ready in actual candidate decode: "+index);
                String name=String.format("frame-%02d.png",index);
                b.recycle();byte[] rgba=new byte[w*h*4];int l=w,t=h,r=0,d=0;
                for(int y=0;y<h;y++)for(int x=0;x<w;x++){
                    int pixel=pixels[y*w+x],offset=(y*w+x)*4;rgba[offset]=(byte)(pixel>>16);rgba[offset+1]=(byte)(pixel>>8);rgba[offset+2]=(byte)pixel;rgba[offset+3]=(byte)(pixel>>>24);
                    if((pixel>>>24)>=8){l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x+1);d=Math.max(d,y+1);}
                }
                if(r<=l||d<=t)throw new IOException("Empty sampled frame");
                left=Math.min(left,l);top=Math.min(top,t);right=Math.max(right,r);bottom=Math.max(bottom,d);
                String raw=String.format("frame-%02d.rgba",index);
                try(FileOutputStream out=new FileOutputStream(new File(args[2],raw))){out.write(rgba);}
                frames.put(new JSONObject().put("progress",progress).put("png",name).put("raw",raw).put("rgbaSha256",hex(MessageDigest.getInstance("SHA-256").digest(rgba))).put("alphaBounds",new JSONArray(new int[]{l,t,r,d})));
            }
        }finally{player.getMethod("release").invoke(p);surface.getMethod("release").invoke(s);}
        System.out.println(new JSONObject().put("sourceSha256",hex(MessageDigest.getInstance("SHA-256").digest(source))).put("width",w).put("height",h).put("durationUs",file.getMethod("duration").invoke(f)).put("alphaThreshold",8).put("sampledUnionBounds",new JSONArray(new int[]{left,top,right,bottom})).put("frames",frames).toString(2));
        System.exit(0);
    }
}
