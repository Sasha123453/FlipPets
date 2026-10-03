package org.flippets.app;

import android.content.Context;
import android.graphics.*;
import org.json.*;
import java.io.*;
import java.security.MessageDigest;
import java.nio.ByteBuffer;

/** Emulator-only deterministic tests for rendering and imported-image isolation. */
public final class CompositionQa {
    static int patches;
    static String hash(Bitmap b)throws Exception{ByteBuffer bytes=ByteBuffer.allocate(b.getByteCount());b.copyPixelsToBuffer(bytes);return Qa.hex(MessageDigest.getInstance("SHA-256").digest(bytes.array()));}
    static void save(Context c,Bitmap b,String name)throws Exception{try(FileOutputStream s=new FileOutputStream(new File(c.getExternalFilesDir(null),name))){b.compress(Bitmap.CompressFormat.PNG,100,s);}}
    static boolean varied(Bitmap b){int first=b.getPixel(0,0);for(int y=0;y<b.getHeight();y+=9)for(int x=0;x<b.getWidth();x+=9)if(b.getPixel(x,y)!=first)return true;return false;}
    public static void run(Context c){
        patches=0;JSONObject report=new JSONObject();JSONArray results=new JSONArray();int failed=0,decoded=0;CompositionRenderer renderer=new CompositionRenderer(c);
        try{
            for(int i=0;i<Pets.catalog(c).length();i++){
                JSONObject pet=Pets.catalog(c).getJSONObject(i);if(!pet.optString("kind").equals("composition"))continue;
                String[] tones=pet.optString("renderer").equals("stretch")||pet.optString("originalFile").startsWith("cc8f")?new String[]{"blue","purple","green","orange","red"}:new String[]{pet.optString("defaultColor")};
                android.content.SharedPreferences p=SceneSettings.prefs(c,pet.getString("id"));java.util.Map<String,?> before=p.getAll();
                try{
                    for(String tone:tones)for(int aspect=0;aspect<3;aspect++){
                        JSONObject result=new JSONObject().put("pet",pet.optString("name")).put("color",tone).put("aspect",aspect==0?"cover 1392x1208":aspect==1?"cover 1208x1392":"inner 1224x2912");
                        Bitmap b=Bitmap.createBitmap(aspect==0?696:aspect==1?604:612,aspect==0?604:aspect==1?696:1456,Bitmap.Config.ARGB_8888);
                        try{p.edit().putString("color",tone).apply();renderer.touch(.7f,.9f,10000);renderer.draw(new Canvas(b),b.getWidth(),b.getHeight(),pet,1791026640123L,10120);String first=hash(b);boolean visible=varied(b);
                            if(tone.equals(tones[0])&&aspect==0)save(c,b,"pet-"+i+".png");
                            renderer.draw(new Canvas(b),b.getWidth(),b.getHeight(),pet,1791026700789L,11000);String second=hash(b);boolean changed=!first.equals(second);
                            result.put("visible",visible).put("framesDiffer",changed).put("hash1",first).put("hash2",second).put("ok",visible&&changed);if(!visible||!changed)failed++;
                        }catch(Throwable e){failed++;result.put("ok",false).put("error",e.toString());}finally{b.recycle();}results.put(result);
                    }
                    String type=pet.optString("renderer");if(type.equals("stretch")){Bitmap b=Bitmap.createBitmap(604,696,Bitmap.Config.ARGB_8888);p.edit().putInt("layout",0).apply();renderer.touch(.7f,.9f,10000);renderer.draw(new Canvas(b),604,696,pet,1791026640123L,10050);String stretched=hash(b);renderer.draw(new Canvas(b),604,696,pet,1791026640123L,14000);String settled=hash(b);p.edit().putInt("layout",1).apply();renderer.draw(new Canvas(b),604,696,pet,1791026640123L,14000);String alternate=hash(b);boolean ok=!stretched.equals(settled)&&!settled.equals(alternate);results.put(new JSONObject().put("test","touch spring and alternate layout").put("ok",ok));if(!ok)failed++;b.recycle();}
                    if(type.equals("signature")){Bitmap b=Bitmap.createBitmap(604,696,Bitmap.Config.ARGB_8888);p.edit().putString("signature","Тест\nMIX Flip").putInt("layout",0).apply();renderer.draw(new Canvas(b),604,696,pet,1791026640123L,14000);String centered=hash(b);p.edit().putInt("layout",3).putInt("font",1).apply();renderer.draw(new Canvas(b),604,696,pet,1791026640123L,14000);boolean ok=!centered.equals(hash(b));results.put(new JSONObject().put("test","signature text font and vertical layout").put("ok",ok));if(!ok)failed++;b.recycle();}
                }finally{android.content.SharedPreferences.Editor e=p.edit().clear();for(java.util.Map.Entry<String,?> entry:before.entrySet()){Object v=entry.getValue();String key=entry.getKey();if(v instanceof String)e.putString(key,(String)v);else if(v instanceof Integer)e.putInt(key,(Integer)v);else if(v instanceof Long)e.putLong(key,(Long)v);else if(v instanceof Float)e.putFloat(key,(Float)v);else if(v instanceof Boolean)e.putBoolean(key,(Boolean)v);}e.apply();renderer.release();}
                decoded+=decodeAssets(c,pet.optString("assetRoot"));
            }
            for(String font:new String[]{"MiSansVF.ttf","Qinghe.otf","Coca-ColaCareFontKaiTi.TTF","FZFWZhuZiAYuanJWB.TTF","MiSansRoundedSC.ttf"}){Typeface.createFromAsset(c.getAssets(),"fonts/"+font);results.put(new JSONObject().put("test","load original font "+font).put("ok",true));}
            // Real import/downsample/alpha/storage/clear code, using only a synthetic app-owned image.
            Bitmap source=Bitmap.createBitmap(4096,2048,Bitmap.Config.ARGB_8888);Canvas canvas=new Canvas(source);canvas.drawColor(0x00000000);Paint paint=new Paint();paint.setColor(Color.RED);canvas.drawRect(0,0,2048,2048,paint);File temp=new File(c.getCacheDir(),"qa-source.png");try(FileOutputStream s=new FileOutputStream(temp)){source.compress(Bitmap.CompressFormat.PNG,100,s);}source.recycle();
            SceneSettings.importImage(c,"qa-private",true,android.net.Uri.fromFile(temp));Bitmap imported=SceneSettings.image(c,"qa-private",true);boolean ok=imported!=null&&imported.getWidth()<=2048&&imported.getHeight()<=2048&&(imported.getPixel(imported.getWidth()-1,0)>>>24)==0;results.put(new JSONObject().put("test","import bounds and transparent foreground").put("ok",ok));if(!ok)failed++;if(imported!=null)imported.recycle();
            JSONObject sample=new JSONObject().put("id","qa-private").put("renderer","photo").put("assetRoot","");Bitmap rendered=Bitmap.createBitmap(696,604,Bitmap.Config.ARGB_8888);renderer.draw(new Canvas(rendered),696,604,sample,1791026640123L,10000);boolean alpha=rendered.getPixel(0,0)==Color.RED&&rendered.getPixel(695,0)!=Color.RED;results.put(new JSONObject().put("test","transparent layer renders over composition").put("ok",alpha));if(!alpha)failed++;rendered.recycle();renderer.release();
            Bitmap jpeg=Bitmap.createBitmap(300,160,Bitmap.Config.ARGB_8888);jpeg.eraseColor(Color.GREEN);File rotatedFile=new File(c.getCacheDir(),"qa-rotated.jpg");try(FileOutputStream stream=new FileOutputStream(rotatedFile)){jpeg.compress(Bitmap.CompressFormat.JPEG,90,stream);}jpeg.recycle();android.media.ExifInterface exif=new android.media.ExifInterface(rotatedFile.getPath());exif.setAttribute(android.media.ExifInterface.TAG_ORIENTATION,"6");exif.saveAttributes();SceneSettings.importImage(c,"qa-private",false,android.net.Uri.fromFile(rotatedFile));Bitmap rotated=SceneSettings.image(c,"qa-private",false);boolean oriented=rotated!=null&&rotated.getWidth()==160&&rotated.getHeight()==300;results.put(new JSONObject().put("test","JPEG EXIF rotation before crop").put("ok",oriented));if(!oriented)failed++;if(rotated!=null)rotated.recycle();rotatedFile.delete();
            SceneSettings.clearImages(c,"qa-private");boolean cleared=!SceneSettings.imageFile(c,"qa-private",true).exists();results.put(new JSONObject().put("test","remove private image").put("ok",cleared));if(!cleared)failed++;temp.delete();
        }catch(Throwable e){failed++;try{report.put("fatal",e.toString());}catch(Exception ignored){}}finally{renderer.release();}
        try{report.put("apkSha256",Qa.binarySha(c)).put("tested",results.length()).put("failed",failed).put("decodedOriginalImages",decoded).put("validCompiledNinePatches",patches).put("results",results);Pets.write(c,"composition-qa.json",report.toString(2));}catch(Exception ignored){}
    }
    static int decodeAssets(Context c,String path)throws Exception{int count=0;for(String name:c.getAssets().list(path)){String child=path+name;if(name.endsWith(".png")||name.endsWith(".webp")){try(InputStream s=c.getAssets().open(child)){Bitmap b=BitmapFactory.decodeStream(s);if(b==null)throw new IOException("Unreadable image: "+child);if(name.endsWith(".9.png")){byte[] chunk=b.getNinePatchChunk();if(chunk==null||!NinePatch.isNinePatchChunk(chunk))throw new IOException("Invalid original nine-patch: "+child);patches++;}b.recycle();count++;}}else if(!name.contains("."))count+=decodeAssets(c,child+"/");}return count;}
}
