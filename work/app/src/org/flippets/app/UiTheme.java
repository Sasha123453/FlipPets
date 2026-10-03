package org.flippets.app;

import android.app.Activity;
import android.content.Context;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.os.Build;
import android.view.View;
import android.view.Window;
import android.widget.*;

/** Material You color roles, using the system tonal palette without extra libraries. */
final class UiTheme {
    final Context context;
    final boolean dark;
    final int background,surface,container,text,secondary,primary,onPrimary,accent,onAccent,outline;
    UiTheme(Context c){
        context=c;dark=(c.getResources().getConfiguration().uiMode&Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES;
        background=color(dark?"system_neutral1_900":"system_neutral1_10",dark?0xff151218:0xfffff7ff);
        surface=color(dark?"system_neutral1_800":"system_neutral1_50",dark?0xff211e26:0xfff5eff7);
        container=color(dark?"system_neutral2_700":"system_neutral2_100",dark?0xff39333f:0xffe9e0ed);
        text=color(dark?"system_neutral1_50":"system_neutral1_900",dark?0xffe9e0e9:0xff201a24);
        secondary=color(dark?"system_neutral2_200":"system_neutral2_700",dark?0xffcdc2d3:0xff514658);
        primary=color(dark?"system_accent1_200":"system_accent1_600",dark?0xffd7baff:0xff7044a1);
        onPrimary=color(dark?"system_accent1_800":"system_accent1_0",dark?0xff40116b:0xffffffff);
        accent=color(dark?"system_accent1_700":"system_accent1_100",dark?0xff583183:0xffefdcff);
        onAccent=color(dark?"system_accent1_100":"system_accent1_900",dark?0xffefdcff:0xff29004a);
        outline=color(dark?"system_neutral2_500":"system_neutral2_400",dark?0xff96879e:0xff998ca1);
    }
    private int color(String name,int fallback){if(Build.VERSION.SDK_INT>=31){int id=context.getResources().getIdentifier(name,"color","android");if(id!=0)return context.getColor(id);}return fallback;}
    int dp(float n){return Math.round(n*context.getResources().getDisplayMetrics().density);}
    void window(Window w){w.setStatusBarColor(background);w.setNavigationBarColor(background);int flags=w.getDecorView().getSystemUiVisibility();int light=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;w.getDecorView().setSystemUiVisibility(dark?flags&~light:flags|light);}
    GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
    void card(View v,int color,int radius){v.setBackground(shape(color,radius));v.setClipToOutline(true);}
    TextView label(String value,int sp,boolean muted){TextView t=new TextView(context);t.setText(value);t.setTextSize(sp);t.setTextColor(muted?secondary:text);t.setFontFeatureSettings("kern");return t;}
    void style(Button b,boolean filled){b.setAllCaps(false);b.setTextSize(15);b.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));b.setTextColor(filled?onPrimary:onAccent);b.setMinHeight(dp(52));b.setMinimumHeight(dp(52));b.setPadding(dp(18),dp(12),dp(18),dp(12));b.setGravity(android.view.Gravity.CENTER);b.setBackground(new RippleDrawable(ColorStateList.valueOf(dark?0x33ffffff:0x22000000),shape(filled?primary:accent,28),null));b.setStateListAnimator(null);}
    Button button(String title,boolean filled,View.OnClickListener click){Button b=new Button(context);style(b,filled);b.setText(title);b.setOnClickListener(click);return b;}
    void chip(Button b,boolean selected){style(b,false);b.setTextColor(selected?onAccent:secondary);b.setBackground(new RippleDrawable(ColorStateList.valueOf(dark?0x33ffffff:0x22000000),shape(selected?accent:surface,24),null));b.setSelected(selected);}
    LinearLayout.LayoutParams spaced(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(8);return p;}
    void field(EditText e){e.setTextColor(text);e.setHintTextColor(secondary);e.setTextSize(16);e.setMinHeight(dp(56));e.setPadding(dp(18),dp(12),dp(18),dp(12));e.setBackground(shape(surface,24));e.setBackgroundTintList(null);}
    void toggle(Switch s){s.setTextColor(text);s.setTextSize(15);s.setMinHeight(dp(56));s.setPadding(dp(4),dp(8),dp(4),dp(8));s.setThumbTintList(new ColorStateList(new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},new int[]{primary,secondary}));s.setTrackTintList(new ColorStateList(new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},new int[]{accent,container}));s.setSwitchPadding(dp(16));}
}
