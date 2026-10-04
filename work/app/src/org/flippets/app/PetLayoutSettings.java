package org.flippets.app;

import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;

/** A staged editor using Main's existing virtual cover and decoder. */
final class PetLayoutSettings {
    private PetLayoutSettings(){}
    static AlertDialog show(MainActivity a,CoverPreview preview){
        JSONObject pet=Pets.current(a);if(!PetLayout.supported(pet))return null;
        String id=pet.optString("id");SharedPreferences prefs=SceneSettings.prefs(a,id);UiTheme ui=a.ui;
        PetLayoutProfile[] profiles={PetLayout.read(prefs,false),PetLayout.read(prefs,true)};
        int[] mode={prefs.getBoolean("petClockless",false)?1:0};boolean[] refreshing={false};
        ViewGroup original=(ViewGroup)preview.getParent();int originalIndex=original.indexOfChild(preview);ViewGroup.LayoutParams originalParams=preview.getLayoutParams();
        ScrollView scroll=new ScrollView(a);LinearLayout panel=new LinearLayout(a);panel.setOrientation(1);panel.setPadding(ui.dp(18),ui.dp(10),ui.dp(18),ui.dp(20));panel.setBackgroundColor(ui.background);scroll.addView(panel);
        original.removeView(preview);LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(-2,-2);pp.gravity=Gravity.CENTER_HORIZONTAL;panel.addView(preview,pp);
        RadioGroup modes=new RadioGroup(a);modes.setOrientation(1);for(int i=0;i<2;i++){RadioButton b=new RadioButton(a);b.setId(i+100);b.setText(i==0?"С часами · нынешний размер":"Без часов · крупнее справа");b.setTextColor(ui.text);b.setTextSize(15);b.setMinHeight(ui.dp(48));modes.addView(b,new RadioGroup.LayoutParams(-1,-2));}modes.check(100+mode[0]);panel.addView(modes);
        TextView note=ui.label("Круглым питомцам увеличение ограничивает ширина: пропорции сохраняются. Камеры схематичны; после ручного смещения проверь голову и реакции на телефоне.",12,true);panel.addView(note,ui.spaced());
        JSONObject clips=pet.optJSONObject("clips");boolean video=false;if(clips!=null){java.util.Iterator<String> it=clips.keys();while(it.hasNext())if(clips.optString(it.next()).endsWith(".mp4")){video=true;break;}}
        if(video)panel.addView(ui.label("Убираются только часы приложения. Часы, нарисованные внутри видео, остаются. Положение MP4 в обычных живых обоях пока не меняется.",12,true),ui.spaced());
        TextView[] labels=new TextView[3];SeekBar[] sliders=new SeekBar[3];
        for(int i=0;i<3;i++){labels[i]=ui.label("",14,false);panel.addView(labels[i],ui.spaced());SeekBar seek=new SeekBar(a);seek.setMax(i==0?100:50);seek.setContentDescription(i==0?"Масштаб питомца":i==1?"Положение питомца по горизонтали":"Положение питомца по вертикали");seek.setProgressTintList(android.content.res.ColorStateList.valueOf(ui.primary));seek.setThumbTintList(android.content.res.ColorStateList.valueOf(ui.primary));panel.addView(seek,new LinearLayout.LayoutParams(-1,ui.dp(48)));sliders[i]=seek;}
        Runnable changed=()->{
            if(refreshing[0])return;
            PetLayoutProfile p=new PetLayoutProfile(mode[0]==1,(sliders[0].getProgress()+60)/100f,(sliders[1].getProgress()-25)/100f,(sliders[2].getProgress()-25)/100f);profiles[mode[0]]=p;
            labels[0].setText("Масштаб · "+Math.round(p.scale*100)+" % от автоматического");
            labels[1].setText("По горизонтали · "+direction(p.x,"влево","вправо"));labels[2].setText("По вертикали · "+direction(p.y,"вверх","вниз"));preview.stage.previewLayout(p);
        };
        Runnable refresh=()->{PetLayoutProfile p=profiles[mode[0]];refreshing[0]=true;sliders[0].setProgress(Math.round(p.scale*100)-60);sliders[1].setProgress(Math.round(p.x*100)+25);sliders[2].setProgress(Math.round(p.y*100)+25);refreshing[0]=false;changed.run();};
        for(SeekBar seek:sliders)seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar s,int progress,boolean user){if(user)changed.run();}public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}});
        modes.setOnCheckedChangeListener((g,checked)->{mode[0]=checked==101?1:0;refresh.run();});
        Button reset=ui.button("Автоматически · сбросить этот вариант",false,v->{profiles[mode[0]]=new PetLayoutProfile(mode[0]==1,1,0,0);refresh.run();});reset.setTag("pet-layout-reset");panel.addView(reset,ui.spaced());
        panel.addView(ui.label("Изменения пока видны только здесь. «Применить» сохраняет оба варианта для этого питомца и обновляет внешний экран.",12,true),ui.spaced());refresh.run();
        AlertDialog dialog=new AlertDialog.Builder(a).setTitle(pet.optString("name")+" · вариант и положение").setView(scroll).setPositiveButton("Применить",(d,w)->{PetLayout.save(a,id,mode[0]==1,profiles[0],profiles[1]);a.refreshSelection();}).setNegativeButton("Отмена",null).create();
        dialog.setOnDismissListener(d->{preview.stage.previewLayout(null);ViewGroup parent=(ViewGroup)preview.getParent();if(parent!=null)parent.removeView(preview);if(!a.isFinishing()&&!a.isDestroyed())original.addView(preview,Math.min(originalIndex,original.getChildCount()),originalParams);a.layoutDialog=null;});dialog.show();return dialog;
    }
    private static String direction(float value,String negative,String positive){int n=Math.round(value*100);return n==0?"по умолчанию":Math.abs(n)+" % "+(n<0?negative:positive);}
}
