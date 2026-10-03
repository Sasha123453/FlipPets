package org.flippets.app;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;

/** Settings are local and scoped to the selected composition. */
public final class SceneControls {
    static void note(Activity a,LinearLayout parent,String text){TextView v=new TextView(a);v.setTextColor(Color.WHITE);v.setText(text);v.setPadding(0,16,0,12);parent.addView(v);}
    static void button(Activity a,LinearLayout parent,String label,Runnable action){Button b=new Button(a);b.setText(label);b.setAllCaps(false);b.setOnClickListener(v->action.run());parent.addView(b);}
    static void changed(Activity a,PetStage preview){preview.reload();Pets.signal(a);}
    static void choose(Activity a,LinearLayout parent,String title,String key,String[] labels,String[] values,SharedPreferences p,PetStage preview){
        note(a,parent,title);Spinner s=new Spinner(a);s.setAdapter(new ArrayAdapter<>(a,android.R.layout.simple_spinner_dropdown_item,labels));s.setPopupBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.WHITE));int n=0;String current=p.getString(key,values[0]);for(int i=0;i<values.length;i++)if(values[i].equals(current))n=i;s.setSelection(n);parent.addView(s);
        s.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?> v){}public void onItemSelected(AdapterView<?> view,View child,int index,long row){if(!values[index].equals(p.getString(key,values[0]))){p.edit().putString(key,values[index]).apply();changed(a,preview);}}});
    }
    static void integer(Activity a,LinearLayout parent,String label,String key,String[] choices,SharedPreferences p,PetStage preview){
        button(a,parent,label,()->new AlertDialog.Builder(a).setTitle(label).setSingleChoiceItems(choices,p.getInt(key,0),(dialog,which)->{p.edit().putInt(key,which).apply();changed(a,preview);dialog.dismiss();}).setNegativeButton("Отмена",null).show());
    }
    static void toggle(Activity a,LinearLayout parent,String label,String key,boolean fallback,SharedPreferences p,PetStage preview){Switch s=new Switch(a);s.setText(label);s.setTextColor(Color.WHITE);s.setChecked(p.getBoolean(key,fallback));parent.addView(s);s.setOnCheckedChangeListener((v,yes)->{p.edit().putBoolean(key,yes).apply();changed(a,preview);});}
    static void edit(Activity a,LinearLayout parent,String label,String key,String fallback,int max,SharedPreferences p,PetStage preview){button(a,parent,label,()->{EditText value=new EditText(a);value.setText(p.getString(key,fallback));value.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(max)});value.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);new AlertDialog.Builder(a).setTitle(label).setView(value).setPositiveButton("Сохранить",(d,w)->{p.edit().putString(key,value.getText().toString()).apply();changed(a,preview);}).setNegativeButton("Отмена",null).show();});}
    static void slider(Activity a,LinearLayout parent,String label,String key,float fallback,float start,float range,SharedPreferences p,PetStage preview){note(a,parent,label);SeekBar s=new SeekBar(a);s.setMax(100);s.setProgress(Math.round((p.getFloat(key,fallback)-start)*100/range));parent.addView(s);s.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){}public void onProgressChanged(SeekBar b,int value,boolean user){if(user){p.edit().putFloat(key,start+range*value/100f).apply();changed(a,preview);}}});}
    public static void populate(MainActivity a,LinearLayout panel,JSONObject pet,PetStage preview){
        String id=pet.optString("id"),type=pet.optString("renderer");SharedPreferences p=SceneSettings.prefs(a,id);
        boolean glitter=pet.optString("name").equals("Flowing glitter");
        note(a,panel,glitter?"Четыре исходных эффекта, собственный фон и прозрачный передний слой. Наклон выбирает эффект и слегка смещает фотографию.":"Исходная графика Xiaomi; композиция адаптирована для MIX Flip и работает без root.");
        if(type.equals("stretch")||pet.optString("originalFile").startsWith("cc8f"))choose(a,panel,"Цвет часов","color",new String[]{"Синий","Фиолетовый","Зелёный","Оранжевый","Красный"},new String[]{"blue","purple","green","orange","red"},p,preview);
        if(type.equals("stretch")){integer(a,panel,"Расположение цифр","layout",new String[]{"Две строки","Одна строка"},p,preview);note(a,panel,"Касайся и тяни цифры: они растягиваются и возвращаются. Пружина адаптирована, системный движок Folme не используется.");}
        if(type.equals("signature")||type.equals("paper")||type.equals("calendar")){
            edit(a,panel,type.equals("calendar")?"Заголовок":"Текст подписи","signature",type.equals("paper")?"С Новым годом!":type.equals("calendar")?"Мой кинокалендарь":"Хорошего дня",80,p,preview);
            if(type.equals("calendar")){edit(a,panel,"Подпись к постеру","caption","Добавь постер и подпись в настройках",240,p,preview);note(a,panel,"Дата обновляется автоматически. Постер и подпись выбираются вручную; подключение к Douban отсутствует.");}
            else{integer(a,panel,"Расположение подписи","layout",new String[]{"По центру","Слева","Справа","Вертикально"},p,preview);integer(a,panel,"Шрифт Xiaomi","font",new String[]{"MiSans","Qinghe","Coca-Cola","Fangzheng"},p,preview);toggle(a,panel,"Жирный текст","bold",false,p,preview);button(a,panel,"Размер подписи",()->{EditText v=new EditText(a);v.setInputType(InputType.TYPE_CLASS_NUMBER);v.setText(Integer.toString(p.getInt("size",54)));new AlertDialog.Builder(a).setTitle("Размер: 24–100").setView(v).setPositiveButton("Сохранить",(d,w)->{try{p.edit().putInt("size",Math.max(24,Math.min(100,Integer.parseInt(v.getText().toString())))).apply();changed(a,preview);}catch(Exception e){a.message("Введи число от 24 до 100.");}}).setNegativeButton("Отмена",null).show();});}
        }
        if(type.equals("steps")){note(a,panel,"Шаги считаются только пока приложение или его живые обои видимы. Это собственный счётчик, без истории Mi Fitness. Дай разрешение на шаги выше.");button(a,panel,"Цель по шагам",()->{EditText v=new EditText(a);v.setInputType(InputType.TYPE_CLASS_NUMBER);v.setText(Integer.toString(p.getInt("goal",8000)));new AlertDialog.Builder(a).setTitle("Цель: 100–100000").setView(v).setPositiveButton("Сохранить",(d,w)->{try{p.edit().putInt("goal",Math.max(100,Math.min(100000,Integer.parseInt(v.getText().toString())))).apply();changed(a,preview);}catch(Exception e){a.message("Введи число.");}}).setNegativeButton("Отмена",null).show();});}
        if(!type.equals("stretch")&&!type.equals("analog")&&!type.equals("dragon")&&!type.equals("steps")){
            button(a,panel,"Выбрать фотографию / фон",()->a.pickImage(id,false));button(a,panel,"Прозрачный передний слой (PNG)",()->a.pickImage(id,true));
            button(a,panel,"Убрать свои изображения",()->{SceneSettings.clearImages(a,id);changed(a,preview);});
            slider(a,panel,"Масштаб фотографии","zoom",1,1,2,p,preview);slider(a,panel,"Сдвиг по горизонтали","panX",.5f,0,1,p,preview);slider(a,panel,"Сдвиг по вертикали","panY",.5f,0,1,p,preview);
            if(glitter)toggle(a,panel,"Реагировать на наклон","gravity",true,p,preview);
            else{choose(a,panel,"Фон","background",new String[]{"Тёмный","Синий","Зелёный","Бордовый","Светлый"},new String[]{"#182432","#274DA0","#244A39","#641C37","#EFE5D5"},p,preview);choose(a,panel,"Цвет текста","textColor",new String[]{"Светлый","Лайм","Красный","Тёмный"},new String[]{"#F4EDE4","#C5F36D","#F36A59","#182432"},p,preview);}
        }
        if(pet.optString("kind").equals("composition"))slider(a,panel,"Поле слева под камеры","safeCamera",.34f,.15f,.4f,p,preview);
        if(pet.optString("kind").equals("composition"))toggle(a,panel,"Приглушённое оформление","dim",false,p,preview);
    }
}
