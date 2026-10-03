package org.flippets.app;

import android.content.*;
import android.content.res.Configuration;
import android.graphics.*;
import android.hardware.display.DisplayManager;
import android.os.Handler;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.view.*;
import android.widget.FrameLayout;

/** A scaled virtual cover: render dimensions/density stay identical to the actual panel. */
public final class CoverPreview extends FrameLayout implements DisplayManager.DisplayListener {
    public final PetStage stage;
    private final View cameras;
    private final DisplayManager displays;
    private int coverWidth=CoverGeometry.WIDTH,coverHeight=CoverGeometry.HEIGHT;
    private int cameraRight;
    public CoverPreview(Context context){
        super(context);displays=(DisplayManager)context.getSystemService(Context.DISPLAY_SERVICE);
        Configuration coverConfig=new Configuration(context.getResources().getConfiguration());coverConfig.densityDpi=CoverGeometry.DENSITY;
        stage=new PetStage(context.createConfigurationContext(coverConfig),true);stage.previewSurface=true;addView(stage);
        cameras=new View(context){final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);protected void onDraw(Canvas canvas){float w=getWidth(),h=getHeight();paint.setColor(0xee151519);float radius=w*.13f;canvas.drawCircle(w*.16f,h*.15f,radius,paint);canvas.drawCircle(w*.16f,h*.395f,radius,paint);paint.setColor(0xff494952);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(w*.003f);canvas.drawCircle(w*.16f,h*.15f,radius*.87f,paint);canvas.drawCircle(w*.16f,h*.395f,radius*.87f,paint);paint.setStyle(Paint.Style.FILL);}};
        cameras.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);addView(cameras);setClipChildren(true);refreshGeometry();
    }
    private void refreshGeometry(){
        int width=CoverGeometry.WIDTH,height=CoverGeometry.HEIGHT,inset=0;
        for(Display display:displays.getDisplays())if(display.getDisplayId()!=Display.DEFAULT_DISPLAY){
            Point size=new Point();display.getRealSize(size);
            if(Math.min(size.x,size.y)==CoverGeometry.WIDTH&&Math.max(size.x,size.y)==CoverGeometry.HEIGHT){width=size.x;height=size.y;DisplayCutout cutout=display.getCutout();if(cutout!=null)for(Rect rect:cutout.getBoundingRects())if(rect.left==0)inset=Math.max(inset,rect.right);break;}
        }
        boolean changed=width!=coverWidth||height!=coverHeight||inset!=cameraRight;coverWidth=width;coverHeight=height;cameraRight=inset;stage.previewCameraRight=inset;if(changed){stage.requestApplyInsets();stage.requestLayout();requestLayout();}
    }
    protected void onMeasure(int widthSpec,int heightSpec){
        int max=Math.round(300*getResources().getDisplayMetrics().density);
        int width=MeasureSpec.getMode(widthSpec)==MeasureSpec.UNSPECIFIED?max:Math.min(max,MeasureSpec.getSize(widthSpec));
        if(MeasureSpec.getMode(heightSpec)!=MeasureSpec.UNSPECIFIED)width=Math.min(width,Math.round(MeasureSpec.getSize(heightSpec)*(coverWidth/(float)coverHeight)));
        width=Math.max(1,width);int height=CoverGeometry.previewHeight(width,coverWidth,coverHeight);
        setMeasuredDimension(width,height);int w=MeasureSpec.makeMeasureSpec(coverWidth,MeasureSpec.EXACTLY),h=MeasureSpec.makeMeasureSpec(coverHeight,MeasureSpec.EXACTLY);stage.measure(w,h);cameras.measure(w,h);
    }
    protected void onLayout(boolean changed,int left,int top,int right,int bottom){
        float scale=getWidth()/(float)coverWidth;
        for(View child:new View[]{stage,cameras}){child.layout(0,0,coverWidth,coverHeight);child.setPivotX(0);child.setPivotY(0);child.setScaleX(scale);child.setScaleY(scale);}
    }
    protected void onAttachedToWindow(){super.onAttachedToWindow();displays.registerDisplayListener(this,new Handler(Looper.getMainLooper()));refreshGeometry();}
    protected void onDetachedFromWindow(){displays.unregisterDisplayListener(this);super.onDetachedFromWindow();}
    public void onDisplayAdded(int id){refreshGeometry();}public void onDisplayRemoved(int id){refreshGeometry();}public void onDisplayChanged(int id){refreshGeometry();}
}
