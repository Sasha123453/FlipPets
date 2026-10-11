package org.flippets.app;

public final class SharedPetGeometryTest {
    static void close(float actual,float expected){if(Math.abs(actual-expected)>.002)throw new AssertionError(actual+" != "+expected);}
    public static void main(String[] args){
        float scale=Float.parseFloat(args[0]),x=Float.parseFloat(args[1]),y=Float.parseFloat(args[2]);int cases=0;
        for(int width:new int[]{1208,604,302})for(boolean clockless:new boolean[]{false,true}){
            int height=width*1392/1208;float fit=width/1208f;
            CoverGeometry.Placement p=CoverGeometry.calibrated(width,height,scale,x,y,1140,1392,new PetLayoutProfile(clockless,1,0,0));
            close(p.scale,scale*fit);close(p.x,x*fit);close(p.y,y*fit);
            // Compare the body guide against the real native composition's reviewed
            // capybara-relative right edge and feet, rather than decorative bounds.
            close(p.x+812*p.scale,1140*fit);close(p.y+574*p.scale,1392*fit);cases++;
        }
        CoverGeometry.Placement manual=CoverGeometry.calibrated(1208,1392,scale,x,y,1140,1392,new PetLayoutProfile(false,1.1f,.05f,-.03f));
        close(manual.scale,scale*1.1f);close(manual.x+812*manual.scale,1140+.05f*1208);close(manual.y+574*manual.scale,1392-.03f*1392);cases++;
        for(float invalid:new float[]{Float.NaN,Float.POSITIVE_INFINITY,0,-1}){
            try{CoverGeometry.calibrated(1208,1392,invalid,x,y,1140,1392,PetLayoutProfile.CLOCK);throw new AssertionError("Invalid transform accepted");}
            catch(IllegalArgumentException expected){cases++;}
        }
        System.out.println(cases+" shared native/app geometry assertions passed");
    }
}
