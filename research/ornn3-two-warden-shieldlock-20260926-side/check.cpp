#include "web.cpp"
int main(){string id;long long lockedTicks=0;int count=0;while(cin>>id){double p[35];for(double&v:p)cin>>v;Hero h;Scenario sc;Build b;int aug;Options o;auto e=configure(p,35,h,sc,b,aug,o);assert(e.empty());
// Skill shields block all mana sources, even after the one-second timer ends.
Sim test(h,sc,b,aug,o);test.capture=false;test.mp=0;test.locked=0;test.f=60;test.shield(100,120,0);for(int src=0;src<4;src++)test.gain(10,src,true);assert(test.mp==0);
test.ns=0;test.gain(10,0);assert(test.mp>0);test.mp=0;test.shield(100,120,13);test.gain(10,1);assert(test.mp>0);
// Actual battle: inspect every frame, including expiry and consumed shields.
for(int d:{100,400,650}){o.dps=d;Sim s(h,sc,b,aug,o);s.capture=false;while(!s.finished){s.advance(1);if(s.skillShield()){lockedTicks++;assert(s.mp==0);}}}count++;}
cout<<"{\"passed\":true,\"builds\":"<<count<<",\"lockedFrames\":"<<lockedTicks<<",\"checks\":\"skill shield blocks mana; removal unlocks; equipment shields do not lock; actual frame-level mana remains zero\"}"<<endl;}
