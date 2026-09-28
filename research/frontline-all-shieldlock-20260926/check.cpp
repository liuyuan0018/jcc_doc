#include "web.cpp"
int main(){long long lockedFrames=0;int battles=0,unitCases=0;vector<int> scenarios;for(int i=0;i<int(SCENARIOS.size());i++){auto h=HEROES[SCENARIOS[i].hero];if(h.star==(h.cost<=3?3:2))scenarios.push_back(i);}
for(int sid:scenarios){auto sc=SCENARIOS[sid];auto h=HEROES[sc.hero];Options o;o.seconds=30;o.attackers=5;o.wound=.33;o.resistanceMode=3;o.control=false;
auto b=makeBuild({16,23,27});Sim t(h,sc,b,0,o);t.capture=false;t.f=60;t.locked=0;t.mp=0;
bool expected=h.kind==0||h.kind==1||h.kind==7||h.kind==8||h.kind==15||h.kind==16||h.kind==17;t.shield(100,120,0);
for(int src=0;src<4;src++)for(bool bypass:{false,true}){t.mp=0;t.gain(10,src,bypass);assert(expected?t.mp==0:t.mp>0);unitCases++;}
t.ns=0;t.mp=0;t.gain(10,0);assert(t.mp>0);
for(int tag:{1,2,3,6,13}){t.ns=0;t.mp=0;t.shield(100,120,tag);t.gain(10,1);assert(t.mp>0);unitCases++;}
if(expected){
 // A surviving skill shield blocks damage mana; breaking it enables subsequent gains.
 Sim u(h,sc,b,0,o);u.capture=false;u.f=60;u.locked=0;u.mp=0;u.o.dps=300;u.shield(100000,120,0);u.incoming(0);assert(u.mp==0&&u.skillShield());u.shields[0].value=.001;u.incoming(0);assert(!u.skillShield());u.gain(10,0);assert(u.mp>0);
 // Expiry removes the lock even if an equipment shield remains.
 Sim v(h,sc,b,0,o);v.capture=false;v.started=true;v.f=60;v.locked=0;v.mp=0;v.o.skills=false;v.o.dps=0;v.shield(100,0,0);v.shield(100,120,13);v.advance(1);assert(!v.skillShield()&&v.totalShield()>0);v.gain(10,2);assert(v.mp>0);
}
for(auto ids:vector<vector<int>>{{16,23,27},{22,22,23},{5,17,27},{24,24,27},{16,16,25},{9,23,33}})for(int d:{300,700,1300}){auto bb=makeBuild(ids);o.dps=d;Sim s(h,sc,bb,0,o);s.capture=false;while(!s.finished){s.advance(1);if(expected&&s.skillShield()){lockedFrames++;assert(s.mp==0);}}battles++;}
}
assert(lockedFrames>0);cout<<"{\"passed\":true,\"unitCases\":"<<unitCases<<",\"battles\":"<<battles<<",\"lockedFrames\":"<<lockedFrames<<",\"checks\":\"all four mana sources, direct mana, damage break, duration expiry, item and trait shields, frame-level skill shield mana\"}\n";}
