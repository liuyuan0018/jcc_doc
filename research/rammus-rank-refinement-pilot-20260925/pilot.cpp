#include "web.cpp"
#include <chrono>
int main(){
 string id;int lo,hi;long long total=0;auto start=chrono::steady_clock::now();
 while(cin>>id>>lo>>hi){
  double p[35];for(double& v:p)cin>>v;Hero h;Scenario sc;Build b;int aug;Options o;
  auto err=configure(p,35,h,sc,b,aug,o);if(!err.empty()){cerr<<err;return 1;}
  auto run=[&](int d){o.dps=d;Sim sim(h,sc,b,aug,o);sim.capture=false;total++;return sim.run();};
  vector<Result> grid;vector<int> reversals;bool failed=false;int highest=-1,firstFail=-1;
  auto gstart=chrono::steady_clock::now();
  for(int d=lo;d<=hi;d++){auto r=run(d);grid.push_back(r);if(r.alive){highest=d;if(failed)reversals.push_back(d);}else{failed=true;if(firstFail<0)firstFail=d;}}
  double gridSecs=chrono::duration<double>(chrono::steady_clock::now()-gstart).count();
  int l=lo,u=hi,calls=0;vector<pair<int,bool>> probes;auto bstart=chrono::steady_clock::now();
  while(u-l>1){int mid=(l+u)/2;auto r=run(mid);calls++;probes.push_back({mid,r.alive});if(r.alive)l=mid;else u=mid;}
  double binarySecs=chrono::duration<double>(chrono::steady_clock::now()-bstart).count();
  cout<<setprecision(17)<<"{\"id\":\""<<id<<"\",\"lo\":"<<lo<<",\"hi\":"<<hi<<",\"highestPass\":"<<highest<<",\"firstFail\":"<<firstFail<<",\"binaryPass\":"<<l<<",\"binaryCalls\":"<<calls<<",\"gridSeconds\":"<<gridSecs<<",\"binarySeconds\":"<<binarySecs<<",\"reversals\":[";
  for(size_t i=0;i<reversals.size();i++){if(i)cout<<',';cout<<reversals[i];}cout<<"],\"stages\":[";
  for(size_t i=0;i<grid.size();i++){if(i)cout<<',';cout<<"{\"dps\":"<<lo+i<<",\"result\":";outputResult(cout,grid[i],17);cout<<'}';}
  cout<<"],\"binaryProbes\":[";for(size_t i=0;i<probes.size();i++){if(i)cout<<',';cout<<'['<<probes[i].first<<','<<(probes[i].second?"true":"false")<<']';}cout<<"]}"<<endl;
 }
 cerr<<"runs="<<total<<" seconds="<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<endl;
}
