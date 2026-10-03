package org.flippets.app;

import android.content.*;
import android.graphics.*;
import android.net.Uri;
import java.io.*;

/** Private bounded copies of images selected through Android's document picker. */
public final class SceneSettings {
    public static SharedPreferences prefs(Context c,String id){return c.getSharedPreferences("scene-"+id,0);}
    static File imageFile(Context c,String id,boolean foreground){return new File(c.getFilesDir(),id+(foreground?"-front":"-photo")+".png");}
    public static Bitmap image(Context c,String id,boolean foreground){File f=imageFile(c,id,foreground);return f.exists()?BitmapFactory.decodeFile(f.getPath()):null;}
    public static void importImage(Context c,String id,boolean foreground,Uri uri)throws Exception{
        BitmapFactory.Options o=new BitmapFactory.Options();o.inJustDecodeBounds=true;
        try(InputStream s=c.getContentResolver().openInputStream(uri)){BitmapFactory.decodeStream(s,null,o);}
        if(o.outWidth<=0||o.outHeight<=0)throw new IOException("Файл не содержит изображение");
        o.inSampleSize=1;while(Math.max(o.outWidth,o.outHeight)/o.inSampleSize>2048)o.inSampleSize*=2;o.inJustDecodeBounds=false;
        Bitmap b;try(InputStream s=c.getContentResolver().openInputStream(uri)){b=BitmapFactory.decodeStream(s,null,o);}
        if(b==null)throw new IOException("Не удалось прочитать изображение");
        try{
            int orientation=1;try(InputStream s=c.getContentResolver().openInputStream(uri)){orientation=new android.media.ExifInterface(s).getAttributeInt(android.media.ExifInterface.TAG_ORIENTATION,1);}catch(Exception ignored){}
            Matrix m=new Matrix();switch(orientation){case 2:m.setScale(-1,1);break;case 3:m.setRotate(180);break;case 4:m.setScale(1,-1);break;case 5:m.setRotate(90);m.postScale(-1,1);break;case 6:m.setRotate(90);break;case 7:m.setRotate(-90);m.postScale(-1,1);break;case 8:m.setRotate(-90);break;}
            if(!m.isIdentity()){Bitmap rotated=Bitmap.createBitmap(b,0,0,b.getWidth(),b.getHeight(),m,true);if(rotated!=b){b.recycle();b=rotated;}}
            File target=imageFile(c,id,foreground);android.util.AtomicFile file=new android.util.AtomicFile(target);FileOutputStream stream=null;
            try{stream=file.startWrite();if(!b.compress(Bitmap.CompressFormat.PNG,100,stream))throw new IOException("Не удалось сохранить изображение");file.finishWrite(stream);}catch(Exception e){if(stream!=null)file.failWrite(stream);throw e;}
            SharedPreferences p=prefs(c,id);p.edit().putLong("imageRevision",p.getLong("imageRevision",0)+1).apply();Pets.signal(c);
        }finally{b.recycle();}
    }
    public static void clearImages(Context c,String id){for(boolean f:new boolean[]{false,true})new android.util.AtomicFile(imageFile(c,id,f)).delete();SharedPreferences p=prefs(c,id);p.edit().putLong("imageRevision",p.getLong("imageRevision",0)+1).apply();Pets.signal(c);}
}
