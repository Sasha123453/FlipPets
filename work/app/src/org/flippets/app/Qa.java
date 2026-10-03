package org.flippets.app;

import android.content.Context;
import android.graphics.Bitmap;
import org.libpag.*;
import org.json.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.security.MessageDigest;

/** Test only this app's assets; never captures the device's screen or notifications. */
public final class Qa {
    public static void run(Context context){
        JSONArray results=new JSONArray();int failed=0;
        try{
            JSONArray pets=Pets.catalog(context);
            for(int p=0;p<pets.length();p++){
                JSONObject pet=pets.getJSONObject(p),clips=pet.getJSONObject("clips");if(pet.optString("kind").equals("composition"))continue;java.util.Iterator<String> keys=clips.keys();
                while(keys.hasNext()){
                    String key=keys.next(),path=clips.getString(key);JSONObject result=new JSONObject().put("pet",pet.optString("name")).put("clip",key).put("path",path);
                    PAGPlayer player=null;PAGSurface surface=null;android.media.MediaMetadataRetriever video=null;
                    try{
                        long duration;
                        if(path.endsWith(".mp4")){video=new android.media.MediaMetadataRetriever();try(android.content.res.AssetFileDescriptor fd=context.getAssets().openFd(path)){video.setDataSource(fd.getFileDescriptor(),fd.getStartOffset(),fd.getLength());}duration=Long.parseLong(video.extractMetadata(android.media.MediaMetadataRetriever.METADATA_KEY_DURATION))*1000;result.put("width",video.extractMetadata(android.media.MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)).put("height",video.extractMetadata(android.media.MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)).put("durationUs",duration);}
                        else{PAGFile f=PAGFile.Load(context.getAssets(),path);if(f==null)throw new IOException("PAGFile.Load returned null");duration=f.duration();result.put("width",f.width()).put("height",f.height()).put("durationUs",duration);surface=PAGSurface.MakeOffscreen(320,512);if(surface==null)throw new IOException("No offscreen surface");player=new PAGPlayer();player.setSurface(surface);player.setComposition(f);player.setScaleMode(PAGScaleMode.LetterBox);}
                        JSONArray hashes=new JSONArray();boolean visible=false;
                        for(int frame=0;frame<2;frame++){
                            double progress=frame==0?0.2:0.7;Bitmap b;if(video!=null)b=video.getScaledFrameAtTime((long)(duration*progress),android.media.MediaMetadataRetriever.OPTION_CLOSEST,320,512);else{player.setProgress(progress);player.flush();b=surface.makeSnapshot();}if(b==null)throw new IOException("No snapshot");
                            if(b.getConfig()==Bitmap.Config.HARDWARE){Bitmap software=b.copy(Bitmap.Config.ARGB_8888,false);b.recycle();b=software;}
                            ByteBuffer pixels=ByteBuffer.allocate(b.getByteCount());b.copyPixelsToBuffer(pixels);byte[] data=pixels.array();String hash=hex(MessageDigest.getInstance("SHA-256").digest(data));hashes.put(hash);
                            int[] argb=new int[b.getWidth()*b.getHeight()];b.getPixels(argb,0,b.getWidth(),0,0,b.getWidth(),b.getHeight());for(int v:argb)if((v>>>24)>0){visible=true;break;}
                            if(key.equals("0")&&frame==0){try(FileOutputStream out=new FileOutputStream(new File(context.getExternalFilesDir(null),"pet-"+p+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}}
                            b.recycle();
                        }
                        boolean moving=!hashes.getString(0).equals(hashes.getString(1));result.put("frameHashes",hashes).put("visible",visible).put("framesDiffer",moving).put("ok",visible&&moving);if(!visible||!moving)failed++;
                    }catch(Throwable e){failed++;result.put("ok",false).put("error",e.toString());}
                    finally{if(player!=null)player.release();if(surface!=null)surface.release();if(video!=null)video.release();}
                    results.put(result);
                }
            }
            Pets.write(context,"qa.json",new JSONObject().put("apkSha256",binarySha(context)).put("tested",results.length()).put("failed",failed).put("results",results).toString(2));
            Pets.write(context,"displays.txt",Pets.displayReport(context));
        }catch(Throwable e){try{Pets.write(context,"qa-error.txt",e.toString());}catch(Exception ignored){}}
    }
    static String binary;
    static synchronized String binarySha(Context c)throws Exception{if(binary==null){MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream s=new FileInputStream(c.getApplicationInfo().sourceDir)){byte[] bytes=new byte[1024*1024];int n;while((n=s.read(bytes))!=-1)digest.update(bytes,0,n);}binary=hex(digest.digest());}return binary;}
    static String hex(byte[] bytes){StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format("%02x",b&255));return s.toString();}
}
