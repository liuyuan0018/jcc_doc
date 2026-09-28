"""Apply only web-facing parameter and trace hooks to the validated C++ core."""
from pathlib import Path
from replay_telemetry import instrument
P=Path(__file__).resolve().parent
s=(P/'engine-original.cpp').read_text()
s=s[:s.index('struct Best{')]
# DataJ mobile S18 snapshot, rechecked 2026-09-21. Keep the historical core intact.
def correct(old, new):
    global s
    if s.count(old) != 1:
        raise RuntimeError(f'Skill correction must match exactly once: {old}')
    s = s.replace(old, new, 1)

correct('1.5*(A+extraA+v[0]*ap*max(0.,1.-double(f)/(12*F)))',
        'v[1]/100*defenses(true)')
correct('m+=.07*H+h.v[1]*lastAmp;kobukoSmash=false;',
        'm+=.1*H+h.v[1]*lastAmp;kobukoSmash=false;')
correct('while(treeBlocked>=650){treeBlocked-=650;',
        'const double blockThreshold=h.star==3?300:650;while(treeBlocked>=blockThreshold){treeBlocked-=blockThreshold;')
# Archival callers can retain round-trip double precision; legacy exports keep 10.
correct('void outputResult(ostream& out,const Result& r){\n out<<setprecision(10)',
        'void outputResult(ostream& out,const Result& r,int precision=10){\n out<<setprecision(precision)')
# Potions are outside the user-approved equipment pool, including manual replay.
s=s.replace('bool legal(array<int,3> ids){', 'bool legal(array<int,3> ids){for(int id:ids)if(id>=0&&ITEMS[id].cat==3)return false;')
# User client test: Vi casts without interrupting basic attacks; mana lock is unchanged.
s=s.replace('paused=f+o.pause;', 'if(h.kind!=12&&h.kind!=11)paused=f+o.pause;')
# User confirmed: Hecarim attacks during the three-second effect; mana stays locked.
correct('case 11:hot(v[0]*ap,3*F);resEnd=f+3*F;locked=paused=f+3*F;',
        'case 11:hot(v[0]*ap,3*F);resEnd=f+3*F;locked=f+3*F;')
# User client test: multiple normal Bloodthirsters share one shield. Radiant interactions remain unverified.
s=s.replace('if(!blood&&b.n(BLOOD)&&hp<=.5*H){blood=true;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==BLOOD)shield((ITEMS[b.ids[j]].rad?.6:.3)*H,5*F,6+j);}', 'if(!blood&&b.n(BLOOD)&&hp<=.5*H){blood=true;bool normalGranted=false;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==BLOOD){if(!ITEMS[b.ids[j]].rad){if(normalGranted)continue;normalGranted=true;}shield((ITEMS[b.ids[j]].rad?.6:.3)*H,5*F,6+j);}}')
# User-confirmed double normal Vow: one low-health shield. Startup mana remains additive;
# the separate low-health mana gain is unchanged because its stacking rule is unverified.
correct('if(!vow&&b.n(VOW)&&hp<=.4*H){vow=true;gain(b.w(VOW,15,30),3,true);for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==VOW)shield((ITEMS[b.ids[j]].rad?.5:.2)*H,limit,3+j);}',
        'if(!vow&&b.n(VOW)&&hp<=.4*H){vow=true;gain(b.w(VOW,15,30),3,true);bool normalGranted=false;for(int j=0;j<3;j++)if(b.ids[j]>=0&&ITEMS[b.ids[j]].kind==VOW){if(!ITEMS[b.ids[j]].rad){if(normalGranted)continue;normalGranted=true;}shield((ITEMS[b.ids[j]].rad?.5:.2)*H,limit,3+j);}}')
# Artifacts are limited to one copy per unit, independent of catalog flags.
s=s.replace('&&ITEMS[ids[j]].unique', '&&(ITEMS[ids[j]].unique||ITEMS[ids[j]].cat==2)')
s=s.replace('double dps=1400,','double physicalShare=.5;\n double dps=1400,')
s=s.replace('int allyPeriod=120,','int attackers=1;bool soloPlate=false;\n int allyPeriod=120,')
s=s.replace('healthFactor=1+b.hpp+brawl;', 'healthFactor=1+b.hpp+brawl+(o.soloPlate&&b.c[GARGOYLE][0]?.17:0);')
s=s.replace('b.w(GARGOYLE,30,60)', 'b.w(GARGOYLE,10,20)*o.attackers')
s=s.replace('double physicalShare=.5;', 'double physicalShare=.5,wound=0;int woundStart=0,woundEnd=5400;')
s=s.replace('double heal(double v,int src=0){v=max(0.,v);', 'double heal(double v,int src=0){v=max(0.,v);if(!b.n(MITTENS)&&f>=o.woundStart&&f<o.woundEnd)v*=1-o.wound;')
s=s.replace('int woundStart=0,woundEnd=5400;', 'int woundStart=0,woundEnd=5400,resistanceMode=0;')
s=s.replace('  return v;\n }\n void trigger()', '  return v>0&&((armor?1:2)&o.resistanceMode)?v*.7:v;\n }\n void trigger()')
# Leona uses defenses(true), including the resistance reduction applied above.
s=s.replace('(A+M+extraA+extraM+2*mogul+120)*h.v[1]/100', '(o.resistanceMode?((A+extraA+mogul+60)*(o.resistanceMode&1?.7:1)+(M+extraM+mogul+60)*(o.resistanceMode&2?.7:1)):(A+M+extraA+extraM+2*mogul+120))*h.v[1]/100')
s=s.replace(' ostream* trace=nullptr;', ''' bool capture=true;
 struct WebEvent {int frame;string kind;double value;};
 vector<array<double,19>> frames;
 vector<WebEvent> events;
 void snapshot(){if(!capture)return;frames.push_back({double(f),max(0.,hp),H,totalShield(),mp,cap,double(max(0,locked-f)),double(max(0,paused-f)),double(r.casts),double(r.attacks),r.heal,r.used,r.damage,defenses(true),defenses(false),double(transformed),double(f<zhonyaUntil||f<edgeUntil),double(r.alive),r.mpBlocked});}
 ostream* trace=nullptr;''')
s=s.replace('void event(const string& k,double v=0){','void event(const string& k,double v=0){if(capture)events.push_back({f,k,v});')
s=s.replace('raw*.5*(pow(.95,b.c[BRAMBLE][0])*pow(.90,b.c[BRAMBLE][1])*res(defenses(true))+res(defenses(false)))*mul','(o.physicalShare==.5?raw*.5*(pow(.95,b.c[BRAMBLE][0])*pow(.90,b.c[BRAMBLE][1])*res(defenses(true))+res(defenses(false))):raw*(o.physicalShare*pow(.95,b.c[BRAMBLE][0])*pow(.90,b.c[BRAMBLE][1])*res(defenses(true))+(1-o.physicalShare)*res(defenses(false))))*mul')
s=s.replace('if(!r.alive)break;', 'if(!r.alive){event("death",0);snapshot();break;}')
s=s.replace('r.minHP=min(r.minHP,hp);if(trace)event("frame");','r.minHP=min(r.minHP,hp);snapshot();if(trace)event("frame");')
# A simulation owns its cursor; budget boundaries must not repeat startup or finalize early.
s=s.replace(' Result run(){', ' bool started=false,finished=false;long long executedTicks=0;\n int advance(int budget){\n  if(budget<=0||finished)return 0;\n  if(!started){started=true;')
s=s.replace('  for(f=0;f<=limit;f++){', '  }\n  const int begin=f,end=min(limit+1,f+budget);\n  for(;f<end;f++){')
s=s.replace('  r.hp=max(0.,hp);r.H=H;', '  const int used=f-begin+(!r.alive?1:0);executedTicks+=used-(begin==0?1:0);\n  if(r.alive&&f<=limit)return used;\n  finished=true;\n  r.hp=max(0.,hp);r.H=H;')
s=s.replace('isfinite(r.heal));return r;', 'isfinite(r.heal));return used;')
s=s.replace('\n};\nvoid outputResult', '\n Result run(){while(!finished)advance(limit+1);return r;}\n};\nvoid outputResult')
(P/'engine-web.hpp').write_text(instrument(s))
