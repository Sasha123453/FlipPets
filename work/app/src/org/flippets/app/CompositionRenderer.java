package org.flippets.app;

import android.content.*;
import android.graphics.*;
import org.json.JSONObject;
import java.util.*;
import java.text.SimpleDateFormat;

/** Offline adaptation of MAML compositions; original images, local data and settings. */
public final class CompositionRenderer {
    final Context context;final Paint paint=new Paint(3);
    final LinkedHashMap<String,Bitmap> images=new LinkedHashMap<>(32,.75f,true);
    final Map<String,Typeface> fonts=new HashMap<>();
    String id="",root="";long revision=-1;Bitmap photo,front;
    int cameraRight;
    float touchX=.6f,touchY=.5f;long touchTime;
    public CompositionRenderer(Context c){context=c;}
    public void touch(float x,float y,long time){touchX=Math.max(0,Math.min(1,x));touchY=Math.max(0,Math.min(1,y));touchTime=time;}
    public void release(){for(Bitmap b:images.values())if(b!=null)b.recycle();images.clear();if(photo!=null)photo.recycle();if(front!=null)front.recycle();photo=front=null;id="";revision=-1;}
    void select(JSONObject pet){String next=pet.optString("id");if(!next.equals(id)){release();id=next;root=pet.optString("assetRoot");}long v=SceneSettings.prefs(context,id).getLong("imageRevision",0);if(v!=revision){if(photo!=null)photo.recycle();if(front!=null)front.recycle();photo=SceneSettings.image(context,id,false);front=SceneSettings.image(context,id,true);revision=v;}}
    Bitmap image(String path){if(images.containsKey(path))return images.get(path);Bitmap b=null;try(java.io.InputStream s=context.getAssets().open(root+path)){b=BitmapFactory.decodeStream(s);}catch(Exception ignored){}images.put(path,b);if(images.size()>32){String key=images.keySet().iterator().next();Bitmap old=images.remove(key);if(old!=null)old.recycle();}return b;}
    Typeface font(int which){String[] f={"MiSansVF.ttf","Qinghe.otf","Coca-ColaCareFontKaiTi.TTF","FZFWZhuZiAYuanJWB.TTF","MiSansRoundedSC.ttf"};String key=f[Math.max(0,Math.min(4,which))];if(!fonts.containsKey(key)){try{fonts.put(key,Typeface.createFromAsset(context.getAssets(),"fonts/"+key));}catch(Exception e){fonts.put(key,Typeface.DEFAULT);}}return fonts.get(key);}
    static int color(String text,int fallback){try{return Color.parseColor(text);}catch(Exception e){return fallback;}}
    void bitmap(Canvas c,Bitmap b,float l,float t,float r,float bottom){if(b!=null){paint.setShader(null);paint.setColor(Color.WHITE);paint.setAlpha(255);c.drawBitmap(b,null,new RectF(l,t,r,bottom),paint);}}
    void text(Canvas c,String value,float x,float y,float size,int col,Paint.Align align){paint.setShader(null);paint.setColor(col);paint.setTextSize(size);paint.setTextAlign(align);c.drawText(value,x,y,paint);}
    static String clock(Calendar date){return String.format(Locale.US,"%02d:%02d",date.get(Calendar.HOUR_OF_DAY),date.get(Calendar.MINUTE));}
    public void draw(Canvas c,int width,int height,JSONObject pet,long wallTime,long elapsed){
        select(pet);SharedPreferences pref=SceneSettings.prefs(context,id);Calendar date=Calendar.getInstance();date.setTimeInMillis(wallTime);
        String type=pet.optString("renderer");int bg=color(pref.getString("background","#182432"),0xff182432),fg=color(pref.getString("textColor","#F4EDE4"),0xfff4ede4);
        c.drawColor(bg);paint.setTypeface(font(pref.getInt("font",0)));
        if(photo!=null)drawPhoto(c,photo,width,height,pref.getFloat("zoom",1),pref.getFloat("panX",.5f),pref.getFloat("panY",.5f));
        String tone=pref.getString("color",pet.optString("defaultColor","blue"));
        boolean dark=pref.getBoolean("dim",false);
        if(type.equals("analog")&&photo==null)bitmap(c,image("assets/"+tone+"/bg.png"),0,0,width,height);
        if(type.equals("paper")&&photo==null){Bitmap paper=image("assets/bg/bg.png");if(paper!=null)drawPhoto(c,paper,width,height,1,.72f,.5f);}
        // Fit the original wide design into the cover, preserving space for the left cameras.
        float safe=Math.max(width*pref.getFloat("safeCamera",.34f),cameraRight+12);
        float scale=SceneGeometry.scale(width,height,safe),offsetY=SceneGeometry.y(height,scale);
        c.save();c.translate(SceneGeometry.x(width,scale),offsetY);c.scale(scale,scale);
        if(type.equals("analog"))analog(c,tone,date,wallTime,dark);
        else if(type.equals("dragon"))dragon(c,date,wallTime,dark);
        else if(type.equals("stretch"))stretch(c,tone,date,pref,elapsed);
        else if(type.equals("steps"))steps(c,date,elapsed,pref,fg);
        else if(type.equals("calendar"))calendar(c,date,pref,fg);
        else{
            if(type.equals("photo")){if(photo==null){paint.setColor(0xff31495d);c.drawRoundRect(new RectF(360,140,925,450),35,35,paint);text(c,"Выбери фотографию",642,295,38,fg,Paint.Align.CENTER);}text(c,clock(date),908,90,60,fg,Paint.Align.RIGHT);}
            else signature(c,date,pref,fg,type.equals("paper"));
        }
        c.restore();
        if(front!=null)drawPhoto(c,front,width,height,pref.getFloat("zoom",1),pref.getFloat("panX",.5f),pref.getFloat("panY",.5f));
        if(dark){paint.setColor(0x55000000);c.drawRect(0,0,width,height,paint);}
    }
    public static void drawPhoto(Canvas c,Bitmap b,int w,int h,float zoom,float px,float py){
        float s=Math.max(w/(float)b.getWidth(),h/(float)b.getHeight())*Math.max(1,Math.min(3,zoom));float bw=b.getWidth()*s,bh=b.getHeight()*s;
        Paint p=new Paint(3);c.drawBitmap(b,null,new RectF(-(bw-w)*Math.max(0,Math.min(1,px)),-(bh-h)*Math.max(0,Math.min(1,py)),w+(bw-w)*(1-Math.max(0,Math.min(1,px))),h+(bh-h)*(1-Math.max(0,Math.min(1,py)))),p);
    }
    void rotated(Canvas c,Bitmap b,float cx,float cy,float w,float h,float pivotY,float angle){if(b==null)return;c.save();c.rotate(angle,cx,cy);bitmap(c,b,cx-w/2,cy-pivotY,cx+w/2,cy-pivotY+h);c.restore();}
    void analog(Canvas c,String tone,Calendar d,long time,boolean dim){
        float cx=657,cy=298,s=1.04f;double sec=d.get(Calendar.SECOND)+(time%1000)/1000.0;float minute=(float)(d.get(Calendar.MINUTE)*6+sec*.1),hour=(float)((d.get(Calendar.HOUR)%12)*30+d.get(Calendar.MINUTE)*.5+sec/120);
        String path="assets/"+tone+"/";
        rotated(c,image(path+(dim?"second_ball_aod.png":"second_light_ball.png")),cx,cy,dim?518*s:1230*s,dim?518*s:1230*s,(dim?259:615)*s,(float)sec*6);
        rotated(c,image(path+(dim?"hour_aod.png":"hour.png")),cx,cy,26*s,164*s,193*s,hour);
        rotated(c,image(path+(dim?"minute_aod.png":"minute.png")),cx,cy,8*s,212*s,241*s,minute);
        bitmap(c,image(path+(dim?"center_aod.png":"center.png")),cx-13*s,cy-13*s,cx+13*s,cy+13*s);
        int col=color(tone.equals("green")?"#7AFFD3":tone.equals("purple")?"#E4D5FF":tone.equals("red")?"#FFCFCC":tone.equals("orange")?"#FFE5CC":"#ADE4FF",Color.WHITE);
        paint.setTypeface(font(4));String digits=clock(d);float[] angles={-10,-5,0,5,10};c.save();c.rotate(minute,cx,cy);
        for(int i=0;i<5;i++){c.save();c.rotate(angles[i],cx,cy);text(c,digits.substring(i,i+1),cx,cy-268,42,col,Paint.Align.CENTER);c.restore();}c.restore();
    }
    void dragon(Canvas c,Calendar d,long time,boolean dim){
        float cx=704,cy=298,s=2.35f;bitmap(c,image("assets/black/bg_p2.png"),cx-768*.86f,cy-333*.86f,cx+(1089-768)*.86f,cy+333*.86f);
        double sec=d.get(Calendar.SECOND)+(time%1000)/1000.;float hour=(float)(d.get(Calendar.HOUR)*30+d.get(Calendar.MINUTE)*.5+sec/120),minute=(float)(d.get(Calendar.MINUTE)*6+sec*.1);
        String p="assets/pointer/"+(dim?"aod":"normal")+"/";
        for(int i=0;i<2;i++){float a=i==0?hour:minute;String n=i==0?"hour":"minute";float w=(i==0?15:13)*s;
            rotated(c,image(p+n+"_shadow.png"),cx,cy+6*s,w,212*s,106*s,a);rotated(c,image(p+n+(a<=180?"_right.png":"_left.png")),cx,cy,w,212*s,106*s,a);
        }
        if(!dim)rotated(c,image("assets/black/second"+(sec*6<=180?"_right.png":"_left.png")),cx,cy,16*s,212*s,106*s,(float)sec*6);
        bitmap(c,image(p+"center.png"),cx-2*s,cy-2*s,cx+2*s,cy+2*s);
        Bitmap month=image("assets/month/"+(d.get(Calendar.MONTH)+1)+".png");if(month!=null)bitmap(c,month,cx-month.getWidth()*.45f,cy-102,cx+month.getWidth()*.45f,cy-102+month.getHeight()*.9f);
        int day=d.get(Calendar.DAY_OF_MONTH);if(day>9)bitmap(c,image("assets/black/date/"+day/10+".png"),cx-20,cy+85,cx,cy+137);bitmap(c,image("assets/black/date/"+day%10+".png"),cx,cy+85,cx+20,cy+137);
    }
    void stretch(Canvas c,String tone,Calendar d,SharedPreferences p,long elapsed){
        String time=clock(d).replace(":","");boolean stacked=p.getInt("layout",0)==0;
        float age=(elapsed-touchTime)/1000f;float pulse=touchTime>0&&age>=0&&age<2?(float)(Math.exp(-3*age)*Math.cos(age*13))*(touchY-.5f)*.7f:0;
        for(int i=0;i<4;i++){
            float l,t,r,b;if(stacked){l=364+(i%2)*276;r=l+240;t=i<2?48:316;b=i<2?282+pulse*240:548-pulse*240;}
            else{l=332+i*154;r=l+140;t=72+pulse*120*(i%2==0?1:-1);b=528-pulse*120*(i%2==0?1:-1);}
            patch(c,image("assets/light/nine_path/"+tone+"/"+(i<2?"hour/":"minute/")+time.charAt(i)+".9.png"),new RectF(l,t,r,b));
        }
    }
    /** Draw raw .9.png stretch markers without displaying its one-pixel border. */
    void patch(Canvas c,Bitmap b,RectF dst){if(b==null)return;paint.setShader(null);paint.setColor(Color.WHITE);byte[] chunk=b.getNinePatchChunk();if(chunk!=null&&NinePatch.isNinePatchChunk(chunk)){new NinePatch(b,chunk,"Xiaomi clock").draw(c,new Rect(Math.round(dst.left),Math.round(dst.top),Math.round(dst.right),Math.round(dst.bottom)),paint);return;}int w=b.getWidth(),h=b.getHeight();int[] x=markers(b,true),y=markers(b,false);
        float s=Math.min(dst.width()/(w-2),dst.height()/(h-2));float[] dx={dst.left,dst.left+(x[1]-1)*s,dst.right-(w-1-x[2])*s,dst.right},dy={dst.top,dst.top+(y[1]-1)*s,dst.bottom-(h-1-y[2])*s,dst.bottom};
        for(int i=0;i<3;i++)for(int j=0;j<3;j++)if(dx[i+1]>dx[i]&&dy[j+1]>dy[j])c.drawBitmap(b,new Rect(x[i],y[j],x[i+1],y[j+1]),new RectF(dx[i],dy[j],dx[i+1],dy[j+1]),paint);
    }
    static int[] markers(Bitmap b,boolean horizontal){int size=horizontal?b.getWidth():b.getHeight(),first=-1,last=-1;for(int i=1;i<size-1;i++){int pixel=horizontal?b.getPixel(i,0):b.getPixel(0,i);if((pixel>>>24)>128&&(pixel&0xffffff)==0){if(first<0)first=i;last=i;}}return new int[]{1,first<0?size/3:first,last<0?size*2/3:last+1,size-1};}
    void steps(Canvas c,Calendar d,long elapsed,SharedPreferences pref,int fg){
        StepLedger s=StepStore.get(context);int goal=Math.max(100,pref.getInt("goal",8000));float ratio=Math.min(1,s.total/(float)goal);
        text(c,clock(d),914,125,74,fg,Paint.Align.RIGHT);text(c,new SimpleDateFormat("d MMM · EEE",Locale.getDefault()).format(d.getTime()),364,82,26,fg,Paint.Align.LEFT);
        text(c,Integer.toString(s.total),364,218,62,fg,Paint.Align.LEFT);text(c,"шагов / "+goal,364,256,23,fg,Paint.Align.LEFT);
        bitmap(c,image("assets/step_ani/frame_"+(elapsed/45%30)+".png"),866,184,922,240);
        int max=1;for(int n:s.hours)max=Math.max(max,n);
        for(int i=0;i<24;i++){float x=367+i*23;float bar=s.hours[i]==0?7:Math.max(12,120*s.hours[i]/(float)max);paint.setColor(s.hours[i]>0?0xffff753e:0xff603825);c.drawRoundRect(new RectF(x,412-bar,x+14,412),7,7,paint);}
        text(c,"00:00",364,445,20,fg,Paint.Align.LEFT);text(c,"12:00",640,445,20,fg,Paint.Align.CENTER);text(c,"24:00",924,445,20,fg,Paint.Align.RIGHT);
        paint.setColor(0xff603825);c.drawRoundRect(new RectF(364,478,924,494),8,8,paint);paint.setColor(0xffff753e);if(ratio>0)c.drawRoundRect(new RectF(364,478,364+560*ratio,494),8,8,paint);
        text(c,"Учтены приложением сегодня",364,538,23,fg,Paint.Align.LEFT);
    }
    void signature(Canvas c,Calendar d,SharedPreferences p,int fg,boolean paper){
        String value=p.getString("signature",paper?"С Новым годом!":"Хорошего дня");int layout=p.getInt("layout",0);float size=Math.max(24,Math.min(100,p.getInt("size",54)));paint.setTypeface(Typeface.create(font(p.getInt("font",paper?2:0)),p.getBoolean("bold",false)?Typeface.BOLD:Typeface.NORMAL));
        if(layout==3){String[] lines=value.split("\n");float y=126;for(String line:lines){StringBuilder chars=new StringBuilder();line.codePoints().limit(5).forEach(cp->chars.appendCodePoint(cp));for(int i=0;i<chars.length();){int cp=chars.codePointAt(i);text(c,new String(Character.toChars(cp)),662,y,size,fg,Paint.Align.CENTER);y+=size*1.05f;i+=Character.charCount(cp);}}}
        else{Paint.Align align=layout==1?Paint.Align.LEFT:layout==2?Paint.Align.RIGHT:Paint.Align.CENTER;float x=layout==1?374:layout==2?919:647;String[] lines=value.split("\n",-1);float y=286-Math.min(4,lines.length)*size*.52f;for(int i=0;i<Math.min(4,lines.length);i++){String line=lines[i];paint.setTextSize(size);float fit=Math.min(size,540*size/Math.max(1,paint.measureText(line)));text(c,line,x,y+i*size*1.12f,fit,fg,align);}}
        paint.setTypeface(font(4));text(c,clock(d),919,535,42,fg,Paint.Align.RIGHT);
    }
    void calendar(Canvas c,Calendar d,SharedPreferences p,int fg){
        // Douban's private provider is unavailable: use local title/caption/image only.
        paint.setColor(0xaa182432);c.drawRoundRect(new RectF(344,30,942,565),25,25,paint);
        text(c,new SimpleDateFormat("MMMM yyyy",Locale.getDefault()).format(d.getTime()),374,87,31,fg,Paint.Align.LEFT);text(c,Integer.toString(d.get(Calendar.DAY_OF_MONTH)),374,220,116,fg,Paint.Align.LEFT);
        text(c,new SimpleDateFormat("EEEE",Locale.getDefault()).format(d.getTime()),374,271,29,fg,Paint.Align.LEFT);
        String title=p.getString("signature","Мой кинокалендарь"),caption=p.getString("caption","Добавь постер и подпись в настройках");
        paint.setTextSize(36);text(c,title,374,349,Math.min(36,540*36/Math.max(1,paint.measureText(title))),fg,Paint.Align.LEFT);
        String[] lines=caption.split("\n");for(int i=0;i<Math.min(3,lines.length);i++){paint.setTextSize(25);text(c,lines[i],374,394+i*31,Math.min(25,540*25/Math.max(1,paint.measureText(lines[i]))),fg,Paint.Align.LEFT);}
        text(c,clock(d),910,534,39,fg,Paint.Align.RIGHT);
    }
}
