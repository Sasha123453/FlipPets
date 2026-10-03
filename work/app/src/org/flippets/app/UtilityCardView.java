package org.flippets.app;

import android.content.*;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.RippleDrawable;
import android.media.MediaMetadata;
import android.media.session.*;
import android.media.session.MediaController;
import android.os.*;
import android.text.TextUtils;
import android.view.*;
import android.widget.*;
import java.util.Locale;

/** Optional compact overlay. Event-driven battery/media, a visible-only timer tick. */
public final class UtilityCardView extends LinearLayout {
    private final UiTheme ui;
    private final boolean full;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final SharedPreferences prefs;
    private boolean active;
    private String mode="",stamp="";
    private TextView header,value,detail;
    private Button first,second,focus,stopwatch;
    private Intent battery;
    private int boundsWidth,lastAccent=Integer.MIN_VALUE;
    private float boundsSafe;
    private final Runnable tick=()->{if(active)render();};
    private final Runnable mediaChanged=()->{if(active&&"media".equals(mode))render();};
    private final SharedPreferences.OnSharedPreferenceChangeListener changed=(p,key)->{if(key!=null&&(key.equals("utilityCard")||key.startsWith("utilityTimer")||key.equals("petId")))handler.post(tick);};
    public UtilityCardView(Context c,boolean full){
        super(c);this.full=full;ui=new UiTheme(c);prefs=c.getSharedPreferences(Pets.PREFS,0);setOrientation(VERTICAL);setPadding(ui.dp(full?10:12),ui.dp(full?6:10),ui.dp(full?6:12),ui.dp(full?6:10));ui.card(this,full?0xb31b1820:ui.surface,full?20:24);setElevation(full?0:ui.dp(4));setVisibility(GONE);setClickable(true);setFocusable(false);
    }
    public void start(){if(active)return;active=true;battery=null;prefs.registerOnSharedPreferenceChangeListener(changed);PetNotifications.addMediaListener(mediaChanged);render();}
    public void stop(){if(!active)return;active=false;handler.removeCallbacksAndMessages(null);prefs.unregisterOnSharedPreferenceChangeListener(changed);PetNotifications.removeMediaListener(mediaChanged);if("timer".equals(mode))UtilityTimerStore.checkpoint(getContext());stamp="";}
    String qaDisplayValue(){return value==null?"":value.getText().toString();}
    Button qaButton(String action){return "toggle".equals(action)?first:("reset".equals(action)||"next".equals(action))?second:"focus".equals(action)?focus:"stopwatch".equals(action)?stopwatch:null;}
    void resetForQaRestore(){stop();mode="";stamp="";}
    public void batteryChanged(Intent i){if(Intent.ACTION_BATTERY_CHANGED.equals(i.getAction())){battery=new Intent(i);if(active&&"battery".equals(mode))render();}}
    public void windowBounds(int width,float safeLeft){
        if(width<=0)return;boundsWidth=width;boundsSafe=safeLeft;int margin=ui.dp(8);int available=Math.max(1,width-Math.round(safeLeft)-2*margin);int cap=full?("battery".equals(mode)?180:"timer".equals(mode)?224:240):260;int wanted=Math.min(ui.dp(cap),available);FrameLayout.LayoutParams lp=(FrameLayout.LayoutParams)getLayoutParams();
        if(lp==null||lp.width!=wanted){lp=new FrameLayout.LayoutParams(wanted,-2,Gravity.RIGHT|Gravity.BOTTOM);lp.rightMargin=margin;lp.bottomMargin=margin;setLayoutParams(lp);}
    }
    private TextView text(int size){TextView t=ui.label("",size,false);t.setMaxLines(1);t.setEllipsize(TextUtils.TruncateAt.END);addView(t,new LayoutParams(-1,-2));return t;}
    private Button button(String name,Runnable action){Button b=ui.button(name,false,v->action.run());b.setContentDescription(name);b.setMinWidth(0);b.setMinimumWidth(0);b.setMinHeight(ui.dp(48));b.setMinimumHeight(ui.dp(48));b.setPadding(ui.dp(full?0:6),ui.dp(full?0:6),ui.dp(full?0:6),ui.dp(full?0:6));if(full)b.setTextSize(android.util.TypedValue.COMPLEX_UNIT_DIP,24);else b.setTextSize(14);b.setMaxLines(full?1:2);b.setEllipsize(TextUtils.TruncateAt.END);if(full)b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x44ffffff),ui.shape(0x16ffffff,24),null));return b;}
    private TextView dockText(int size){TextView t=ui.label("",size,false);t.setTextColor(Color.WHITE);t.setMaxLines(1);t.setEllipsize(TextUtils.TruncateAt.END);return t;}
    private void dockButton(Button b){LayoutParams p=new LayoutParams(ui.dp(48),-2);p.leftMargin=ui.dp(4);addView(b,p);}
    private void actionLabel(Button button,String label,String glyph){String visible=full?glyph:label;if(!visible.contentEquals(button.getText()))button.setText(visible);button.setContentDescription(label);}
    private void dock(){
        setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);header=dockText(12);detail=dockText("media".equals(mode)?11:12);value=dockText("media".equals(mode)?14:21);value.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));value.setFontFeatureSettings("tnum");if(!"media".equals(mode))value.setAutoSizeTextTypeUniformWithConfiguration(12,21,1,android.util.TypedValue.COMPLEX_UNIT_SP);
        if("battery".equals(mode)){setMinimumHeight(ui.dp(52));LayoutParams number=new LayoutParams(-2,-2);number.rightMargin=ui.dp(10);addView(value,number);addView(detail,new LayoutParams(0,-2,1));}
        else {setMinimumHeight(0);if("media".equals(mode)){LinearLayout song=new LinearLayout(getContext());song.setOrientation(VERTICAL);song.addView(value,new LayoutParams(-1,-2));song.addView(detail,new LayoutParams(-1,-2));addView(song,new LayoutParams(0,-2,1));}else addView(value,new LayoutParams(0,-2,1));dockButton(first);dockButton(second);}
        lastAccent=Integer.MIN_VALUE;harmonize();
    }
    private void harmonize(){if(!full)return;int accent=Color.WHITE;try{accent=Color.parseColor(Pets.current(getContext()).optString("timeColor","#FFFFFF"));if(Color.luminance(accent)<.3f)accent=Color.WHITE;}catch(Exception ignored){}if(lastAccent==accent)return;lastAccent=accent;value.setTextColor("media".equals(mode)?Color.WHITE:accent);detail.setTextColor(0xffdedbe2);if(first!=null)first.setTextColor(accent);if(second!=null)second.setTextColor(0xfff5f0f7);}
    private void row(Button a,Button b){LinearLayout row=new LinearLayout(getContext());row.setOrientation(HORIZONTAL);LayoutParams rowp=new LayoutParams(-1,-2);rowp.topMargin=ui.dp(6);addView(row,rowp);LayoutParams ap=new LayoutParams(0,-2,1);ap.rightMargin=ui.dp(4);row.addView(a,ap);row.addView(b,new LayoutParams(0,-2,1));}
    private void rebuild(){
        removeAllViews();stamp="";first=second=focus=stopwatch=null;
        if(!full){header=text(13);header.setTextColor(ui.secondary);value=text("media".equals(mode)?18:26);detail=text(12);detail.setTextColor(ui.secondary);}
        if("media".equals(mode)){first=button("Играть",()->mediaControl("toggle"));second=button("Далее",()->mediaControl("next"));if(!full)row(first,second);actionLabel(second,"Далее","›| ");}
        if("timer".equals(mode)){first=button("Старт",()->timerAction("toggle"));second=button("Сброс",()->timerAction("reset"));if(!full)row(first,second);actionLabel(second,"Сброс","↺");stopwatch=button("Секундомер",()->timerAction("stopwatch"));focus=button("Фокус 25 мин",()->timerAction("focus"));}
        if(full)dock();if(boundsWidth>0)windowBounds(boundsWidth,boundsSafe);
    }
    private void mediaControl(String action){if(!PetNotifications.control(action))detail.setText("Команда сейчас недоступна");}
    private void timerAction(String action){TimerState s=UtilityTimerStore.read(getContext());long now=SystemClock.elapsedRealtime();if("toggle".equals(action))s.toggle(now);else if("reset".equals(action))s.reset(now);else s.select(action,now);UtilityTimerStore.save(getContext(),s);Pets.signal(getContext());render();}
    private void labels(String a,String b,String c){String next=a+"\n"+b+"\n"+c;if(next.equals(stamp))return;stamp=next;header.setText(a);value.setText(b);detail.setText(c);setContentDescription(a+". "+b+". "+c);}
    private void render(){
        handler.removeCallbacks(tick);if(!active)return;String selected=prefs.getString("utilityCard","none");if(!selected.equals("battery")&&!selected.equals("media")&&!selected.equals("timer"))selected="none";
        if(!selected.equals(mode)){if("timer".equals(mode))UtilityTimerStore.checkpoint(getContext());mode=selected;if(!"none".equals(mode))rebuild();}
        if("none".equals(mode)||full&&"media".equals(mode)&&PetNotifications.currentMedia()==null){setVisibility(GONE);return;}setVisibility(VISIBLE);harmonize();
        if("battery".equals(mode))renderBattery();else if("media".equals(mode))renderMedia();else renderTimer();
    }
    private void renderBattery(){
        if(battery==null)battery=getContext().registerReceiver(null,new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        if(battery==null){labels("Батарея",full?"—":"Нет данных",full?"Нет данных":"Данные появятся от системы");return;}
        int level=battery.getIntExtra(BatteryManager.EXTRA_LEVEL,-1),scale=battery.getIntExtra(BatteryManager.EXTRA_SCALE,100),status=battery.getIntExtra(BatteryManager.EXTRA_STATUS,BatteryManager.BATTERY_STATUS_UNKNOWN),plug=battery.getIntExtra(BatteryManager.EXTRA_PLUGGED,0);
        String percent=level>=0&&scale>0?Math.round(100f*level/scale)+"%":"—";
        String source=(plug&BatteryManager.BATTERY_PLUGGED_USB)!=0?"USB":(plug&BatteryManager.BATTERY_PLUGGED_AC)!=0?"Питание":(plug&BatteryManager.BATTERY_PLUGGED_WIRELESS)!=0?"Беспроводная":"";
        String state=status==BatteryManager.BATTERY_STATUS_FULL?"Заряд завершён":status==BatteryManager.BATTERY_STATUS_CHARGING?"Заряжается":plug!=0?"Подключён к питанию":"От батареи";
        String temp=battery.hasExtra(BatteryManager.EXTRA_TEMPERATURE)?String.format(Locale.getDefault(),"Батарея: %.1f °C",battery.getIntExtra(BatteryManager.EXTRA_TEMPERATURE,0)/10f):"Температура недоступна";
        if(full){String compactTemp=battery.hasExtra(BatteryManager.EXTRA_TEMPERATURE)?String.format(Locale.getDefault(),"%.1f °C",battery.getIntExtra(BatteryManager.EXTRA_TEMPERATURE,0)/10f):"";labels(state,percent,(plug!=0?"⚡︎ ":"")+compactTemp);setContentDescription("Батарея "+percent+". "+state+". "+temp+(source.isEmpty()?"":". "+source));}
        else labels(state,percent,temp+(source.isEmpty()?"":" · "+source));
    }
    private void renderMedia(){
        MediaController c=PetNotifications.currentMedia();PlaybackState s=c==null?null:c.getPlaybackState();MediaMetadata m=c==null?null:c.getMetadata();boolean playing=PetNotifications.isPlaying(s);
        String title=m==null?null:m.getString(MediaMetadata.METADATA_KEY_TITLE),artist=m==null?null:m.getString(MediaMetadata.METADATA_KEY_ARTIST);
        if(c==null)labels("Музыка","Нет активного плеера",PetNotifications.listenerAvailable()?"Запусти музыку на телефоне":"Нужен доступ к уведомлениям");
        else labels(playing?"Сейчас играет":"Музыка на паузе",title==null||title.isEmpty()?"Активный плеер":title,artist==null||artist.isEmpty()?"Управление медиасессией":artist);
        String label=playing?"Пауза":"Играть";actionLabel(first,label,playing?"Ⅱ":"▶");first.setEnabled(PetNotifications.canControl("toggle"));second.setEnabled(PetNotifications.canControl("next"));first.setAlpha(first.isEnabled()?1f:.45f);second.setAlpha(second.isEnabled()?1f:.45f);
    }
    private void renderTimer(){
        TimerState s=UtilityTimerStore.read(getContext());long now=SystemClock.elapsedRealtime();if(s.finishIfNeeded(now))UtilityTimerStore.save(getContext(),s);
        long seconds=("focus".equals(s.mode)?s.displayed(now)+999:s.displayed(now))/1000;long hours=seconds/3600;String value=hours>0?String.format(Locale.getDefault(),"%d:%02d:%02d",hours,seconds/60%60,seconds%60):String.format(Locale.getDefault(),"%02d:%02d",seconds/60,seconds%60);
        labels("focus".equals(s.mode)?"Визуальный таймер · 25 минут":"Секундомер",value,"Без звукового сигнала");
        String title=s.running?"Пауза":"Старт";actionLabel(first,title,s.running?"Ⅱ":"▶");stopwatch.setSelected("stopwatch".equals(s.mode));focus.setSelected("focus".equals(s.mode));stopwatch.setAlpha(stopwatch.isSelected()?1f:.65f);focus.setAlpha(focus.isSelected()?1f:.65f);
        if(s.running&&isShown()&&getWindowVisibility()==VISIBLE)handler.postDelayed(tick,Math.max(1,1000-s.elapsed(now)%1000));
    }
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);if(handler!=null){handler.removeCallbacks(tick);if(active&&visibility==VISIBLE)handler.post(tick);}}
    @Override protected void onVisibilityChanged(View changedView,int visibility){super.onVisibilityChanged(changedView,visibility);if(handler!=null&&active){handler.removeCallbacks(tick);if(visibility==VISIBLE)handler.post(tick);}}
}
