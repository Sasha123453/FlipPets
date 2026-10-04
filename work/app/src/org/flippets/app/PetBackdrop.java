package org.flippets.app;

import android.content.Context;
import android.graphics.*;
import android.view.View;
import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.*;

/** Xiaomi's original clock digits behind the animated character, adapted to the cover aspect ratio. */
public final class PetBackdrop extends View {
    Bitmap[] digits=new Bitmap[10];Bitmap[][] desk=new Bitmap[4][10];Bitmap bg;String loaded="";Paint paint=new Paint(3);Typeface font;int cameraRight;final boolean clock;boolean clockLoaded;PetLayoutProfile layoutDraft;
    BitmapShader sceneShader;final Paint scenePaint=new Paint(3),skyPaint=new Paint(3);final Matrix sceneMatrix=new Matrix();int sourceWidth,sourceHeight;float sceneScale,sceneX,sceneY;
    public PetBackdrop(Context c,boolean clock){super(c);this.clock=clock;setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);}
    void releaseClock(){for(int i=0;i<10;i++){if(digits[i]!=null)digits[i].recycle();digits[i]=null;}for(int i=0;i<4;i++)for(int j=0;j<10;j++){if(desk[i][j]!=null)desk[i][j].recycle();desk[i][j]=null;}font=null;clockLoaded=false;}
    void release(){releaseClock();sceneShader=null;scenePaint.setShader(null);if(bg!=null)bg.recycle();bg=null;loaded="";}
    boolean clockEnabled(){return clock&&!(layoutDraft!=null?layoutDraft:PetLayout.read(getContext(),Pets.current(getContext()))).clockless;}
    void sceneTransform(int width,int height,float scale,float x,float y){if(sourceWidth==width&&sourceHeight==height&&sceneScale==scale&&sceneX==x&&sceneY==y)return;sourceWidth=width;sourceHeight=height;sceneScale=scale;sceneX=x;sceneY=y;updateSceneShader();invalidate();}
    void updateSceneShader(){if(bg==null||sourceWidth<=0||sourceHeight<=0||sceneScale<=0){scenePaint.setShader(null);return;}if(sceneShader==null)sceneShader=new BitmapShader(bg,Shader.TileMode.CLAMP,Shader.TileMode.CLAMP);sceneMatrix.setScale(sceneScale*sourceWidth/bg.getWidth(),sceneScale*sourceHeight/bg.getHeight());sceneMatrix.postTranslate(sceneX,sceneY);sceneShader.setLocalMatrix(sceneMatrix);float top=Math.max(0,sceneY);Shader fade=new LinearGradient(0,top,0,top+48,new int[]{0x00000000,0xff000000},null,Shader.TileMode.CLAMP);scenePaint.setShader(new ComposeShader(sceneShader,fade,PorterDuff.Mode.DST_IN));int sky1=bg.getPixel(bg.getWidth()/2,Math.min(bg.getHeight()-1,Math.round(bg.getHeight()*.20f))),sky2=bg.getPixel(bg.getWidth()/2,Math.min(bg.getHeight()-1,Math.round(bg.getHeight()*.40f)));skyPaint.setShader(new LinearGradient(0,0,0,Math.max(1,top+48),sky1,sky2,Shader.TileMode.CLAMP));}
    void load(){JSONObject pet=Pets.current(getContext());String id=pet.optString("id");
        if(!id.equals(loaded)){release();loaded=id;for(String name:new String[]{"bg.webp","bg.png"})try(java.io.InputStream s=getContext().getAssets().open("pets/"+id+"/"+name)){bg=BitmapFactory.decodeStream(s);break;}catch(Exception ignored){}updateSceneShader();}
        if(!clockEnabled()){if(clockLoaded)releaseClock();return;}if(clockLoaded)return;clockLoaded=true;
        for(int i=0;i<10;i++)try(java.io.InputStream stream=getContext().getAssets().open("pets/"+id+"/temp_"+i+".png")){digits[i]=BitmapFactory.decodeStream(stream);}catch(Exception ignored){}
        try{font=Typeface.createFromAsset(getContext().getAssets(),"pets/"+id+"/c700_regular.ttf");}catch(Exception e){font=Typeface.DEFAULT;}
        String[] slots={"hour_0","hour_1","minute_0","minute_1"};for(int i=0;i<4;i++)for(int j=0;j<10;j++)try(java.io.InputStream s=getContext().getAssets().open("pets/"+id+"/desk/"+slots[i]+"/temp_"+j+".png")){desk[i][j]=BitmapFactory.decodeStream(s);}catch(Exception ignored){}
    }
    protected void onDraw(Canvas canvas){super.onDraw(canvas);load();float w=getWidth(),h=getHeight();
        if(bg!=null&&!(Pets.current(getContext()).optString("name").equals("Flowing glitter")&&SceneSettings.imageFile(getContext(),Pets.current(getContext()).optString("id"),false).exists())){if(scenePaint.getShader()!=null){canvas.drawRect(0,0,w,h,skyPaint);canvas.drawRect(0,0,w,h,scenePaint);}else canvas.drawBitmap(bg,null,new RectF(0,0,w,h),paint);}if(!clockEnabled())return;String time=new SimpleDateFormat("HHmm",Locale.US).format(new Date());
        float left=Math.max(w*.31f,cameraRight+16);float available=w-left-16;
        if(desk[0][0]!=null){float sr=Math.min(w/336f,(w-cameraRight-24)/125f),x=w-123*sr,y=6*sr;float[] xs={0,39,39,73},ys={0,4,48,48};for(int i=0;i<4;i++){Bitmap b=desk[i][time.charAt(i)-'0'];if(b!=null)canvas.drawBitmap(b,null,new RectF(x+xs[i]*sr,y+ys[i]*sr,x+(xs[i]+44)*sr,y+(ys[i]+52)*sr),paint);}return;}
        if(digits[0]!=null){float digitW=Math.min(56*h/213*.97f,available/4);float digitH=Math.min(189*h/213*.97f,h*.9f);float x=left+(available-digitW*4)/2,y=(h-digitH)/2;
            for(int i=0;i<4;i++){Bitmap b=digits[time.charAt(i)-'0'];if(b!=null)canvas.drawBitmap(b,null,new RectF(x+i*digitW,y,x+(i+1)*digitW,y+digitH),paint);}
        }else{paint.setTypeface(font);paint.setColor(parse(Pets.current(getContext()).optString("timeColor","#DBFF5A")));paint.setTextSize(Math.min(available/3.4f,h*.32f));paint.setTextAlign(Paint.Align.CENTER);canvas.drawText(time.substring(0,2)+":"+time.substring(2),left+available/2,h*.29f,paint);}
    }
    int parse(String color){try{return Color.parseColor(color);}catch(Exception e){return Color.WHITE;}}
}
