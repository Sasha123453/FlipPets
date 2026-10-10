package org.flippets.uiqa;

import android.app.*;
import android.os.*;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.view.accessibility.*;
import android.graphics.Rect;
import android.util.*;
import java.io.*;
import java.util.*;
import org.xmlpull.v1.XmlSerializer;

/** Temporary shell-started test helper. Captures only our own UI and its document picker. */
public class DumpUi extends Instrumentation {
    public void onCreate(Bundle args){super.onCreate(args);start();}
    public void onStart(){Bundle result=new Bundle();int code=0;
        try{
            UiAutomation automation=getUiAutomation(UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES);
            AccessibilityServiceInfo info=automation.getServiceInfo();info.flags|=AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS|AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;automation.setServiceInfo(info);
            Thread.sleep(400);
            List<AccessibilityWindowInfo> windows=automation.getWindowsOnAllDisplays().get(0);
            File file=new File(getTargetContext().getExternalFilesDir(null),"primary-ui.xml");
            try(FileOutputStream out=new FileOutputStream(file)){
                XmlSerializer xml=Xml.newSerializer();xml.setOutput(out,"UTF-8");xml.startDocument("UTF-8",true);xml.startTag(null,"hierarchy");
                if(windows!=null)for(AccessibilityWindowInfo w:windows){AccessibilityNodeInfo root=w.getRoot();if(root==null)continue;String pkg=String.valueOf(root.getPackageName());
                    if(pkg.equals("org.flippets.app")||pkg.equals("com.google.android.documentsui")||pkg.equals("com.android.documentsui")||pkg.equals("moe.shizuku.privileged.api")){Rect clip=new Rect();w.getBoundsInScreen(clip);write(xml,root,clip);}
                }
                xml.endTag(null,"hierarchy");xml.endDocument();
            }
            result.putString("stream","Own primary display UI captured.\n");
        }catch(Throwable e){code=1;result.putString("stream",e.toString()+"\n");}
        finish(code,result);
    }
    void write(XmlSerializer xml,AccessibilityNodeInfo node,Rect clip)throws IOException {
        if(!node.isVisibleToUser())return;
        Rect r=new Rect();node.getBoundsInScreen(r);if(!r.intersect(clip))return;
        xml.startTag(null,"node");
        attr(xml,"text",node.getText());attr(xml,"package",node.getPackageName());attr(xml,"class",node.getClassName());attr(xml,"content-desc",node.getContentDescription());attr(xml,"resource-id",node.getViewIdResourceName());
        xml.attribute(null,"clickable",String.valueOf(node.isClickable()));xml.attribute(null,"checked",String.valueOf(node.isChecked()));xml.attribute(null,"enabled",String.valueOf(node.isEnabled()));
        xml.attribute(null,"bounds","["+r.left+","+r.top+"]["+r.right+","+r.bottom+"]");
        for(int i=0;i<node.getChildCount();i++){AccessibilityNodeInfo child=node.getChild(i);if(child!=null)write(xml,child,r);}
        xml.endTag(null,"node");
    }
    void attr(XmlSerializer xml,String key,CharSequence value)throws IOException{xml.attribute(null,key,value==null?"":value.toString());}
}
