#include "engine-web.hpp"
static string response;
static const char* fail(const string& message){response="{\"error\":\""+message+"\"}";return response.c_str();}
static string configure(const double* p,int n,Hero& h,Scenario& sc,Build& b,int& aug,Options& o){
 if(n<34)return string("Invalid parameter count");
 if(n>=35&&(p[34]!=floor(p[34])||p[34]<0||p[34]>3))return string("Invalid resistance mode");
 for(int i=0;i<n;i++)if(!isfinite(p[i]))return string("Parameters must be finite");
 auto whole=[&](int i){return floor(p[i])==p[i];};
 for(int i:{0,1,2,3,4,5,8,9,12,19,21,22,25,26,27,28,29,30,32,33})if(!whole(i))return string("Frame and index values must be integers");
 if(p[0]<0||p[0]>=SCENARIOS.size())return string("Unknown scenario");
 vector<int> ids{int(p[1]),int(p[2]),int(p[3])};
 for(int i=35;i<n;i++){if(!whole(i))return string("Equipment indices must be integers");ids.push_back(int(p[i]));}
 for(int id:ids)if(id<-1||id>=int(ITEMS.size()))return string("Unknown equipment");
 for(size_t i=3;i<ids.size();i++)if(ids[i]<0||ITEMS[ids[i]].kind>=0)return string("Additional slots require stat-only condition equipment");
 auto sorted=ids;sort(sorted.begin(),sorted.end());if(!legal(sorted))return string("Unique equipment cannot be repeated");
 if(p[4]<0||p[4]>3||p[5]<1||p[5]>180||p[6]<0||p[6]>100000||p[7]<0||p[7]>1000||p[8]<1||p[8]>300||p[9]<0||p[9]>300||p[10]<0||p[10]>1||p[11]<0||p[11]>10)return string("Simulation parameter outside supported range");
 if(p[12]<0||p[12]>1||p[19]<0||p[19]>2||p[20]<0||p[20]>1||p[21]<0||p[21]>1||p[22]<0||p[22]>30||p[23]<0||p[23]>.3||p[24]<0||p[24]>.1||p[25]<0||p[25]>1||p[26]<0||p[26]>1||p[27]<0||p[28]<0)return string("Invalid mechanics option");
 if(p[4]==3||(p[30]&&p[4]!=0))return string("Equipment augments are mutually exclusive");
 if(p[29]<0||p[29]>30||p[30]<0||p[30]>1)return string("Invalid targeting or Solo Plate option");
 if((p[31]!=0&&p[31]!=.33)||p[32]<0||p[33]>5401||p[33]<p[32])return string("Invalid wound parameters");
 sc=SCENARIOS[int(p[0])];h=HEROES[sc.hero];b=makeBuild(ids,int(p[19]));aug=int(p[4]);
 if(p[30]&&!b.c[GARGOYLE][0])return string("Solo Plate requires normal Gargoyle Stoneplate");
 if(aug&1&&!b.c[STEADFAST][0])return string("Heart augment requires normal Steadfast Heart");
 if(aug&2&&(!b.n(MOGUL)||sc.slots>=9))return string("Gold augment requires Moguls Mail and an extra team slot");
 if(p[19]){if(ids[0]!=-1||ids[1]<0||ids[2]<0)return string("Glove envelope requires two items");for(int j=1;j<3;j++)if(ITEMS[ids[j]].cat!=int(p[19])-1)return string("Glove item category mismatch");}
 if(p[13]!=-1){if(p[13]<1||p[13]>1000000)return string("Invalid HP");h.hp=p[13];}
 if(p[14]!=-1){if(p[14]<0||p[14]>5)return string("Invalid attack speed");h.as=p[14];}
 if(p[15]!=-1){if(p[15]<0||p[15]>10000)return string("Invalid armor");h.a=p[15];}
 if(p[16]!=-1){if(p[16]<0||p[16]>10000)return string("Invalid magic resistance");h.m=p[16];}
 if(p[18]!=-1){if(p[18]<15||p[18]>1000)return string("Invalid mana cap");h.cap=p[18];}
 if(p[17]!=-1){if(p[17]<0||p[17]>h.cap)return string("Initial mana exceeds cap");h.mp=p[17];}
 if(h.mp>h.cap)return string("Initial mana exceeds cap");
 b.ap+=p[11];o.seconds=p[5];o.dps=p[6];o.targetRes=p[7];o.lock=p[8];o.pause=p[9];o.physicalShare=p[10];o.skills=p[12];o.aoeVamp=p[20];o.itemVamp=p[21];o.edgeFrames=p[22];o.dawn=p[23];o.axe=p[24];o.control=p[25];o.gunSelf=p[26];o.allyDeath=p[27];o.allyPeriod=p[28];o.attackers=p[29];o.soloPlate=p[30];o.wound=p[31];o.woundStart=p[32];o.woundEnd=p[33];o.resistanceMode=n>=35?p[34]:0;
 return "";
}
extern "C" const char* run_web(const double* p,int n){
 Hero h;Scenario sc;Build b;int aug;Options o;
 auto error=configure(p,n,h,sc,b,aug,o);if(!error.empty())return fail(error);
 Sim sim(h,sc,b,aug,o);Result r=sim.run();ostringstream out;out<<"{\"result\":";outputResult(out,r);
 out<<",\"frames\":[";for(size_t i=0;i<sim.frames.size();i++){if(i)out<<',';out<<'[';for(int k=0;k<19;k++){if(k)out<<',';out<<setprecision(12)<<sim.frames[i][k];}out<<']';}out<<"],\"events\":[";
 for(size_t i=0;i<sim.events.size();i++){if(i)out<<',';auto e=sim.events[i];out<<'['<<e.frame<<",\""<<e.kind<<"\","<<e.value<<']';}
 out<<"],\"presentation\":{\"schemaVersion\":1,\"fps\":"<<o.fps<<",\"frameColumns\":[\"frame\",\"armor\",\"magicResist\",\"abilityPower\"],\"frames\":[";
 for(size_t i=0;i<sim.attributes.size();i++){if(i)out<<',';out<<'[';for(int k=0;k<4;k++){if(k)out<<',';out<<setprecision(12)<<sim.attributes[i][k];}out<<']';}
 out<<"],\"eventColumns\":[\"frame\",\"kind\",\"amount\",\"source\"],\"events\":[";
 for(size_t i=0;i<sim.presentationEvents.size();i++){if(i)out<<',';const auto& e=sim.presentationEvents[i];out<<'['<<e.frame<<",\""<<e.kind<<"\","<<e.amount<<",\""<<e.source<<"\"]";}
 out<<"]}}";response=out.str();return response.c_str();
}
#ifdef NATIVE_TEST
int main(int argc,char** argv){vector<double> p;for(int i=1;i<argc;i++)p.push_back(stod(argv[i]));cout<<run_web(p.data(),p.size())<<'\n';}
#endif
