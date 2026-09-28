#include "../../tank-lab/src/engine-web.hpp"
#include "before.hpp"
#include <chrono>
int main(int argc,char**argv){
 bool benchmark=argc>1;long long cases=0,ticks=0;double secondsNew=0,secondsOld=0;
 vector<vector<int>> gears{{27,9,16},{27,33,33},{4,48,45},{50,61,65},{29,0,30},{22,22,23},{24,24,27},{16,16,25},{5,17,27},{17,17,17}};
 if(!benchmark)for(int i=0;i<int(ITEMS.size());i++)if(ITEMS[i].kind>=0&&ITEMS[i].cat!=3)gears.push_back({i,27,33});
 for(int sn=0;sn<int(SCENARIOS.size());sn++)for(int gi=0;gi<int(gears.size());gi++)for(int aug:{0,4}){
  if(!legal(gears[gi])||(aug==4&&find(gears[gi].begin(),gears[gi].end(),27)==gears[gi].end()))continue;
  auto sc=SCENARIOS[sn];auto h=HEROES[sc.hero];auto b=makeBuild(gears[gi]);auto ob=before::makeBuild(gears[gi]);Options o;o.seconds=30;o.dps=(sn%7==0)?0:300+(sn%11)*150;o.wound=(sn%2)?0:.33;o.attackers=sn%9;o.control=sn%3==0;o.resistanceMode=sn%4;o.soloPlate=aug==4;o.allyDeath=150;o.itemVamp=true;
  before::Options oldO;static_assert(sizeof(o)==sizeof(oldO));memcpy(&oldO,&o,sizeof(o));Sim n(h,sc,b,0,o);before::Sim old(h,sc,ob,0,oldO);n.capture=old.capture=!benchmark&&gi<2;
  auto start=chrono::steady_clock::now();auto expected=old.run();secondsOld+=chrono::duration<double>(chrono::steady_clock::now()-start).count();
  start=chrono::steady_clock::now();if(!benchmark&&gi<2){int budget=1;while(!n.finished){n.advance(budget);budget=(budget*7)%131+1;}}else n.run();secondsNew+=chrono::duration<double>(chrono::steady_clock::now()-start).count();
  ostringstream a,e;outputResult(a,n.r,17);before::outputResult(e,expected,17);if(a.str()!=e.str()){cerr<<"Mismatch scenario "<<sn<<" gear "<<gi<<" augment "<<aug<<"\n"<<a.str()<<"\n"<<e.str()<<endl;return 1;}
  assert(n.frames==old.frames&&n.attributes==old.attributes&&n.events.size()==old.events.size()&&n.presentationEvents.size()==old.presentationEvents.size());
  for(size_t i=0;i<n.events.size();i++)assert(n.events[i].frame==old.events[i].frame&&n.events[i].kind==old.events[i].kind&&n.events[i].value==old.events[i].value);
  for(size_t i=0;i<n.presentationEvents.size();i++){auto&a=n.presentationEvents[i];auto&e=old.presentationEvents[i];assert(a.frame==e.frame&&a.kind==e.kind&&a.amount==e.amount&&a.source==e.source);}
  assert(n.executedTicks==old.executedTicks);cases++;ticks+=n.executedTicks;
 }

 if(!benchmark)for(int mask=0;mask<8;mask++)for(auto ids:vector<vector<int>>{{24,24,27},{65,23,27},{22,22,23}}){
  auto h=HEROES[0];h.kind=24;h.v[0]=500;h.v[1]=100;h.v[2]=1;auto sc=SCENARIOS[0];auto b=makeBuild(ids);auto ob=before::makeBuild(ids);Options o;o.seconds=30;o.dps=500;o.malphiteManaDuringShield=mask&1;o.malphiteAttacksDuringShield=mask&2;o.malphiteBurstOnExpiry=mask&4;before::Options oo;memcpy(&oo,&o,sizeof(o));Sim n(h,sc,b,0,o);before::Sim old(h,sc,ob,0,oo);auto nr=n.run();auto rr=old.run();ostringstream a,e;outputResult(a,nr,17);before::outputResult(e,rr,17);assert(a.str()==e.str()&&n.frames==old.frames&&n.attributes==old.attributes);cases++;ticks+=n.executedTicks;
 }
 cout<<"{\"passed\":true,\"cases\":"<<cases<<",\"ticks\":"<<ticks<<",\"baselineSeconds\":"<<secondsOld<<",\"refactoredSeconds\":"<<secondsNew<<",\"ratio\":"<<secondsNew/secondsOld<<",\"exactResultsFramesAndEvents\":true}\n";
}
