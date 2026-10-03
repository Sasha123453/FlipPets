package org.flippets.app;

public class PetStateTest {
    static void expect(int actual,int expected,String scenario){if(actual!=expected)throw new AssertionError(scenario+": "+actual+" != "+expected);}
    public static void main(String[] args){
        PetState p=new PetState();expect(p.index(1000),0,"idle");
        p.rain=true;expect(p.index(1000),7,"rain");p.lowBattery=true;expect(p.index(1000),6,"low beats rain");
        p.charging=true;expect(p.index(1000),5,"charge beats low");p.notificationUntil=2000;expect(p.index(1000),4,"notification beats charge");
        p.music=true;expect(p.index(1000),3,"music beats notification");p.step(1000);expect(p.index(1000),2,"walk beats music");
        p.step(1300);expect(p.index(1300),1,"fast cadence becomes run");p.step(1800);expect(p.index(1800),2,"slower cadence becomes walk");
        p.overrideIndex=12;p.overrideUntil=1900;expect(p.index(1850),12,"tap overrides events");expect(p.index(1900),2,"tap expires exactly");
        expect(p.index(3700),3,"movement expires exactly");p.music=false;expect(p.index(3700),5,"old notification expires");
        p.charging=false;p.lowBattery=false;p.rain=false;expect(p.index(4000),0,"return to idle");
        PetState shared=new PetState();shared.sensorStep(100,5000);shared.sensorStep(100,5002);expect(shared.index(5002),2,"duplicate step from the second display remains walking");shared.sensorStep(101,5300);expect(shared.index(5300),1,"a genuinely new fast step runs");
        System.out.println("PASS: event priorities, cadence boundaries, expiry and duplicate sensor events across displays");
    }
}
