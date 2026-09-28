#define main equipment_engine_main
#include "engine.cpp"
#undef main
int main(int argc,char** argv){int sn=stoi(argv[1]),category=stoi(argv[2]);auto sc=SCENARIOS[sn];Options o;long long tested=0,alive=0;
 for(int i=0;i<int(ITEMS.size());i++)for(int j=i;j<int(ITEMS.size());j++)for(int k=j;k<int(ITEMS.size());k++)if(legal({i,j,k})){
  auto b=makeBuild({i,j,k});if(b.cat!=category)continue;auto r=Sim(HEROES[sc.hero],sc,b,0,o).run();tested++;
  if(r.alive){alive++;cout<<"{\"items\":["<<i<<','<<j<<','<<k<<"],\"result\":";outputResult(cout,r);cout<<"}\n";}
 }
 cerr<<"tested "<<tested<<" survived "<<alive<<endl;
}
