#define main equipment_engine_main
#include "engine.cpp"
#undef main
int ix(int kind,int rad=0){for(int i=0;i<int(ITEMS.size());i++)if(ITEMS[i].kind==kind&&ITEMS[i].rad==rad)return i;return -1;}
int main(){
 Hero h{};h.kind=-1;h.hp=100000;h.a=h.m=0;h.as=0;h.ad=0;h.cap=1000000;h.role=0;
 Scenario sc{};Options o;o.skills=false;o.dps=300;o.targetRes=50;
 // Bramble and BT: no attack or spell damage; default must grant zero omnivamp.
 Build b=makeBuild({ix(BRAMBLE),ix(BLOOD),-1});
 auto r=Sim(h,sc,b,0,o).run();assert(r.damage>0&&r.vamp==0&&r.heal==0);
 o.itemVamp=true;auto upper=Sim(h,sc,b,0,o).run();assert(upper.vamp>0);o.itemVamp=false;
 // Wit's own explicit magic-damage heal is separate from generic BT omnivamp.
 h.as=1;b=makeBuild({ix(WITS),ix(BLOOD),-1});r=Sim(h,sc,b,0,o).run();assert(abs(r.heal-r.damage*.25)<1e-6);
 // Mitigation arithmetic: zero defenses and no shields, fixed 9000 raw damage in 30 seconds.
 h.as=0;b=makeBuild({-1,-1,-1});r=Sim(h,sc,b,0,o).run();assert(abs(r.raw-9000)<1e-6&&abs(r.hp-(h.hp-9000))<1e-6);
 // Armor 100 against a half-physical/half-magical input reduces total to 75%.
 h.a=100;r=Sim(h,sc,b,0,o).run();assert(abs(r.hp-(h.hp-9000*.75))<1e-6);h.a=0;
 // Defy does not multiply durability; the unexpired debt explains all extra remaining HP.
 b=makeBuild({ix(DEFY),-1,-1});r=Sim(h,sc,b,0,o).run();double full=9000*.5*(100./140+1);
 assert(abs(r.hp-(h.hp-full+r.debtLeft+r.debtForgiven))<1e-6);
 // Lifelines respond to nonlethal deferred ticks, not only to the next incoming packet.
 b=makeBuild({ix(DEFY),ix(BLOOD),-1});Sim s(h,sc,b,0,o);s.hp=s.H*.5-1;s.trigger();assert(s.blood&&s.totalShield()>0);
 cout<<"PASS: isolated item damage vs omnivamp; Wits explicit heal; raw damage; mixed mitigation; deferred damage accounting; deferred lifeline threshold\n";
}
