package org.flippets.app;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.hardware.display.DisplayManager;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    PetStage preview;
    String exported,logExport,pickPet;
    boolean pickFront;
    LinearLayout body;
    LinearLayout clipPanel;
    TextView selectedName,selectedInfo;
    Button detailsButton;
    int dp(float value){return Math.round(value*getResources().getDisplayMetrics().density);}
    protected void onCreate(Bundle saved){
        super.onCreate(saved);if(saved!=null){pickPet=saved.getString("pickPet");pickFront=saved.getBoolean("pickFront");exported=saved.getString("exported");logExport=saved.getString("logExport");}getWindow().setStatusBarColor(0xff111c28);getWindow().setNavigationBarColor(0xff111c28);
        ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);body.setPadding(dp(18),dp(14),dp(18),dp(24));body.setBackgroundColor(0xff111c28);scroll.addView(body);setContentView(scroll);scroll.setOnApplyWindowInsetsListener((v,i)->{android.graphics.Insets bars=android.os.Build.VERSION.SDK_INT>=30?i.getInsets(android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.displayCutout()):android.graphics.Insets.of(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);return i;});
        text("Flip Pets",30);text("Твоё оформление внешнего экрана",14);
        selectedName=new TextView(this);selectedName.setTextSize(22);selectedName.setTextColor(Color.WHITE);body.addView(selectedName);
        selectedInfo=new TextView(this);selectedInfo.setTextSize(13);selectedInfo.setTextColor(0xffb9cbd6);selectedInfo.setPadding(0,dp(6),0,dp(12));body.addView(selectedInfo);
        preview=new PetStage(this,false);body.addView(preview,new LinearLayout.LayoutParams(-1,dp(168)));
        button("Выбрать оформление",v->new GalleryDialog(this).show());
        LinearLayout controls=new LinearLayout(this);Button startButton=new Button(this);startButton.setText("Два экрана · Shizuku");startButton.setAllCaps(false);startButton.setOnClickListener(v->ShizukuBridge.start(this));controls.addView(startButton,new LinearLayout.LayoutParams(0,dp(54),2));Button stopButton=new Button(this);stopButton.setText("Стоп");stopButton.setAllCaps(false);stopButton.setOnClickListener(v->ShizukuBridge.stop(this));controls.addView(stopButton,new LinearLayout.LayoutParams(0,dp(54),1));body.addView(controls);
        text("При складывании — штатный экран и AOD Xiaomi.",13);
        button("Полноэкранный просмотр",v->startActivity(new Intent(this,PetActivity.class)));
        button("Установить как живые обои",v->{try{startActivity(new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(this,PetWallpaper.class)));}catch(Exception e){message(e.toString());}});
        text("",13);
        detailsButton=new Button(this);detailsButton.setAllCaps(false);detailsButton.setOnClickListener(v->{boolean open=clipPanel.getVisibility()!=View.VISIBLE;clipPanel.setVisibility(open?View.VISIBLE:View.GONE);getSharedPreferences(Pets.PREFS,0).edit().putBoolean("detailsOpen",open).apply();refreshDetailsTitle();});body.addView(detailsButton);
        clipPanel=new LinearLayout(this);clipPanel.setOrientation(1);body.addView(clipPanel);clipPanel.setVisibility(getSharedPreferences(Pets.PREFS,0).getBoolean("detailsOpen",false)?View.VISIBLE:View.GONE);
        button("Доступы, запуск и диагностика",v->settings());button("Сохранить журнал",v->exportLogs());
        refreshSelection();
    }
    void select(int index){Pets.select(this,index);preview.reload();refreshSelection();}
    void refreshSelection(){JSONObject pet=Pets.current(this);selectedName.setText(pet.optString("name"));selectedInfo.setText(GalleryDialog.group(pet)+(pet.optString("kind").equals("composition")?" · настройки ниже":" · сцен: "+pet.optJSONObject("clips").length()));populateClips();refreshDetailsTitle();}
    void refreshDetailsTitle(){detailsButton.setText((clipPanel.getVisibility()==View.VISIBLE?"Скрыть":"Открыть")+" сцены и настройки оформления");}
    void settings(){
        ScrollView scroll=new ScrollView(this);LinearLayout panel=new LinearLayout(this);panel.setOrientation(1);panel.setPadding(dp(14),dp(10),dp(14),dp(18));panel.setBackgroundColor(0xff182432);scroll.addView(panel);LinearLayout mainBody=body;body=panel;
        text("Запуск без root",21);text("Запусти Shizuku через беспроводную отладку, затем нажми «Включить два экрана». ПК постоянно не нужен. После перезагрузки Shizuku нужно запустить снова. Набор, избранное и оформление сохраняются.",14);
        button("Инструкция по Shizuku",v->ShizukuBridge.guide(this));button("Состояние контроллера",v->ShizukuBridge.status(this));button("Открыть внешний экран вручную",v->openSecondary());
        text("Реакции питомцев",21);text("Зарядка и низкий заряд работают сразу. Для музыки и входящих уведомлений нужен отдельный доступ. Содержимое сообщений не сохраняется.",14);
        button("Доступ к уведомлениям и музыке",v->startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));
        button("Разрешить шаги",v->{if(checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.ACTIVITY_RECOGNITION},3);else message("Доступ уже разрешён. Нужен датчик шагов.");});
        Switch rain=new Switch(this);rain.setText("Дождь · ручной режим");rain.setTextColor(Color.WHITE);rain.setChecked(Pets.state.rain);rain.setOnCheckedChangeListener((b,yes)->{Pets.state.rain=yes;Pets.signal(this);});body.addView(rain);
        Switch decoder=new Switch(this);decoder.setText("Совместимый декодер · если питомец не виден");decoder.setTextColor(Color.WHITE);decoder.setChecked(getSharedPreferences(Pets.PREFS,0).getBoolean("softwareDecoder",false));decoder.setOnCheckedChangeListener((b,yes)->{getSharedPreferences(Pets.PREFS,0).edit().putBoolean("softwareDecoder",yes).apply();org.libpag.VideoDecoder.SetMaxHardwareDecoderCount(yes?0:4);preview.reload();Pets.signal(this);});body.addView(decoder);
        text("Расход ресурсов",21);button("Плавность анимаций",v->new AlertDialog.Builder(this).setTitle("Частота PAG-анимаций").setItems(new String[]{"Экономно · 12 кадров/с","Обычно · 20 кадров/с","Плавно · 30 кадров/с"},(d,which)->{getSharedPreferences(Pets.PREFS,0).edit().putInt("frameRate",new int[]{12,20,30}[which]).apply();Pets.signal(this);}).setNegativeButton("Отмена",null).show());text("Скрытый экран останавливает рендеринг и освобождает декодеры. Внешний сеанс не запрещает телефону засыпать. Частота видео зависит от исходного файла.",14);
        text("Диагностика ошибок",21);button("Сохранить журнал",v->exportLogs());text("Последние ошибки и запуски сохраняются на телефоне. Журнал ограничен по размеру; фонового опроса нет. Отчёт включает только логи нашего приложения, без содержимого уведомлений и фото.",14);
        text("Совместимость",21);button("Сохранить диагностику экранов",v->diagnostics());text("Режим двух физических экранов ещё требует проверки на MIX Flip. При отказе нужна диагностика. Камерные жесты, платежи, диалоговый ИИ и онлайн-погода Xiaomi не перенесены.",14);
        body=mainBody;new AlertDialog.Builder(this).setTitle("Настройки").setView(scroll).setPositiveButton("Готово",null).show();
    }
    void text(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setPadding(0,12,0,12);body.addView(t);}
    void populateClips(){clipPanel.removeAllViews();JSONObject pet=Pets.current(this),clips=pet.optJSONObject("clips");if(pet.optString("kind").equals("composition")){SceneControls.populate(this,clipPanel,pet,preview);return;}if(clips==null)return;boolean reactive=pet.optString("kind").equals("reactive");TextView note=new TextView(this);note.setTextColor(Color.WHITE);note.setPadding(0,12,0,12);note.setText(reactive?"Этот питомец реагирует на системные события.":"Для этого набора доступны оригинальные сцены и реакции на касания. Видео Lumi и Peeko перенесены без диалогового ИИ Xiaomi.");clipPanel.addView(note);
        for(int i=0;i<clips.length();i+=2){LinearLayout row=new LinearLayout(this);for(int j=i;j<Math.min(i+2,clips.length());j++){final int index=j;Button b=new Button(this);b.setAllCaps(false);String label=reactive&&j<Pets.EVENTS.length?Pets.EVENTS[j]:"Сцена "+(j+1);if(clips.optString(Integer.toString(j)).contains("nfc_pin"))label="NFC (просмотр)";JSONArray extra=pet.optJSONArray("extra");if(extra!=null&&j<extra.length())label=videoLabel(extra.optJSONObject(j).optString("label"),j);b.setText(label);b.setOnClickListener(v->Pets.choose(this,index));row.addView(b,new LinearLayout.LayoutParams(0,-2,1));}clipPanel.addView(row);}
        if(pet.optString("name").equals("Flowing glitter"))SceneControls.populate(this,clipPanel,pet,preview);
    }
    String videoLabel(String name,int index){String[] keys={"idle","happy","sad","sing","speak","listen","dance","greet","rain","snow","spring","midautumn","newyear","nationalday","dragon"};String[] titles={"Ожидание","Радость","Грусть","Поёт","Говорит","Слушает","Танец","Приветствие","Дождь","Снег","Весна","Праздник осени","Новый год","Праздник","Дракон"};for(int i=0;i<keys.length;i++)if(name.startsWith(keys[i]))return titles[i]+(name.endsWith("_a")?" 1":name.endsWith("_b")?" 2":name.matches(".*_[0-9]")?" "+(Character.digit(name.charAt(name.length()-1),10)+1):"");return "Сцена "+(index+1);}
    void button(String title,View.OnClickListener listener){Button b=new Button(this);b.setAllCaps(false);b.setTextSize(16);b.setText(title);b.setOnClickListener(listener);body.addView(b);}
    void message(String text){new AlertDialog.Builder(this).setMessage(text).setPositiveButton("ОК",null).show();}
    void openSecondary(){
        DisplayManager dm=(DisplayManager)getSystemService(DISPLAY_SERVICE);java.util.ArrayList<Display> candidates=new java.util.ArrayList<>();
        for(Display d:dm.getDisplays())if(d.getDisplayId()!=Display.DEFAULT_DISPLAY)candidates.add(d);
        if(candidates.isEmpty()){message("Второй экран сейчас не доступен приложению. Проверь при раскрытом и закрытом телефоне и сохрани диагностику.");return;}
        String[] names=new String[candidates.size()];for(int i=0;i<names.length;i++)names[i]="Экран "+candidates.get(i).getDisplayId()+": "+candidates.get(i).getName();
        new AlertDialog.Builder(this).setTitle("Выбери внешний экран").setItems(names,(dialog,which)->{
            int id=candidates.get(which).getDisplayId();Intent intent=new Intent(this,PetActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_MULTIPLE_TASK);
            ActivityManager am=(ActivityManager)getSystemService(ACTIVITY_SERVICE);
            if(!am.isActivityStartAllowedOnDisplay(this,id,intent)){message("Прошивка запрещает запуск приложения на этом экране. Сохрани диагностику для проверки запуска через ADB.");return;}
            try{startActivity(intent,ActivityOptions.makeBasic().setLaunchDisplayId(id).toBundle());}catch(Exception e){message("Запуск не удался: "+e);}
        }).setNegativeButton("Отмена",null).show();
    }
    void exportLogs(){android.widget.Toast.makeText(this,"Собираю журнал…",android.widget.Toast.LENGTH_SHORT).show();ShizukuBridge.captureStatus(this,()->new Thread(()->{logExport=AppLog.report(getApplicationContext());runOnUiThread(()->{if(!isFinishing()&&!isDestroyed())startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("text/plain").putExtra(Intent.EXTRA_TITLE,"flip-pets-log.txt"),8);});},"diagnostic-export").start());}
    void diagnostics(){exported=Pets.displayReport(this);new AlertDialog.Builder(this).setTitle("Диагностика экранов").setMessage(exported).setPositiveButton("Сохранить .txt",(d,w)->startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("text/plain").putExtra(Intent.EXTRA_TITLE,"flip-pets-diagnostics.txt"),7)).setNeutralButton("Скопировать",(d,w)->((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("Диагностика",exported))).setNegativeButton("Закрыть",null).show();}
    void pickImage(String id,boolean front){pickPet=id;pickFront=front;startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("image/*"),front?10:9);}
    protected void onSaveInstanceState(Bundle state){state.putString("exported",exported);state.putString("logExport",logExport);state.putString("pickPet",pickPet);state.putBoolean("pickFront",pickFront);super.onSaveInstanceState(state);}
    protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if((request==9||request==10)&&result==RESULT_OK&&data!=null&&pickPet!=null){final String id=pickPet;final boolean front=pickFront;final android.net.Uri uri=data.getData();new Thread(()->{try{SceneSettings.importImage(this,id,front,uri);runOnUiThread(()->{if(!isFinishing())preview.reload();});}catch(Exception e){runOnUiThread(()->{if(!isFinishing())message(e.toString());});}},"photo-import").start();}if((request==7||request==8)&&result==RESULT_OK&&data!=null)try(java.io.OutputStream s=getContentResolver().openOutputStream(data.getData())){String report=request==8?logExport:exported;if(report==null)report=Pets.displayReport(this)+AppLog.saved(this);s.write(report.getBytes(StandardCharsets.UTF_8));}catch(Exception e){message(e.toString());}}
    protected void onStart(){super.onStart();if(preview!=null){refreshSelection();preview.start();}}
    protected void onStop(){preview.stop();super.onStop();}
    protected void onDestroy(){preview.destroy();super.onDestroy();}
    public void onRequestPermissionsResult(int request,String[] p,int[] results){super.onRequestPermissionsResult(request,p,results);if(request==3){preview.stop();preview.start();}}
}
