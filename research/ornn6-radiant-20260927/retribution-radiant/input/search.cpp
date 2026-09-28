// Exhaustive episode-one archive: every legal build and every attempted stage.
// No winner pruning. One atomic file pair per scenario permits safe inspection.
#include "web.cpp"
#include <zlib.h>
#include <filesystem>
#include <chrono>
namespace fs=std::filesystem;
struct Gzip {
 gzFile file=nullptr;
 explicit Gzip(const string& path){file=gzopen(path.c_str(),"wb1");if(!file)throw runtime_error("open "+path);gzbuffer(file,1<<20);}
 void write(const string& value){if(gzwrite(file,value.data(),unsigned(value.size()))!=int(value.size()))throw runtime_error("gzip write failed");}
 void close(){auto f=file;file=nullptr;if(gzclose(f)!=Z_OK)throw runtime_error("gzip close failed");}
 ~Gzip(){if(file)gzclose(file);}
};
int main(int argc,char** argv){
 try {
  if(argc!=3&&argc!=4)throw runtime_error("Usage: archive-episode-one OUTPUT_DIRECTORY THREADS [PILOT_SCENARIO]");
  fs::path out=argv[1];fs::create_directories(out);int threads=stoi(argv[2]);if(threads<1||threads>16)throw runtime_error("invalid threads");
  vector<Build> builds;
  for(int i=0;i<int(ITEMS.size());i++)if(ITEMS[i].cat==0&&ITEMS[i].kind>=0)
   for(int j=i;j<int(ITEMS.size());j++)if(ITEMS[j].cat==0&&ITEMS[j].kind>=0)
    for(int k=j;k<int(ITEMS.size());k++)if(ITEMS[k].cat==1&&ITEMS[k].kind>=0&&legal({i,j,k}))builds.push_back(makeBuild({i,j,k}));
  vector<int> cases;
  cases={8};
  if(argc==4){int sn=stoi(argv[3]);if(find(cases.begin(),cases.end(),sn)==cases.end())throw runtime_error("invalid pilot scenario");cases={sn};}
  auto eligible=[](const Build& b,int aug){return b.n(JUSTICE)>0;};
  long long perCase=0;for(const auto& b:builds)for(int aug:{0})perCase+=eligible(b,aug);
  atomic<int> next{0};atomic<long long> configs{0},runs{0};atomic<bool> failed{false};mutex output;vector<thread> workers;
  cout<<"{\"type\":\"start\",\"scenarios\":"<<cases.size()<<",\"equipmentTriples\":"<<builds.size()<<",\"expectedConfigurations\":"<<perCase*cases.size()<<",\"threads\":"<<threads<<"}"<<endl;
  auto begin=chrono::steady_clock::now();
  for(int worker=0;worker<threads;worker++)workers.emplace_back([&]{try{
   while(!failed){int index=next++;if(index>=int(cases.size()))break;int sn=cases[index];const auto& sc=SCENARIOS[sn];const auto& h=HEROES[sc.hero];
    string stem="scenario-"+to_string(sn);fs::path raw=out/(stem+".runs.jsonl.gz"),summary=out/(stem+".summary.jsonl.gz");
    if(fs::exists(raw)||fs::exists(summary))throw runtime_error("Refusing to overwrite "+stem);
    Gzip archive(raw.string()+".partial"),summaries(summary.string()+".partial");long long caseConfigs=0,caseRuns=0;int ceilings=0;
    for(int bi=0;bi<int(builds.size());bi++)for(int aug:{0})if(eligible(builds[bi],aug)){
     if(failed)throw runtime_error("another worker failed");const auto& b=builds[bi];
     Options o;o.seconds=30;o.dps=300;o.attackers=5;o.soloPlate=aug==4;o.wound=.33;o.woundStart=0;o.woundEnd=5401;o.resistanceMode=3;
     int passed=-1,firstFailure=-1,count=0;Result best{},last{};string key="s"+to_string(sn)+"-b"+to_string(bi)+"-a"+to_string(aug);
     ostringstream record;record<<"{\"id\":\""<<key<<"\",\"scenario\":"<<sn<<",\"heroId\":"<<h.id<<",\"items\":["<<itemIdsJson(b.ids)<<"],\"augment\":"<<aug<<",\"stages\":[";
     for(int dps=300;dps<=20000;dps+=50){
      o.dps=dps;Sim sim(h,sc,b,aug&3,o);sim.capture=false;last=sim.run();if(count++)record<<',';
      record<<"{\"dps\":"<<dps<<",\"result\":";outputResult(record,last,17);record<<'}';caseRuns++;
      if(!last.alive){firstFailure=dps;break;}passed=dps;best=last;
     }
     bool ceiling=firstFailure<0;ceilings+=ceiling;
     record<<"],\"passedDps\":"<<passed<<",\"failedDps\":"<<firstFailure<<",\"ceilingReached\":"<<(ceiling?"true":"false")<<"}\n";archive.write(record.str());
     ostringstream row;row<<setprecision(17)<<"{\"id\":\""<<key<<"\",\"scenario\":"<<sn<<",\"heroId\":"<<h.id<<",\"items\":["<<itemIdsJson(b.ids)<<"],\"augment\":"<<aug<<",\"passedDps\":"<<passed<<",\"failedDps\":"<<firstFailure<<",\"stageCount\":"<<count<<",\"failedFrame\":"<<(ceiling?-1:last.frame)<<",\"remainingHpShield\":"<<(passed<0?0:best.hp+best.shield)<<",\"ceilingReached\":"<<(ceiling?"true":"false")<<"}\n";summaries.write(row.str());caseConfigs++;
    }
    if(caseConfigs!=perCase)throw runtime_error("incomplete scenario");archive.close();summaries.close();fs::rename(raw.string()+".partial",raw);fs::rename(summary.string()+".partial",summary);
    configs+=caseConfigs;runs+=caseRuns;lock_guard<mutex> guard(output);
    cout<<"{\"type\":\"scenarioComplete\",\"scenario\":"<<sn<<",\"configurations\":"<<caseConfigs<<",\"stageRuns\":"<<caseRuns<<",\"ceilings\":"<<ceilings<<",\"totalConfigurations\":"<<configs<<",\"totalStageRuns\":"<<runs<<"}"<<endl;
   }
  }catch(const exception& e){failed=true;lock_guard<mutex> guard(output);cerr<<"archive failed: "<<e.what()<<endl;}});
  for(auto& worker:workers)worker.join();if(failed)return 1;
  if(configs!=perCase*cases.size())throw runtime_error("incomplete archive");
  cout<<"{\"type\":\"complete\",\"configurations\":"<<configs<<",\"stageRuns\":"<<runs<<",\"elapsedSeconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-begin).count()<<"}"<<endl;
 }catch(const exception& e){cerr<<e.what()<<endl;return 1;}
}
