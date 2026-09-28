#include "engine-audit.hpp"
int main(){
 Hero h;for(auto x:HEROES)if(x.kind==11&&x.star==3)h=x;
 Scenario sc{0,6,0,0,0,6};auto b=makeBuild({5,27,30});Options o;o.seconds=30;o.attackers=3;
 for(int mode=0;mode<4;mode++)for(double dps:{1000.,1400.,1800.}){
 auditMode=mode;o.dps=dps;Sim s(h,sc,b,0,o);auto r=s.run();
 cout<<"mode="<<mode<<" dps="<<dps<<" seconds="<<double(r.frame)/30<<" attacks="<<r.attacks<<" casts="<<r.casts<<" heal="<<r.skillHeal<<" hp="<<r.hp<<"\n";
 }
 auditMode=0;b=makeBuild({-1,-1,-1});sc=Scenario{0,0,0,0,0,0};o.dps=0;o.seconds=3;o.targetRes=0;
 for(int star=1;star<=3;star++)for(double ap:{1.,1.18,2.}){
 for(auto x:HEROES)if(x.kind==11&&x.star==star)h=x;
 b.ap=ap-1;Sim s(h,sc,b,0,o);s.hp=1;s.mp=h.cap;s.r.mpInitial=h.cap;auto r=s.run();
 cout<<"isolated star="<<star<<" AP="<<ap*100<<" healing="<<r.skillHeal<<" expected="<<h.v[0]*ap<<" damage="<<r.damage<<" expected="<<3*h.v[1]*ap<<" attacks="<<r.attacks<<"\n";
 }
}
