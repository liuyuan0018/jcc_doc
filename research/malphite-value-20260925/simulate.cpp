#include "engine-web.hpp"
#include <chrono>
// All facts and hypotheses are frozen in model-assumptions.json by the caller.
int main(int argc,char**argv){
 bool telemetry=argc>1&&string(argv[1])=="replay";
 Hero hero{24504,24,2,4,0,2340,70,70,.55,105,30,80,{850,60,.45,0,0,0,0,0}};
 Scenario scenario{};
 int extraIndex=ITEMS.size();Item extra{};extra.id=900001;extra.kind=-1;extra.unique=true;extra.hiddenInUi=true;ITEMS.push_back(extra);
 string id;int i,j,k,aug,variant,requestedDps;double flatHp,hpp,armor;
 while(cin>>id>>i>>j>>k>>aug>>flatHp>>hpp>>armor>>variant>>requestedDps){
  ITEMS[extraIndex].hp=flatHp;ITEMS[extraIndex].hpp=hpp;ITEMS[extraIndex].a=ITEMS[extraIndex].m=armor;
  auto build=makeBuild(vector<int>{i,j,k,extraIndex});
  Options o;o.seconds=30;o.attackers=5;o.wound=.33;o.woundEnd=5401;o.resistanceMode=3;o.soloPlate=aug==4;
  o.malphiteManaDuringShield=variant&1;o.malphiteAttacksDuringShield=variant&2;o.malphiteBurstOnExpiry=!(variant&4);
  auto h=hero;h.a+=10*o.attackers;h.m+=10*o.attackers; // 魔岩巨兽, separately from the sacrifice item.
  int passed=-1,failed=-1,score=-1,fineFail=-1;
  cout<<"{\"id\":\""<<id<<"\",\"variant\":"<<variant;
  if(telemetry){
   o.dps=requestedDps;Sim sim(h,scenario,build,0,o);auto r=sim.run();cout<<",\"result\":";outputResult(cout,r,17);cout<<",\"frames\":[";
   for(size_t n=0;n<sim.frames.size();n++){if(n)cout<<',';cout<<'[';for(int c=0;c<19;c++){if(c)cout<<',';cout<<setprecision(12)<<sim.frames[n][c];}cout<<']';}
   cout<<"],\"attributes\":[";for(size_t n=0;n<sim.attributes.size();n++){if(n)cout<<',';cout<<'[';for(int c=0;c<4;c++){if(c)cout<<',';cout<<sim.attributes[n][c];}cout<<']';}
   cout<<"],\"events\":[";for(size_t n=0;n<sim.presentationEvents.size();n++){if(n)cout<<',';auto&e=sim.presentationEvents[n];cout<<'['<<e.frame<<",\""<<e.kind<<"\","<<e.amount<<",\""<<e.source<<"\"]";}cout<<"]}"<<endl;continue;
  }
  cout<<",\"stages\":[";bool first=true;
  for(int d=300;d<=20000;d+=50){o.dps=d;Sim sim(h,scenario,build,0,o);sim.capture=false;auto r=sim.run();if(!first)cout<<',';first=false;cout<<"["<<d<<','<<(r.alive?1:0)<<','<<r.frame<<']';if(!r.alive){failed=d;break;}passed=d;}
  cout<<"],\"refinement\":[";first=true;score=passed;
  if(failed>=0)for(int d=max(300,passed+1);d<=failed;d++){o.dps=d;Sim sim(h,scenario,build,0,o);sim.capture=false;auto r=sim.run();if(!first)cout<<',';first=false;cout<<'['<<d<<','<<(r.alive?1:0)<<','<<r.frame<<']';if(!r.alive){fineFail=d;break;}score=d;}
  cout<<"],\"passedDps\":"<<passed<<",\"failedDps\":"<<failed<<",\"score\":"<<score<<",\"refinedFail\":"<<fineFail<<"}"<<endl;
 }
}
