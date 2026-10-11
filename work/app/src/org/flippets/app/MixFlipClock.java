package org.flippets.app;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.format.DateFormat;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Stock TYPE_NORMAL TinyClock layout, measured before scaling the complete virtual cover. */
final class MixFlipClock {
    static final float DENSITY=3.25f;
    final Context context;
    final JSONObject data,dims;
    final Typeface digits;
    FrameLayout timeRoot,detailRoot;
    TextView[] numbers;
    TextView date,week;
    int rotation=-1,petType=-1;
    long minute=-1;
    String localeKey="",zoneKey="";boolean format24;
    MixFlipClock(Context c)throws Exception {
        context=c;
        try(java.io.InputStream in=c.getAssets().open("mixflip-clock.json")){
            java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();byte[] b=new byte[4096];int n;
            while((n=in.read(b))!=-1)out.write(b,0,n);
            data=new JSONObject(new String(out.toByteArray(),java.nio.charset.StandardCharsets.UTF_8));
        }
        dims=data.getJSONObject("dimensions");
        digits=Typeface.createFromAsset(c.getAssets(),"clock/mixflip/c700_regular.ttf");
    }
    float dimension(String name){return (float)dims.optDouble("tiny_pets_"+name)*DENSITY;}
    int px(String name){return (int)dimension(name);}
    TextView text(Typeface font,float size,int color){
        TextView t=new TextView(context);t.setTypeface(font);t.setTextSize(TypedValue.COMPLEX_UNIT_PX,size);t.setTextColor(color);
        t.setText("0");t.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);return t;
    }
    LinearLayout.LayoutParams margin(String start,String end){
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-2,-2);p.setMarginStart(px(start));if(end!=null)p.setMarginEnd(px(end));return p;
    }
    void build(int type,int rot)throws Exception {
        petType=type;rotation=rot;minute=-1;String prefix=rot==2?"180_":"";
        int color=Color.parseColor(data.getJSONArray("timeColors").getString(type-1));
        int colon=Color.parseColor(data.getJSONArray("colonColors").getString(type-1));
        timeRoot=new FrameLayout(context);timeRoot.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        LinearLayout row=new LinearLayout(context);row.setOrientation(LinearLayout.HORIZONTAL);row.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        FrameLayout.LayoutParams rp=new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.RIGHT);rp.topMargin=px(prefix+"time_container_margin_top");
        if(rot!=2)rp.setMarginEnd(px("time_container_margin_end"));timeRoot.addView(row,rp);
        numbers=new TextView[4];for(int i=0;i<4;i++)numbers[i]=text(digits,dimension(prefix+"time_text_size"),color);
        row.addView(numbers[0],margin(prefix+"hour1_margin_start",null));row.addView(numbers[1],margin(prefix+"hour2_margin_start",null));
        LinearLayout dots=new LinearLayout(context);dots.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams dp=new LinearLayout.LayoutParams(px(prefix+"colon_size"),-2);dp.setMarginStart(px(prefix+"colon_container_margin_start"));dp.topMargin=px(prefix+"colon_container_margin_top");row.addView(dots,dp);
        for(int i=0;i<2;i++){View dot=new View(context);GradientDrawable shape=new GradientDrawable();shape.setShape(GradientDrawable.OVAL);shape.setColor(colon);dot.setBackground(shape);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(px(prefix+"colon_size"),px(prefix+"colon_size"));if(i==1)p.topMargin=px(prefix+"colon_margin_top");dots.addView(dot,p);}
        row.addView(numbers[2],margin(prefix+"minute1_margin_start",null));row.addView(numbers[3],margin(prefix+"minute2_margin_start",prefix+"minute2_margin_end"));
        // PetsClockTopView is a separate layer above the animated subject.
        detailRoot=new FrameLayout(context);detailRoot.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        LinearLayout details=new LinearLayout(context);details.setOrientation(LinearLayout.VERTICAL);detailRoot.addView(details,new FrameLayout.LayoutParams(-1,-1));
        Typeface info=Typeface.create("mipro-heavy",Typeface.NORMAL);
        // The inspected EEA Russian/Latin font exists on MIX Flip. Match FontUtils' wght=700,
        // without depending on its hidden MultiLangHelper reflection in a third-party app.
        java.io.File latin=new java.io.File("/system/fonts/MiSansLatinVF.ttf");
        if(latin.isFile()&&latin.canRead())try{info=new Typeface.Builder(latin).setFontVariationSettings("'wght' 700").setWeight(700).build();}catch(RuntimeException ignored){}
        date=text(info,dimension(prefix+"date_text_size"),Color.WHITE);week=text(info,dimension(prefix+"date_text_size"),Color.WHITE);
        LinearLayout.LayoutParams day=new LinearLayout.LayoutParams(-2,-2);day.gravity=Gravity.RIGHT;day.topMargin=px(prefix+"date_margin_top");day.setMarginEnd(px(prefix+"date_margin_end"));details.addView(date,day);
        LinearLayout.LayoutParams weekday=new LinearLayout.LayoutParams(-2,-2);weekday.gravity=Gravity.RIGHT;weekday.topMargin=px(prefix+"week_margin_top");weekday.setMarginEnd(px(prefix+"week_margin_end"));details.addView(week,weekday);
    }
    void update(int type,int rot,long now)throws Exception {
        if(type!=petType||rot!=rotation)build(type,rot);
        Locale locale=context.getResources().getConfiguration().getLocales().get(0);String zone=java.util.TimeZone.getDefault().getID();boolean h24=DateFormat.is24HourFormat(context);
        if(minute==now/60000&&localeKey.equals(locale.toLanguageTag())&&zoneKey.equals(zone)&&format24==h24)return;
        minute=now/60000;localeKey=locale.toLanguageTag();zoneKey=zone;format24=h24;Date moment=new Date(now);
        String time=new SimpleDateFormat(h24?"HHmm":"hhmm",Locale.US).format(moment);
        for(int i=0;i<4;i++)numbers[i].setText(time.substring(i,i+1));
        String pattern=locale.getLanguage().equals("zh")&&locale.getCountry().equals("CN")?"M月d日":data.getString("dateFormat");
        date.setText(new SimpleDateFormat(pattern,locale).format(moment));week.setText(new SimpleDateFormat(data.getString("weekFormat"),locale).format(moment));
        for(FrameLayout root:new FrameLayout[]{timeRoot,detailRoot}){root.measure(View.MeasureSpec.makeMeasureSpec(1208,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(1392,View.MeasureSpec.EXACTLY));root.layout(0,0,1208,1392);}
    }
    void draw(Canvas canvas,int w,int h,int type,int rot,boolean details)throws Exception {
        update(type,rot,System.currentTimeMillis());float scale=Math.min(w/1208f,h/1392f);int save=canvas.save();canvas.translate((w-1208*scale)/2,(h-1392*scale)/2);canvas.scale(scale,scale);(details?detailRoot:timeRoot).draw(canvas);canvas.restoreToCount(save);
    }
}
