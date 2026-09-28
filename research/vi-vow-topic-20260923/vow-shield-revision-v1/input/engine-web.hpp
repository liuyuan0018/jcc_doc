// Conditional 30 Hz single-frontline equipment benchmark. Not a game-client emulator.
// Inputs and approximation contracts are documented in report.md and mechanics.md.
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <numeric>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
#include "generated.hpp"
using namespace std;
constexpr double EPS=1e-8;
struct Options {
 int fps=30,seconds=180,frequency=3,lock=30,pause=9,edgeFrames=15,stage=4;
 double physicalShare=.5,wound=0;int woundStart=0,woundEnd=5400,resistanceMode=0;
 double dps=1400,targetRes=50,targetHP=3000,axe=.04,dawn=.15,post=.03,aoeVamp=1;
 int attackers=1;bool soloPlate=false;
 int allyPeriod=120,allyDeath=1000000;
 bool skills=true,shieldMana=true,control=false,itemVamp=false,gunSelf=false,trace=false;
};
struct Build {
 array<int,3> ids;int cat=0;unsigned char c[NK][2]{};
 double hp=0,a=0,m=0,ap=0,ad=0,as=0,crit=0,regen=0,sv=0,dr=1,da=0,critmult=0,hpp=0;
 int n(int k) const{return c[k][0]+c[k][1];}
 double w(int k,double normal,double rad)const{return c[k][0]*normal+c[k][1]*rad;}
};
Build makeBuild(array<int,3> ids,int glove=0){
 Build b;b.ids=ids;int na=0,nr=0,np=0;
 for(int i:ids)if(i>=0){auto e=ITEMS[i];b.c[e.kind][e.rad]++;b.hp+=e.hp;b.a+=e.a;b.m+=e.m;b.ap+=e.ap;b.ad+=e.ad;b.as+=e.as;b.crit+=e.crit;b.regen+=e.regen;b.sv+=e.sv;b.dr*=1-e.dr;b.da+=e.da;b.critmult+=e.critmult;na+=e.cat==2;nr+=e.cat==1;np+=e.cat==3;}
 b.cat=np?5:na>1||nr>1?4:na&&nr?3:na?2:nr?1:0;
 if(glove){b.hp+=150;b.crit+=.2;b.cat=glove==1?6:7;}
 b.hpp=b.w(WARMOG,.18,.36)+b.w(BRAMBLE,.06,.12)+b.w(DCLAW,.06,.28)+b.w(SUNFIRE,.08,.16)+b.n(UNBREAKABLE)*.15;
 return b;
}
bool legal(array<int,3> ids){for(int id:ids)if(id>=0&&ITEMS[id].cat==3)return false;for(int j=1;j<3;j++)if(ids[j]>=0&&ids[j]==ids[j-1]&&(ITEMS[ids[j]].unique||ITEMS[ids[j]].cat==2))return false;return true;}
struct Result {
 int frame=0,casts=0,attacks=0,spiderAttacks=0;bool alive=true;
 double hp=0,H=0,initialHP=0,shield=0,heal=0,overheal=0,vamp=0,skillHeal=0,spiderHeal=0,damage=0,granted=0,used=0,lost=0,converted=0,growth=0,raw=0,avoided=0,ccAvoided=0,deferred=0,debtPaid=0,debtForgiven=0,debtLeft=0,mana=0,mpInitial=0,mpGain=0,mpSpent=0,mpBlocked=0,mpOverflow=0,mpAttack=0,mpDamage=0,mpRegen=0,mpSpecial=0,minHP=1e30;
};
struct Shield{double value=0,decay=0;int end=0,tag=0;};
struct Hot{double heal=0,physical=0,magic=0;int end=0;bool aoe=false;};
struct Sim {
 const Hero& h;const Scenario& sc;const Build& b;Options o;Result r;int aug,f=0,F,limit,hitInterval;
 double hp,H,A,M,healthFactor,mp,cap,attackCharge=0,extraA=0,extraM=0,bonusAP=0,bonusAD=0;
 double lastAmp=1,lastAD=1,crit=0,critFactor=1,spellCrit=1,sv=0,ampDamage=1;
 double burnEnd[3]{},burnRatio[3]{},enemyA[3],enemyM[3],flatA[3]{},flatM[3]{},lastJewel[3]{},shredA[3]{},shredM[3]{};
 int enemyStun[3]{},locked=0,paused=0,eliseEnd=0,viEnd=0,reksaiEnd=0,resEnd=0,drEnd=0;
 int titan=0,mogul=0,shenCharges=0,taricCharges=0,lichCharges=0,manazaneRemaining=0,manaPotRemaining=0,manazaneStart=0,potStart=0;
 int edgeUntil=0,zhonyaUntil=0,brambleReady=0,ascended=0,flailExpiry=0;double flailStacks=0,treeBlocked=0;
 bool transformed=false,half=false,vow=false,sterak=false,blood=false,edge=false,zhonya=false,taric=false,sett=false,healthPot=false;
 bool kobukoSmash=false,covenantDied=false;
 array<Shield,16> shields{};int ns=0;array<Hot,8> hots{};int nh=0;
 array<double,121> debtChanges{};double debtRate=0;
 bool capture=true;
 struct WebEvent {int frame;string kind;double value;};
 vector<array<double,19>> frames;
 vector<WebEvent> events;
 struct PresentationEvent {int frame;string kind;double amount;string source;};
 vector<array<double,4>> attributes;
 vector<PresentationEvent> presentationEvents;
 void presentationEvent(const char* kind,double amount,const char* source){if(capture)presentationEvents.push_back({f,kind,amount,source});}
 void snapshot(){if(!capture)return;frames.push_back({double(f),max(0.,hp),H,totalShield(),mp,cap,double(max(0,locked-f)),double(max(0,paused-f)),double(r.casts),double(r.attacks),r.heal,r.used,r.damage,defenses(true),defenses(false),double(transformed),double(f<zhonyaUntil||f<edgeUntil),double(r.alive),r.mpBlocked});attributes.push_back({double(f),defenses(true),defenses(false),100*abilityPowerMultiplier()});}
 ostream* trace=nullptr;
 Sim(const Hero& hh,const Scenario& ss,const Build& bb,int aa,const Options& oo,ostream* tt=nullptr):h(hh),sc(ss),b(bb),o(oo),aug(aa),F(o.fps),limit(o.seconds*o.fps),hitInterval(o.fps/o.frequency),trace(tt){
  r.frame=limit;
  double brawl=sc.brawl==2?.25:sc.brawl==4?.4:sc.brawl==6?.65:0;
  healthFactor=1+b.hpp+brawl+(o.soloPlate&&b.c[GARGOYLE][0]?.17:0);H=(h.hp+b.hp+((aug&2)?600:0)+400*b.n(HULL))*healthFactor;hp=H;
  double guard=sc.guard==2?25:sc.guard==4?60:sc.guard==6?120:0;
  A=h.a+b.a+guard+b.w(GARGOYLE,10,20)*o.attackers+(h.role<2?b.w(HELM,30,80):0);
  M=h.m+b.m+guard+b.w(GARGOYLE,10,20)*o.attackers+(h.role<2?b.w(HELM,30,80):0);
  mp=h.mp;cap=max(15.,h.cap-10*b.n(DAWNCORE));r.initialHP=H;r.mpInitial=mp;
  for(int i=0;i<3;i++){enemyA[i]=enemyM[i]=o.targetRes;lastJewel[i]=-1000;}
 }
 void event(const string& k,double v=0){if(capture)events.push_back({f,k,v});if(trace)*trace<<f<<','<<fixed<<setprecision(6)<<double(f)/F<<','<<k<<','<<v<<','<<hp<<','<<H<<','<<mp<<','<<totalShield()<<'\n';}
 double heal(double v,int src=0){v=max(0.,v);if(!b.n(MITTENS)&&f>=o.woundStart&&f<o.woundEnd)v*=1-o.wound;double actual=min(max(0.,H-hp),v);hp+=actual;r.heal+=actual;r.overheal+=v-actual;if(src==1)r.vamp+=actual;if(src==2)r.skillHeal+=actual;if(src==3)r.spiderHeal+=actual;if(actual>0)presentationEvent("heal",actual,src==1?"lifesteal":src==2?"skill":src==3?"spider":"other");return actual;}
 void grow(double v){H+=v;hp+=v;r.growth+=v;if(v!=0)presentationEvent("healthGrowth",v,"maxHealth");}
 double totalShield()const{double z=0;for(int i=0;i<ns;i++)z+=shields[i].value;return z;}
 bool skillShield()const{for(int i=0;i<ns;i++)if(shields[i].tag==0&&shields[i].value>EPS)return true;return false;}
 void removeShield(int i){shields[i]=shields[--ns];}
 void shield(double v,int dur,int tag,double decay=0){
  double before=capture?totalShield():0;
  double conv=min(1.,.4*b.n(IDOL))*v;if(conv){grow(conv*healthFactor);r.converted+=conv;v-=conv;decay*=1-min(1.,.4*b.n(IDOL));}
  for(int i=0;i<ns;i++)if(shields[i].tag==tag){r.lost+=shields[i].value;presentationEvent("shieldReplace",shields[i].value,"sameTag");removeShield(i);break;}
  if(v>EPS){assert(ns<16);shields[ns++]={v,decay,f+dur,tag};r.granted+=v;presentationEvent("shieldGain",v,"grant");}
  if(capture&&before>EPS&&totalShield()<=EPS)presentationEvent("shieldBreak",0,"replacement");
 }
 void hot(double value,int frames,double physical=0,double magic=0,bool aoe=false){assert(nh<8);hots[nh++]={value/frames,physical/frames,magic/frames,f+frames,aoe};}
 void gain(double v,int src,bool bypass=false){
  if(v<=0)return;v*=1+b.w(HELM,.15,.30);
  if(f<locked&&!bypass){r.mpBlocked+=v;return;}
  double actual=min(v,max(0.,cap-mp));mp+=actual;r.mpGain+=actual;r.mpOverflow+=v-actual;
  if(src==0)r.mpAttack+=actual;else if(src==1)r.mpDamage+=actual;else if(src==2)r.mpRegen+=actual;else r.mpSpecial+=actual;
  if(trace)event("mana"+to_string(src),actual);
 }
 double abilityPowerMultiplier()const{
  double justice=b.w(JUSTICE,.18,.35)*(hp>H*.5?2:1);
  double blue=1+b.w(BLUE,.10,.20);
  return (1+b.ap+bonusAP+justice+b.n(HULL)*.1+(h.role==2?b.w(HELM,.1,.4):0)+b.w(ARCHANGEL,.20,.40)*(f/(5*F))+(f>=8*F?b.w(CROWN,.25,.50):0)+b.w(TITAN,.02,.04)*titan+b.n(FLICKER)*.02*(r.attacks/3))*blue;
 }
 void stats(){
  double justice=b.w(JUSTICE,.18,.35)*(hp>H*.5?2:1);
  double blue=1+b.w(BLUE,.10,.20);
  lastAmp=abilityPowerMultiplier();
  lastAD=(1+b.ad+bonusAD+justice+b.n(HULL)*.1+(h.role==2?b.w(HELM,.1,.4):0)+b.w(TITAN,.02,.04)*titan+b.w(KRAKEN,.035,.07)*min(15,r.attacks)+b.n(FLICKER)*.02*(r.attacks/3))*blue;
  double cc=.25+b.crit;crit=min(1.,cc);critFactor=1+crit*(.4+b.critmult+.5*max(0.,cc-1)+.1*max(0,b.n(IE)+b.n(JG)-1));spellCrit=b.n(IE)+b.n(JG)?critFactor:1;
  sv=b.sv+b.w(JUSTICE,.15,.30)*(hp<H*.5?2:1);
  ampDamage=1+b.da+(ascended?1.2*b.n(ASCENSION):0)+(titan>=25?b.w(TITAN,.10,.20):0)+b.w(FLAIL,.05,.10)*flailStacks;
 }
 double res(double x){return x>=0?100/(100+x):2-100/(100-x);}
 // Target dummies do not die: no kill-trigger stats or reduction of the prescribed input DPS.
 // Damage quantities are mitigated against target resistances, not a fabricated constant heal budget.
 double deal(double physical,double magic,int target=0,bool spell=false,bool item=false,bool aoe=false){
  if(physical+magic<=0)return 0;
  if(b.n(LASTWHISPER)&&!item)shredA[target]=max(shredA[target],.3);
  if(b.n(VOIDSTAFF)&&!item)shredM[target]=max(shredM[target],.3);
  double am=(b.n(EVENSHROUD)?max(.3,shredA[target]):shredA[target]);double mm=(b.n(IONIC)?max(.3,shredM[target]):shredM[target]);
  double ar=max(0.,enemyA[target]-flatA[target])*(1-am),mr=max(0.,enemyM[target]-flatM[target])*(1-mm);
  double phys=physical*res(ar),mag=magic*res(mr);double critScale=spell?spellCrit:1;
  double damageScale=item?1:ampDamage;double d=(phys+mag)*damageScale*critScale;r.damage+=d;
  double vampEligible=(!item||o.itemVamp)?d:0;
  heal(vampEligible*(sv+(o.gunSelf?b.w(GUNBLADE,.2,.4):0))*(aoe?o.aoeVamp:1),1);
  if(mag>0&&b.n(WITS))heal(mag*damageScale*critScale*.25*b.n(WITS),1);
  if(!item&&(b.n(RED)||b.n(MORELLO))){burnEnd[target]=max(burnEnd[target],double(f+(b.n(MORELLO)?10:5)*F));burnRatio[target]=max(burnRatio[target],b.c[RED][1]||b.c[MORELLO][1]?.02:.01);}
  if(mag>0&&b.n(BLIGHT)&&f-lastJewel[target]>=.5*F){if(mr<=EPS)gain(4*b.n(BLIGHT),3);else flatM[target]+=3*b.n(BLIGHT);lastJewel[target]=f;}
  return d;
 }
 void aoe(double p,double m,bool spell=true,bool item=false){for(int j=0;j<3;j++)deal(p,m,j,spell,item,true);}
 void stun(double secs,int n=3){if(o.control)for(int j=0;j<n;j++)enemyStun[j]=max(enemyStun[j],f+int(round(secs*F)));}
 void cast(){
  if(!o.skills)return;
  double spent=mp;r.casts++;r.mpSpent+=mp;mp=0;locked=f+o.lock;if(h.kind!=12&&h.kind!=11)paused=f+o.pause;
  if(b.n(DAWNCORE)&&r.casts>1)cap=max(15.,cap*pow(.95,b.n(DAWNCORE)));
  if(r.casts==1){manazaneRemaining=b.n(MANAZANE)?5*F:0;manazaneStart=f;manaPotRemaining=b.n(MANAPOT)?5*F:0;potStart=f;}
  lichCharges=1;stats();event("cast",r.casts);
  const auto& v=h.v;double ap=lastAmp,ad=lastAD;
  switch(h.kind){
   case 0:shield(v[0]*ap,4*F,0);aoe(0,v[1]*ap);break;
   case 1:shield(v[0]*ap,4*F,0);break; // Rakan ally AS is excluded by the fixed support-ally contract.
   case 2:deal(0,v[1]/100*defenses(true),0,true);stun(1.5,1);break;
   case 3:hot(.07*H+v[0]*ap,2*F);locked=paused=f+2*F;kobukoSmash=true;break;
   case 4:reksaiEnd=f+3*F;aoe(0,v[1]*ap);stun(1);break;
   case 5:hot(v[1]*ap,3*F);drEnd=f+3*F;locked=paused=f+3*F;break;
   case 6:heal(.08*H+v[0]*ap,2);deal(0,v[2]*ap,0,true);stun(1.5,1);break;
   case 7:shield(.1*H+v[0]*ap,4*F,0);aoe(0,v[1]*ap);deal(0,v[2]*ap,0,true);break;
   case 8:shield(v[0]*ap,4*F,0);shenCharges=3;break;
   case 9:if(!transformed){transformed=true;grow(v[0]*healthFactor);}else eliseEnd=f+4*F;break;
   case 10:heal(v[2]*ap,2);deal(v[1]*ad,0,0,true);break;
   case 11:hot(v[0]*ap,3*F);resEnd=f+3*F;locked=f+3*F;aoe(0,v[1]*ap);stun(v[2]);break;
   case 12:heal(v[1]*ap,2);viEnd=drEnd=f+3*F;break;
   case 13:for(int j=0;j<3;j++)flatM[j]+=10;hot(v[0]*ap,2*F,0,v[1]*ap,true);locked=paused=f+2*F;break;
   case 14:grow(v[1]*ap*healthFactor);deal(v[2]*ad+.08*H,0,0,true);break;
   case 15:shield(v[1]*ap,2*F,0);aoe(0,2*v[0]*ap);break;
   case 16:shield(v[0]*ap,4*F,0);break;
   case 17:shield(.1*H+v[0]*ap,4*F,0);aoe(0,v[1]*ap);break;
   case 18:heal(v[0]*ap,2);aoe(0,v[1]*ap);deal(0,v[1]*ap,0,true);stun(v[2]);break;
   case 19:aoe(0,v[2]*ap);stun(h.star==3?6:1);break;
   case 20:heal(.12*H+v[0]*ap,2);aoe(v[1]*ad+.06*H,0);break;
   case 21:deal(0,v[2]/100*H,0,true);heal(v[3]*ap+(h.star==3?1:.1)*(H-hp),2);break;
   case 22:heal(v[1]*ap,2);taricCharges=2;break;
   case 23:if(!transformed){transformed=true;grow(v[2]*healthFactor);cap=max(15.,50.-10*b.n(DAWNCORE));for(int j=0;j<3;j++){flatA[j]+=v[1]*ap;flatM[j]+=v[1]*ap;}aoe(v[0]*ad,0);stun(1);}else {deal(v[3]*ad,0,0,true);for(int j=1;j<3;j++)deal(v[4]*ad,0,j,true,true,true);}break;
  }
  (void)spent;
 }
 void attack(){
  r.attacks++;titan=min(25,titan+1);stats();
  double p=h.ad*lastAD*critFactor,m=0;
  if(h.kind==5&&o.skills){p=h.v[0]*lastAD*critFactor;aoe(p,0,false);p=0;}
  if(h.kind==3&&kobukoSmash&&o.skills){p=0;m+=.1*H+h.v[1]*lastAmp;kobukoSmash=false;}
  deal(p,m,0,false);
  if(o.skills){
   if(h.kind==9&&transformed){r.spiderAttacks++;heal(h.v[2]*lastAmp,3);deal(0,h.v[1]*lastAmp,0,true);}
   if(h.kind==12)heal(.02*H,2);
   if(h.kind==8&&shenCharges){deal(0,h.v[2]*lastAmp,0,true);shenCharges--;}
   if(h.kind==22&&taricCharges){deal(0,h.v[2]*lastAmp,0,true);taricCharges--;}
  }
  if(b.n(AXE))deal(o.axe*H*b.n(AXE),0,0,false,true);
  if(b.n(HYDRA))aoe((.02*H+.04*h.ad*lastAD)*b.n(HYDRA),0,false,true);
  if(b.n(WITS)){double dmg[5]={25,45,65,85,100};deal(0,dmg[min(4,max(0,o.stage-2))]*b.n(WITS),0,false,true);}
  if(b.n(LICH)&&lichCharges){double dmg[5]={250,350,500,600,700};deal(0,dmg[min(4,max(0,o.stage-2))]*b.n(LICH),0,false,true);lichCharges=0;}
  if(b.n(STATIKK)&&r.attacks%3==0)aoe(0,(15+.35*(lastAmp-1)*100)*b.n(STATIKK),false,true);
  if(b.n(SILVERMERE))stun(.8,1);
  if(b.n(FLAIL)){flailStacks=min(4.,flailStacks+crit);flailExpiry=f+5*F;}
  double mana=h.role==0?5:h.role==1?10:(h.star==3?20:5);
  gain(mana+b.w(SHOJIN,5,10)+b.w(NASHOR,2,4)+2*crit*b.n(NASHOR),0);event("attack",r.attacks);
 }
 double defenses(bool armor){
  double v=(armor?A:M)+(armor?extraA:extraM)+mogul;
  v+=(f<15*F?b.c[EVENSHROUD][0]*15:0)+(f<20*F?b.c[EVENSHROUD][1]*50:0);
  if(o.skills&&h.kind==2)v+=h.v[0]*lastAmp*max(0.,1-double(f)/(12*F));
  if(o.skills&&((h.kind==11&&f<resEnd)||(h.kind==16&&skillShield())))v+=h.kind==11?50:60;
  return v>0&&((armor?1:2)&o.resistanceMode)?v*.7:v;
 }
 void trigger(){
  if(hp<=0)return;
  if(!half&&sc.z&&hp<=.5*H){half=true;shield((sc.z==2?.18:sc.z==4?.3:.4)*H,10*F,2);}
  if(!vow&&b.n(VOW)&&hp<=.4*H){vow=true;gain(b.w(VOW,15,30),3,true);bool normalGranted=false;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==VOW){if(!ITEMS[b.ids[j]].rad){if(normalGranted)continue;normalGranted=true;}shield((ITEMS[b.ids[j]].rad?.5:.2)*H,limit,3+j);}}
  if(!blood&&b.n(BLOOD)&&hp<=.5*H){blood=true;bool normalGranted=false;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==BLOOD){if(!ITEMS[b.ids[j]].rad){if(normalGranted)continue;normalGranted=true;}shield((ITEMS[b.ids[j]].rad?.6:.3)*H,5*F,6+j);}}
  if(!sterak&&b.n(STERAK)&&hp<=.6*H){sterak=true;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==STERAK){double ratio=ITEMS[b.ids[j]].rad?.8:.4;int duration=ITEMS[b.ids[j]].rad?6:4;shield(ratio*H,duration*F,9+j,ratio*H/(duration*F));}}
  if(!edge&&b.n(EDGE)&&hp<=.4*H){edge=true;heal((H-hp)*(b.c[EDGE][1]?1:1-pow(.85,b.c[EDGE][0])));edgeUntil=f+o.edgeFrames;event("edge",o.edgeFrames);}
  if(!zhonya&&b.n(ZHONYA)&&hp<=.4*H){zhonya=true;zhonyaUntil=f+3*F;paused=max(paused,zhonyaUntil);event("zhonya",3);}
  if(!healthPot&&b.n(HEALTHPOT)&&hp<=.5*H){healthPot=true;hot(b.w(HEALTHPOT,750,850),3*F);}
  if(o.skills&&h.kind==22&&!taric&&hp<=.5*H){taric=true;shield((h.star==3?1:.15)*H+h.v[0],(h.star==3?99:3)*F,12);}
  if(o.skills&&h.kind==20&&!sett&&hp<=.4*H){sett=true;gain(100,3,true);}
 }
 void incoming(int enemy){
  double raw=o.dps/o.frequency;r.raw+=raw;
  if(f<edgeUntil||f<zhonyaUntil){r.avoided+=raw;return;}
  if(f<enemyStun[enemy]){r.ccAvoided+=raw;return;}
  double jug=sc.jug==2?.2:sc.jug==4?.33:sc.jug==6?.45:0;
  double mul=b.dr*(1-jug)*((aug&2)?.85:1)*pow(hp>.5*H?.85:.95,b.c[STEADFAST][0])*pow(hp>.5*H?.7:.9,b.c[STEADFAST][1]);
  if(sc.z==6&&ns)mul*=.95;if(f<drEnd)mul*=.85;
  double dmg=(o.physicalShare==.5?raw*.5*(pow(.95,b.c[BRAMBLE][0])*pow(.90,b.c[BRAMBLE][1])*res(defenses(true))+res(defenses(false))):raw*(o.physicalShare*pow(.95,b.c[BRAMBLE][0])*pow(.90,b.c[BRAMBLE][1])*res(defenses(true))+(1-o.physicalShare)*res(defenses(false))))*mul;
  double post=dmg;bool rammusBefore=h.kind==16&&skillShield();
  double usedBefore=capture?r.used:0,shieldBefore=capture?totalShield():0;
  // Expiring shields absorb first. At most 16, no heap allocation in the inner loop.
  while(dmg>EPS&&ns){int k=0;for(int j=1;j<ns;j++)if(shields[j].end<shields[k].end)k=j;double take=min(dmg,shields[k].value);shields[k].value-=take;dmg-=take;r.used+=take;if(shields[k].value<EPS)removeShield(k);}
  if(capture&&r.used>usedBefore)presentationEvent("shieldAbsorb",r.used-usedBefore,"incoming");
  if(capture&&shieldBefore>EPS&&totalShield()<=EPS)presentationEvent("shieldBreak",0,"damage");
  if(b.n(DEFY)&&dmg>0){double deferred=.5*dmg;dmg-=deferred;double rate=deferred/(4*F);debtRate+=rate;debtChanges[(f+4*F+1)%(4*F+1)]-=rate;r.deferred+=deferred;}
  if(dmg>0)presentationEvent("damage",min(max(0.,hp),dmg),"incoming");
  hp-=dmg;
  if(hp<=0){r.alive=false;r.frame=f;return;}
  if(h.role==0)gain(min(42.5,.01*raw+o.post*(o.shieldMana?post:dmg)),1);
  if(b.n(MOGUL)&&mogul<35){mogul++;grow(5*healthFactor);}
  if(b.n(TITAN))titan=min(25,titan+1);
  if(h.kind==21&&o.skills){treeBlocked+=max(0.,raw-post);const double blockThreshold=h.star==3?300:650;while(treeBlocked>=blockThreshold){treeBlocked-=blockThreshold;deal(0,h.v[0]/100*H,0,true);}}
  if(rammusBefore&&!skillShield()&&o.skills)aoe((o.resistanceMode?((A+extraA+mogul+60)*(o.resistanceMode&1?.7:1)+(M+extraM+mogul+60)*(o.resistanceMode&2?.7:1)):(A+M+extraA+extraM+2*mogul+120))*h.v[1]/100,0);
  if(b.n(BRAMBLE)&&f>=brambleReady){aoe(0,b.w(BRAMBLE,100,200),false,true);brambleReady=f+2*F;}
  trigger();event("incoming",post);
 }
 bool started=false,finished=false;long long executedTicks=0;
 int advance(int budget){
  if(budget<=0||finished)return 0;
  if(!started){started=true;
  gain(b.w(VOW,20,40)+20*b.n(MANAPOT),3,true);
  if(sc.z)shield((sc.z==2?.18:sc.z==4?.3:.4)*H,10*F,1);
  for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==CROWN)shield((ITEMS[b.ids[j]].rad?.5:.25)*H,8*F,13+j);
  }
  const int begin=f,end=min(limit+1,f+budget);
  for(;f<end;f++){
   double beforeExpiry=capture?totalShield():0;
   for(int j=0;j<ns;){if(shields[j].end<=f){r.lost+=shields[j].value;presentationEvent("shieldExpire",shields[j].value,"duration");removeShield(j);}else{if(f&&shields[j].decay){double take=min(shields[j].value,shields[j].decay);shields[j].value-=take;r.lost+=take;if(take>0)presentationEvent("shieldDecay",take,"decay");}if(shields[j].value<EPS)removeShield(j);else j++;}}
   if(capture&&beforeExpiry>EPS&&totalShield()<=EPS)presentationEvent("shieldBreak",0,"lifetime");
   if(f>=flailExpiry)flailStacks=0;stats();
   if(f){
    if(f<zhonyaUntil){}else{
     double asBonus=b.as+(h.role==1?.2:0)+b.w(RAGE,.07,.16)*(f/F)+b.w(QSS,.03,.06)*(f/F)+b.n(FLICKER)*.04*r.attacks+b.n(GAMBLER)*.3;
     if(b.n(AXE))asBonus+=b.n(AXE)*1.5*(1-hp/H);
     if(r.attacks>=15)asBonus+=b.w(KRAKEN,.15,.30);
     if(f<eliseEnd)asBonus+=1.75*double(eliseEnd-f)/(4*F);
     if(f<viEnd)asBonus+=h.v[2]/100;
     if(shenCharges)asBonus+=.4;
     double as=b.n(SILVERMERE)?.5:min(5.,h.as*(1+asBonus));
     if(f>=paused)attackCharge+=as/F;
     while(attackCharge>=1-EPS){attackCharge-=1;attack();}
    }
    double regen=b.regen+(h.kind==23?(h.star==3?50:5):0)+(ascended?12*b.n(ASCENSION):0)+(covenantDied?10*b.n(COVENANT):0);
    gain(regen/F,2);
    if(manazaneRemaining>0&&f>manazaneStart&&f>=locked){gain(110.*b.n(MANAZANE)/(5*F),3);manazaneRemaining--;}
    if(manaPotRemaining>0&&f>potStart&&f>=locked){gain(b.w(MANAPOT,80,90)/(5.*F),3);manaPotRemaining--;}
    for(int j=0;j<nh;){auto z=hots[j];heal(z.heal,2);if(z.aoe)aoe(z.physical,z.magic);else deal(z.physical,z.magic,0,true);if(f>=z.end)hots[j]=hots[--nh];else j++;}
    if(f%F==0){
     if(o.skills&&h.kind==19){heal((h.star==3?.04:.025)*H+h.v[0]*lastAmp,2);aoe(0,h.v[1]*lastAmp);}
     if(o.skills&&h.kind==4)heal((.01*H+h.v[0])*(f<reksaiEnd?3:1),2);
     heal(b.w(VISAGE,.02,.04)*(H-hp));
     for(int j=0;j<3;j++)if(f<burnEnd[j])deal(0,0,j); // burn is true damage; separately accounted below.
     for(int j=0;j<3;j++)if(f<burnEnd[j]){double d=o.targetHP*burnRatio[j];r.damage+=d;if(o.itemVamp)heal(d*sv,1);}
    }
    if(f%(2*F)==0){heal(b.w(DCLAW,.025,.05)*H);if(b.n(SUNFIRE)){int target=(f/(2*F)-1)%3;burnEnd[target]=f+10*F;burnRatio[target]=max(burnRatio[target],b.c[SUNFIRE][1]?.02:.01);}}
    if((aug&1)&&f%(10*F)==0)grow(16*b.c[STEADFAST][0]*healthFactor);
    if(b.n(LIGHTSHIELD)&&f%(3*F)==0)shield(.7*(defenses(true)+defenses(false))*b.n(LIGHTSHIELD),5*F,16);
    if(b.n(DAWN)||b.n(DUSK)){
     double interval=(b.n(DAWN)&&b.n(DUSK)?1.25:2.5)*F;
     if(int(f/interval)>int((f-1)/interval)){
      for(int j=0;j<3;j++){double sa=min(3.*b.n(DAWN),max(0.,enemyA[j]-flatA[j]));double sm=min(3.*b.n(DUSK),max(0.,enemyM[j]-flatM[j]));extraA+=sa;extraM+=sm;flatA[j]+=sa;flatM[j]+=sm;}
      if(b.n(DAWN))heal(o.dawn*defenses(true)*b.n(DAWN));
      if(b.n(DUSK))aoe(0,.18*defenses(false)*b.n(DUSK),false,true);
     }
    }
    if(b.n(ASCENSION)&&!ascended&&f>=22*F){ascended=1;double add=(H/healthFactor)*b.n(ASCENSION);healthFactor+=b.n(ASCENSION);grow(add);}
    if(b.n(COVENANT)){
     if(!covenantDied&&f>=o.allyDeath){covenantDied=true;bonusAP+=.4*b.n(COVENANT);}
     if(!covenantDied&&o.allyPeriod>0&&f%o.allyPeriod==0)gain(15*b.n(COVENANT),3);
    }
    // Target dummies cast an 80-mana spell every four seconds, for Ionic's documented trigger.
    if(b.n(IONIC)&&f%(4*F)==0)aoe(0,b.w(IONIC,1.5,3)*80,false,true);
    if(b.n(BOMBPOT)&&f==8*F)stun(b.c[BOMBPOT][1]?2:1.75);
    if(b.n(DEFY)){
     debtRate+=debtChanges[f%(4*F+1)];debtChanges[f%(4*F+1)]=0;
     double due=max(0.,debtRate);double d=f>=zhonyaUntil?min(max(0.,hp-1),due):0;hp-=d;r.debtPaid+=d;if(d>0)presentationEvent("damage",d,"deferred");r.debtForgiven+=due-d;trigger();
    }
   }
   if(o.skills&&mp>=cap-EPS&&f>=locked&&f>=zhonyaUntil)cast();
   if(f&&f%hitInterval==0)incoming((f/hitInterval-1)%3);
   if(!r.alive){event("death",0);snapshot();break;}
   if(o.skills&&mp>=cap-EPS&&f>=locked&&f>=zhonyaUntil)cast();
   r.minHP=min(r.minHP,hp);snapshot();if(trace)event("frame");
  }
  const int used=f-begin+(!r.alive?1:0);executedTicks+=used-(begin==0?1:0);
  if(r.alive&&f<=limit)return used;
  finished=true;
  r.hp=max(0.,hp);r.H=H;r.shield=totalShield();r.mana=mp;r.debtLeft=max(0.,r.deferred-r.debtPaid-r.debtForgiven);
  assert(abs(r.mpInitial+r.mpGain-r.mpSpent-r.mana)<.001);
  assert(abs(r.granted-r.used-r.lost-r.shield)<.01+1e-10*max(r.granted,r.shield));
  assert(isfinite(r.H)&&isfinite(r.hp)&&isfinite(r.shield)&&isfinite(r.damage)&&isfinite(r.heal));return used;
 }
 Result run(){while(!finished)advance(limit+1);return r;}
};
void outputResult(ostream& out,const Result& r,int precision=10){
 out<<setprecision(precision)<<"{\"frame\":"<<r.frame<<",\"alive\":"<<(r.alive?"true":"false")<<",\"hp\":"<<r.hp<<",\"H\":"<<r.H<<",\"initial_hp\":"<<r.initialHP<<",\"shield\":"<<r.shield<<",\"casts\":"<<r.casts<<",\"attacks\":"<<r.attacks<<",\"spider_attacks\":"<<r.spiderAttacks<<",\"heal\":"<<r.heal<<",\"vamp\":"<<r.vamp<<",\"skill_heal\":"<<r.skillHeal<<",\"spider_heal\":"<<r.spiderHeal<<",\"damage\":"<<r.damage<<",\"shield_granted\":"<<r.granted<<",\"shield_used\":"<<r.used<<",\"shield_lost\":"<<r.lost<<",\"shield_converted\":"<<r.converted<<",\"growth\":"<<r.growth<<",\"raw_input\":"<<r.raw<<",\"avoided_raw\":"<<r.avoided<<",\"cc_avoided_raw\":"<<r.ccAvoided<<",\"deferred\":"<<r.deferred<<",\"debt_paid\":"<<r.debtPaid<<",\"debt_left\":"<<r.debtLeft<<",\"mana\":"<<r.mana<<",\"mana_initial\":"<<r.mpInitial<<",\"mana_gain\":"<<r.mpGain<<",\"mana_spent\":"<<r.mpSpent<<",\"mana_blocked\":"<<r.mpBlocked<<",\"mana_overflow\":"<<r.mpOverflow<<",\"mana_attack\":"<<r.mpAttack<<",\"mana_damage\":"<<r.mpDamage<<",\"mana_regen\":"<<r.mpRegen<<",\"mana_special\":"<<r.mpSpecial<<",\"min_hp\":"<<r.minHP<<"}";
}
