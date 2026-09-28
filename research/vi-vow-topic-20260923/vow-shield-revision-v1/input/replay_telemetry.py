"""Add presentation facts at settlement sites without changing combat state."""


def instrument(source: str) -> str:
    def replace(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise ValueError(f"Telemetry hook must match exactly once: {old[:90]}")
        source = source.replace(old, new, 1)

    replace(' vector<WebEvent> events;', ''' vector<WebEvent> events;
 struct PresentationEvent {int frame;string kind;double amount;string source;};
 vector<array<double,4>> attributes;
 vector<PresentationEvent> presentationEvents;
 void presentationEvent(const char* kind,double amount,const char* source){if(capture)presentationEvents.push_back({f,kind,amount,source});}''')
    replace('double(r.alive),r.mpBlocked});}', 'double(r.alive),r.mpBlocked});attributes.push_back({double(f),defenses(true),defenses(false),100*abilityPowerMultiplier()});}')

    # Share the existing expression. Reading AP at the end of a frame must not
    # update the combat caches used by the next action (lastAmp, sv, etc.).
    begin = source.index('  lastAmp=')
    end = source.index(';', begin)
    expression = source[begin + len('  lastAmp='):end]
    replace(' void stats(){', ''' double abilityPowerMultiplier()const{
  double justice=b.w(JUSTICE,.18,.35)*(hp>H*.5?2:1);
  double blue=1+b.w(BLUE,.10,.20);
  return ''' + expression + ''';
 }
 void stats(){''')
    replace('  lastAmp=' + expression + ';', '  lastAmp=abilityPowerMultiplier();')
    replace('if(src==3)r.spiderHeal+=actual;return actual;', 'if(src==3)r.spiderHeal+=actual;if(actual>0)presentationEvent("heal",actual,src==1?"lifesteal":src==2?"skill":src==3?"spider":"other");return actual;')
    replace('void grow(double v){H+=v;hp+=v;r.growth+=v;}', 'void grow(double v){H+=v;hp+=v;r.growth+=v;if(v!=0)presentationEvent("healthGrowth",v,"maxHealth");}')

    replace(' void shield(double v,int dur,int tag,double decay=0){', ' void shield(double v,int dur,int tag,double decay=0){\n  double before=capture?totalShield():0;')
    replace('r.lost+=shields[i].value;removeShield(i);break;', 'r.lost+=shields[i].value;presentationEvent("shieldReplace",shields[i].value,"sameTag");removeShield(i);break;')
    replace('shields[ns++]={v,decay,f+dur,tag};r.granted+=v;}\n }', 'shields[ns++]={v,decay,f+dur,tag};r.granted+=v;presentationEvent("shieldGain",v,"grant");}\n  if(capture&&before>EPS&&totalShield()<=EPS)presentationEvent("shieldBreak",0,"replacement");\n }')

    replace('  // Expiring shields absorb first.', '  double usedBefore=capture?r.used:0,shieldBefore=capture?totalShield():0;\n  // Expiring shields absorb first.')
    replace('  if(b.n(DEFY)&&dmg>0)', '''  if(capture&&r.used>usedBefore)presentationEvent("shieldAbsorb",r.used-usedBefore,"incoming");
  if(capture&&shieldBefore>EPS&&totalShield()<=EPS)presentationEvent("shieldBreak",0,"damage");
  if(b.n(DEFY)&&dmg>0)''')
    replace('  hp-=dmg;', '  if(dmg>0)presentationEvent("damage",min(max(0.,hp),dmg),"incoming");\n  hp-=dmg;')
    replace('hp-=d;r.debtPaid+=d;', 'hp-=d;r.debtPaid+=d;if(d>0)presentationEvent("damage",d,"deferred");')

    replace('   for(int j=0;j<ns;){if(shields[j].end<=f)', '   double beforeExpiry=capture?totalShield():0;\n   for(int j=0;j<ns;){if(shields[j].end<=f)')
    replace('r.lost+=shields[j].value;removeShield(j);', 'r.lost+=shields[j].value;presentationEvent("shieldExpire",shields[j].value,"duration");removeShield(j);')
    replace('shields[j].value-=take;r.lost+=take;', 'shields[j].value-=take;r.lost+=take;if(take>0)presentationEvent("shieldDecay",take,"decay");')
    replace('   if(f>=flailExpiry)flailStacks=0;stats();', '   if(capture&&beforeExpiry>EPS&&totalShield()<=EPS)presentationEvent("shieldBreak",0,"lifetime");\n   if(f>=flailExpiry)flailStacks=0;stats();')
    return source
