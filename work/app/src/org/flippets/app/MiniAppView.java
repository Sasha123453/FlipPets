package org.flippets.app;
import android.content.*;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Original public Xiaomi Canvas cards, offline and without a native JavaScript bridge. */
final class MiniAppView extends FrameLayout {
    interface Navigation{void select(String id);}
    final LinearLayout tabs;final TextView note;final boolean nativeLaunch;boolean preview;Insets safe=Insets.NONE;
    WebView web;String mode="focus",loaded="",qaOrigin="";boolean active,ready;int cameraRight;volatile int canvasHeight=Math.round(976f*CoverGeometry.HEIGHT/CoverGeometry.WIDTH);
    MiniAppView(Context c,boolean cover,Navigation navigation){
        this(c,cover,navigation,false);
    }
    MiniAppView(Context c,boolean cover,Navigation navigation,boolean nativeLaunch){
        super(c);this.nativeLaunch=nativeLaunch;preview=!cover;setBackgroundColor(Color.BLACK);tabs=new LinearLayout(c);String[] ids={"focus","water","words"},names={"Фокус","Вода","Слова"};UiTheme ui=new UiTheme(c);
        for(int i=0;i<ids.length;i++){final String id=ids[i];Button b=ui.button(names[i],false,v->navigation.select(id));b.setTag(id);b.setTextSize(12);b.setPadding(dp(3),dp(6),dp(3),dp(6));b.setMinimumWidth(0);b.setMinWidth(0);b.setContentDescription("Карточка Xiaomi: "+names[i]);LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,-2,1);if(i>0)bp.leftMargin=dp(4);tabs.addView(b,bp);}addView(tabs,new LayoutParams(-1,-2,Gravity.TOP));
        note=new TextView(c);note.setText("Оригинальная карточка Xiaomi · 中文");note.setTextColor(0xffaab4c6);note.setTextSize(11);note.setGravity(Gravity.CENTER);note.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);addView(note,new LayoutParams(-1,-2,Gravity.BOTTOM));if(preview){tabs.setVisibility(GONE);note.setVisibility(GONE);}
    }
    int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    void preview(boolean value){if(preview==value)return;preview=value;tabs.setVisibility(value?GONE:VISIBLE);note.setVisibility(value?GONE:VISIBLE);if(active)load();}
    void camera(int right){if(cameraRight!=right){cameraRight=right;requestLayout();}}
    void safeInsets(Insets value){safe=value;requestLayout();}
    void show(String id){if(!MiniAppStore.valid(id))id="focus";mode=id;for(int i=0;i<tabs.getChildCount();i++){Button b=(Button)tabs.getChildAt(i);boolean selected=id.equals(b.getTag());b.setSelected(selected);b.setTextColor(selected?Color.WHITE:0xffb8bfd0);android.graphics.drawable.GradientDrawable bg=new android.graphics.drawable.GradientDrawable();bg.setCornerRadius(dp(24));bg.setColor(selected?0xff344964:0xff17202e);b.setBackground(bg);}if(active&&!loaded.equals(id))load();}
    void start(){if(active)return;active=true;if(!nativeLaunch||getWidth()>0&&getHeight()>0)load();}
    void load(){
        release();if(!active||nativeLaunch&&(getWidth()==0||getHeight()==0))return;ready=false;loaded=mode;final int responseHeight=canvasHeight;final String origin=preview?"preview.flippets.invalid":!qaOrigin.isEmpty()?qaOrigin:nativeLaunch?"native-cards.flippets.invalid":"cards.flippets.invalid";
        web=new WebView(getContext());web.setBackgroundColor(Color.BLACK);WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(!preview);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setAllowFileAccessFromFileURLs(false);s.setAllowUniversalAccessFromFileURLs(false);s.setBlockNetworkLoads(true);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);s.setGeolocationEnabled(false);s.setMediaPlaybackRequiresUserGesture(true);s.setSupportMultipleWindows(false);s.setSaveFormData(false);
        web.setWebChromeClient(new WebChromeClient(){public void onPermissionRequest(PermissionRequest request){request.deny();}});
        web.setWebViewClient(new WebViewClient(){
            public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest request){return true;}
            public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest request){Uri u=request.getUrl();String path=u.getPath();if(!"https".equals(u.getScheme())||!origin.equals(u.getHost())||!("/1.html".equals(path)||"/3.html".equals(path)||"/5.html".equals(path)))return denied();
                try(InputStream in=getContext().getAssets().open("miniapps/xiaomi"+path)){ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] b=new byte[8192];for(int n;(n=in.read(b))>0;)bytes.write(b,0,n);String html=new String(bytes.toByteArray(),StandardCharsets.UTF_8);
                    String meta="<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,maximum-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'\">";
                    html=html.replace("<meta charset=\"utf-8\">","<meta charset=\"utf-8\">"+meta);
                    // Supply the original scripts' responsive viewport contract before they run.
                    // Only the host response changes; bundled Xiaomi HTML remains byte-identical.
                    String viewport="<script>window.CANVAS_W=976;window.CANVAS_H="+responseHeight+";var canvas=document.getElementById('c');canvas.width=CANVAS_W;canvas.height=CANVAS_H;</script>";
                    html=html.replace("<canvas id=\"c\" width=\"976\" height=\"596\"></canvas>","<canvas id=\"c\" width=\"976\" height=\"596\"></canvas>"+viewport);
                    Map<String,String> headers=new HashMap<>();headers.put("Cache-Control","no-store");return new WebResourceResponse("text/html","UTF-8",200,"OK",headers,new ByteArrayInputStream(html.getBytes(StandardCharsets.UTF_8)));
                }catch(IOException e){return denied();}}
            public void onPageFinished(WebView v,String url){if(v==web&&active&&url.startsWith("https://"+origin+"/"))ready=true;}
        });addView(web,0,new LayoutParams(-1,-1));web.loadUrl("https://"+origin+"/"+MiniAppStore.sourceId(mode)+".html");requestLayout();
    }
    static WebResourceResponse denied(){return new WebResourceResponse("text/plain","UTF-8",403,"Blocked",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));}
    void release(){ready=false;if(web!=null){WebView old=web;web=null;old.stopLoading();old.onPause();removeView(old);old.loadUrl("about:blank");old.destroy();}loaded="";}
    void stop(){active=false;release();}
    protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);if(nativeLaunch&&active&&web==null)post(()->{if(active&&web==null)load();});else if(active&&web!=null&&oldw>0&&oldh>0&&(long)w*oldh!=(long)oldw*h){ready=false;post(()->{if(active)load();});}}
    int controlsLeft(int width){return preview?0:nativeLaunch?safe.left:Math.max(cameraRight,Math.round(width*.34f));}
    protected void onMeasure(int w,int h){int width=MeasureSpec.getSize(w),height=preview&&MeasureSpec.getMode(h)!=MeasureSpec.EXACTLY?resolveSize(Math.round(width*CoverGeometry.HEIGHT/(float)CoverGeometry.WIDTH),h):MeasureSpec.getSize(h);setMeasuredDimension(width,height);canvasHeight=Math.max(1,Math.round(976f*height/Math.max(1,width)));int cardH=height;if(web!=null)web.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(cardH,MeasureSpec.EXACTLY));int left=controlsLeft(width),right=nativeLaunch?safe.right:0;tabs.measure(MeasureSpec.makeMeasureSpec(Math.max(1,width-left-right-dp(20)),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.AT_MOST));note.measure(MeasureSpec.makeMeasureSpec(Math.max(1,width-left-right),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.AT_MOST));}
    protected void onLayout(boolean changed,int l,int t,int r,int b){int width=r-l,height=b-t,left=controlsLeft(width),right=nativeLaunch?safe.right:0,top=dp(16)+(nativeLaunch?safe.top:0),bottom=height-dp(14)-(nativeLaunch?safe.bottom:0);if(web!=null){web.layout(0,0,width,height);}tabs.layout(left+dp(10),top,Math.max(left+dp(10)+1,width-right-dp(10)),top+tabs.getMeasuredHeight());note.layout(left,bottom-note.getMeasuredHeight(),Math.max(left+1,width-right),bottom);}
}
