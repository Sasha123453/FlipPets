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
    UiTheme ui;
    boolean waitingSessionStart;
    int dp(float value){return Math.round(value*getResources().getDisplayMetrics().density);}
    protected void onCreate(Bundle saved){
        boolean dark=(getResources().getConfiguration().uiMode&android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES;
        setTheme(dark?android.R.style.Theme_Material_NoActionBar:android.R.style.Theme_Material_Light_NoActionBar);
        super.onCreate(saved);if(saved!=null){pickPet=saved.getString("pickPet");pickFront=saved.getBoolean("pickFront");exported=saved.getString("exported");logExport=saved.getString("logExport");}ui=new UiTheme(this);ui.window(getWindow());
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);body=new LinearLayout(this);body.setOrientation(1);body.setPadding(dp(20),dp(16),dp(20),dp(28));body.setBackgroundColor(ui.background);scroll.setBackgroundColor(ui.background);scroll.addView(body);setContentView(scroll);scroll.setOnApplyWindowInsetsListener((v,i)->{android.graphics.Insets bars=android.os.Build.VERSION.SDK_INT>=30?i.getInsets(android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.displayCutout()):android.graphics.Insets.of(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);return i;});
        text("Flip Pets",34);text("Твой внешний экран",15);
        LinearLayout page=body,card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(18),dp(18),dp(18),dp(18));ui.card(card,ui.surface,28);body.addView(card,ui.spaced());body=card;
        TextView overline=ui.label("СЕЙЧАС НА ЭКРАНЕ",11,true);overline.setLetterSpacing(.1f);body.addView(overline);
        selectedName=ui.label("",24,false);selectedName.setPadding(0,dp(8),0,0);body.addView(selectedName);
        selectedInfo=ui.label("",13,true);selectedInfo.setPadding(0,dp(6),0,dp(16));body.addView(selectedInfo);
        preview=new PetStage(this,false);FrameLayout previewCard=new FrameLayout(this);ui.card(previewCard,0xff182432,22);previewCard.addView(preview,new FrameLayout.LayoutParams(-1,-1));body.addView(previewCard,new LinearLayout.LayoutParams(-1,dp(188)));
        Button gallery=ui.button("Выбрать оформление",true,v->new GalleryDialog(this).show());body.addView(gallery,ui.spaced());
        button("Своё фото",v->ownPhoto());body=page;
        text("Два экрана",22);
        button("Включить через Shizuku",v->startSession());button("Выключить внешний сеанс",v->{waitingSessionStart=false;ShizukuBridge.stop(this);});
        text("При раскрытии — твоё оформление. При складывании — штатный экран и AOD Xiaomi.",14);
        button("Полноэкранный просмотр",v->startActivity(new Intent(this,PetActivity.class)));
        button("Установить как живые обои",v->{try{startActivity(new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(this,PetWallpaper.class)));}catch(Exception e){message(e.toString());}});
        text("Настрой под себя",22);
        detailsButton=ui.button("",false,v->{boolean open=clipPanel.getVisibility()!=View.VISIBLE;clipPanel.setVisibility(open?View.VISIBLE:View.GONE);getSharedPreferences(Pets.PREFS,0).edit().putBoolean("detailsOpen",open).apply();refreshDetailsTitle();});body.addView(detailsButton,ui.spaced());
        clipPanel=new LinearLayout(this);clipPanel.setOrientation(1);clipPanel.setPadding(dp(16),dp(8),dp(16),dp(16));ui.card(clipPanel,ui.surface,24);body.addView(clipPanel,ui.spaced());clipPanel.setVisibility(getSharedPreferences(Pets.PREFS,0).getBoolean("detailsOpen",false)?View.VISIBLE:View.GONE);
        button("Настройки и доступы",v->settings());button("Сохранить журнал",v->exportLogs());
        refreshSelection();
    }
    void ownPhoto(){JSONArray catalog=Pets.catalog(this);for(int i=0;i<catalog.length();i++){JSONObject pet=catalog.optJSONObject(i);if("photo".equals(pet.optString("renderer"))){select(i);pickImage(pet.optString("id"),false);return;}}message("Оформление для своей фотографии не найдено.");}
    void startSession(){if(CoverGuard.notificationPermissionNeeded(this)){waitingSessionStart=true;CoverGuard.requestNotificationPermission(this);return;}ShizukuBridge.start(this);}
    void select(int index){Pets.select(this,index);preview.reload();refreshSelection();}
    void refreshSelection(){JSONObject pet=Pets.current(this);selectedName.setText(pet.optString("name"));selectedInfo.setText(GalleryDialog.group(pet)+(pet.optString("kind").equals("composition")?" · настройки ниже":" · сцен: "+pet.optJSONObject("clips").length()));populateClips();refreshDetailsTitle();}
    void refreshDetailsTitle(){detailsButton.setText((clipPanel.getVisibility()==View.VISIBLE?"Скрыть":"Открыть")+" сцены и настройки оформления");}
    void settings(){
        ScrollView scroll=new ScrollView(this);LinearLayout panel=new LinearLayout(this);panel.setOrientation(1);panel.setPadding(dp(20),dp(10),dp(20),dp(24));panel.setBackgroundColor(ui.background);scroll.addView(panel);LinearLayout mainBody=body;body=panel;
        text("Полезные карточки",21);UtilitySettings.populate(this,body,preview);
        text("Запуск без root",21);text("Запусти Shizuku через беспроводную отладку, затем нажми «Включить через Shizuku». ПК постоянно не нужен. После перезагрузки Shizuku нужно запустить снова. Набор, избранное и оформление сохраняются.",14);
        button("Инструкция по Shizuku",v->ShizukuBridge.guide(this));button("Состояние контроллера",v->ShizukuBridge.status(this));button("Открыть внешний экран вручную",v->openSecondary());
        text("Реакции питомцев",21);text("Зарядка и низкий заряд работают сразу. Для музыки и входящих уведомлений нужен отдельный доступ. Содержимое сообщений не сохраняется.",14);
        button("Доступ к уведомлениям и музыке",v->startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));
        button("Разрешить шаги",v->{if(checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.ACTIVITY_RECOGNITION},3);else message("Доступ уже разрешён. Нужен датчик шагов.");});
        Switch rain=new Switch(this);rain.setText("Дождь · ручной режим");ui.toggle(rain);rain.setChecked(Pets.state.rain);rain.setOnCheckedChangeListener((b,yes)->{Pets.state.rain=yes;Pets.signal(this);});body.addView(rain);
        Switch decoder=new Switch(this);decoder.setText("Совместимый декодер · если питомец не виден");ui.toggle(decoder);decoder.setChecked(getSharedPreferences(Pets.PREFS,0).getBoolean("softwareDecoder",false));decoder.setOnCheckedChangeListener((b,yes)->{getSharedPreferences(Pets.PREFS,0).edit().putBoolean("softwareDecoder",yes).apply();org.libpag.VideoDecoder.SetMaxHardwareDecoderCount(yes?0:4);preview.reload();Pets.signal(this);});body.addView(decoder);
        text("Расход ресурсов",21);button("Плавность анимаций",v->new AlertDialog.Builder(this).setTitle("Частота PAG-анимаций").setItems(new String[]{"Экономно · 12 кадров/с","Обычно · 20 кадров/с","Плавно · 30 кадров/с"},(d,which)->{getSharedPreferences(Pets.PREFS,0).edit().putInt("frameRate",new int[]{12,20,30}[which]).apply();Pets.signal(this);}).setNegativeButton("Отмена",null).show());text("Скрытый экран останавливает рендеринг и освобождает декодеры. Внешний сеанс не запрещает телефону засыпать. Частота видео зависит от исходного файла.",14);
        Switch calm=new Switch(this);calm.setText("Спокойный режим Bubbles/Roe");ui.toggle(calm);calm.setChecked(getSharedPreferences(Pets.PREFS,0).getBoolean("calmPets",false));calm.setOnCheckedChangeListener((b,yes)->{getSharedPreferences(Pets.PREFS,0).edit().putBoolean("calmPets",yes).apply();Pets.playRevision++;Pets.signal(this);});body.addView(calm);text("Charlie, Coco, Lola, Jumbo и Pip проигрывают сцену один раз, как в оригинале. Bubbles/Roe повторяют обычные состояния; спокойный режим останавливает их после одного цикла. Это дополнительная настройка порта.",14);
        text("Диагностика ошибок",21);button("Сохранить журнал",v->exportLogs());text("Последние ошибки и запуски сохраняются на телефоне. Журнал ограничен по размеру; фонового опроса нет. Отчёт включает только логи нашего приложения, без содержимого уведомлений и фото.",14);
        text("Совместимость",21);button("Сохранить диагностику экранов",v->diagnostics());text("Два экрана без root проверены на MIX Flip с HyperOS 3 EEA. На другой прошивке поведение может отличаться. Камерные жесты, платежи, диалоговый ИИ и онлайн-погода Xiaomi не перенесены.",14);
        text("Работа в фоне",21);text("Внешний сеанс продолжает работать после закрытия окна приложения. Его можно выключить здесь или из постоянного уведомления. Принудительная остановка в системных настройках прекращает работу приложения.",14);button("Разрешить уведомление сеанса",v->CoverGuard.requestNotificationPermission(this));
        Switch fade=new Switch(this);fade.setText("Затухание при складывании");ui.toggle(fade);fade.setChecked(getSharedPreferences(Pets.PREFS,0).getBoolean("hingeFade",true));fade.setOnCheckedChangeListener((b,yes)->getSharedPreferences(Pets.PREFS,0).edit().putBoolean("hingeFade",yes).apply());body.addView(fade);text("По углу шарнира, если датчик доступен. При наличии только состояния складывания используется плавный переход между состояниями. Штатный экран возвращается при закрытии или сне.",14);
        body=mainBody;new AlertDialog.Builder(this).setTitle("Настройки").setView(scroll).setPositiveButton("Готово",null).show();
    }
    void text(String value,int size){TextView t=ui.label(value,size,size<20);if(size>=20)t.setTypeface(android.graphics.Typeface.create("sans-serif-medium",0));t.setPadding(0,dp(size>=20?18:8),0,dp(8));body.addView(t);}
    void populateClips(){clipPanel.removeAllViews();JSONObject pet=Pets.current(this),clips=pet.optJSONObject("clips");if(pet.optString("kind").equals("composition")){SceneControls.populate(this,clipPanel,pet,preview);return;}if(clips==null)return;boolean reactive=pet.optString("kind").equals("reactive");TextView note=new TextView(this);note.setTextColor(ui.secondary);note.setTextSize(14);note.setPadding(0,dp(12),0,dp(12));note.setText(reactive?"Этот питомец реагирует на системные события.":"Для этого набора доступны оригинальные сцены и реакции на касания. Видео Lumi и Peeko перенесены без диалогового ИИ Xiaomi.");clipPanel.addView(note);
        int columns=getResources().getConfiguration().fontScale>1.25f?1:2;for(int i=0;i<clips.length();i+=columns){LinearLayout row=new LinearLayout(this);for(int j=i;j<Math.min(i+columns,clips.length());j++){final int index=j;Button b=new Button(this);ui.style(b,false);String label=reactive&&j<Pets.EVENTS.length?Pets.EVENTS[j]:"Сцена "+(j+1);if(clips.optString(Integer.toString(j)).contains("nfc_pin"))label="NFC (просмотр)";JSONArray extra=pet.optJSONArray("extra");if(extra!=null&&j<extra.length())label=videoLabel(extra.optJSONObject(j).optString("label"),j);b.setText(label);b.setOnClickListener(v->Pets.choose(this,index));LinearLayout.LayoutParams cell=new LinearLayout.LayoutParams(0,-2,1);cell.topMargin=dp(6);cell.leftMargin=j>i?dp(6):0;row.addView(b,cell);}clipPanel.addView(row);}
        if(pet.optString("name").equals("Flowing glitter"))SceneControls.populate(this,clipPanel,pet,preview);
    }
    String videoLabel(String name,int index){String[] keys={"idle","happy","sad","sing","speak","listen","dance","greet","rain","snow","spring","midautumn","newyear","nationalday","dragon"};String[] titles={"Ожидание","Радость","Грусть","Поёт","Говорит","Слушает","Танец","Приветствие","Дождь","Снег","Весна","Праздник осени","Новый год","Праздник","Дракон"};for(int i=0;i<keys.length;i++)if(name.startsWith(keys[i]))return titles[i]+(name.endsWith("_a")?" 1":name.endsWith("_b")?" 2":name.matches(".*_[0-9]")?" "+(Character.digit(name.charAt(name.length()-1),10)+1):"");return "Сцена "+(index+1);}
    void button(String title,View.OnClickListener listener){body.addView(ui.button(title,false,listener),ui.spaced());}
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
    public void onRequestPermissionsResult(int request,String[] p,int[] results){super.onRequestPermissionsResult(request,p,results);if(request==3){preview.stop();preview.start();}if(request==CoverGuard.NOTIFICATION_PERMISSION_REQUEST&&waitingSessionStart){waitingSessionStart=false;ShizukuBridge.start(this);}}
}
