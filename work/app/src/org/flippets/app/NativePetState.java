package org.flippets.app;

import org.json.*;

/** Converts private OEM state to fixed labels/counts; never returns paths, photos or custom names. */
final class NativePetState {
    static final int MAX_JSON=2*1024*1024;
    static final String[] NAMES={"Другое оформление","Девон-рекс","Капибара","Выдра","Бишон-фризе","Сиамский кот","Чёрная пантера"};
    static String title(JSONObject item){
        JSONObject pets=item.optJSONObject("pets");if(pets==null)return NAMES[0];
        JSONObject ai=pets.optJSONObject("aiPetsData");
        if(ai!=null)return ai.optString("bizId").matches("flippets-charlie-[0-9a-f]{32}")?"Charlie · Flip Pets":"Другой AI-питомец";
        int type=pets.optInt("petType",0);return type>=1&&type<=6?NAMES[type]:"Другой питомец";
    }
    static String summarize(String current,String all)throws JSONException {
        if(current==null||all==null||current.length()>MAX_JSON||all.length()>MAX_JSON)throw new JSONException("Native state size");
        JSONArray history=new JSONArray(all);if(history.length()>9)throw new JSONException("Unknown native quota");
        String selected=current.trim().equals("null")?"Не выбрано":title(new JSONObject(current));int count=0;StringBuilder labels=new StringBuilder();
        for(int i=0;i<history.length();i++){JSONObject item=history.getJSONObject(i);if(item.optJSONObject("pets")!=null){count++;labels.append("\n• ").append(title(item));}}
        if(count>3)throw new JSONException("Unknown native pet quota");
        return "Сейчас: "+selected+"\nМеста питомцев: "+count+" / 3 · свободно "+(3-count)+"\nВсе оформления: "+history.length()+" / 9"+labels;
    }
}
