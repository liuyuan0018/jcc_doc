#include "web.cpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <zlib.h>
struct Job {string id;array<double,35> p;};
int main(int argc,char**argv){try{
 if(argc!=5)throw runtime_error("scan OUTPUT LOWER UPPER THREADS < input");
 string out=argv[1];int lower=stoi(argv[2]),upper=stoi(argv[3]),nt=stoi(argv[4]);
 if(lower<0||upper<lower||nt<1||nt>8)throw runtime_error("invalid range/thread count");
 vector<Job> jobs;Job j;while(cin>>j.id){for(auto&v:j.p)if(!(cin>>v))throw runtime_error("incomplete input");jobs.push_back(j);}
 filesystem::create_directories(out);atomic<int> next{0},done{0};atomic<bool> failed{false};mutex log;vector<thread> workers;auto start=chrono::steady_clock::now();
 for(int w=0;w<nt;w++)workers.emplace_back([&,w]{gzFile gz=nullptr;try{
  string stem=out+"/worker-"+to_string(w);if(filesystem::exists(stem+".csv.gz")||filesystem::exists(stem+".jsonl"))throw runtime_error("output exists");
  gz=gzopen((stem+".csv.gz.partial").c_str(),"wb1");if(!gz)throw runtime_error("gzip open failed");gzbuffer(gz,1<<20);ofstream summary(stem+".jsonl.partial");
  string header="id,dps,alive,frame,hp,shield\n";gzwrite(gz,header.data(),header.size());
  while(!failed){int ix=next++;if(ix>=int(jobs.size()))break;auto job=jobs[ix];Hero h;Scenario sc;Build b;int aug;Options o;auto error=configure(job.p.data(),35,h,sc,b,aug,o);if(!error.empty())throw runtime_error(error);
   int highest=-1,passes=0,reversals=0,rangeStart=-1;bool previous=false;vector<pair<int,int>> ranges;Result best{},end{};string stages;stages.reserve((upper-lower+1)*75);char line[512];
   int begin=int(job.p[6]); int limit=begin+50;
   for(int d=begin;d<=limit;d++){
    o.dps=d;Sim sim(h,sc,b,aug,o);sim.capture=false;auto r=sim.run();
    if(!isfinite(r.hp)||!isfinite(r.shield)||r.hp<0||r.shield<0)throw runtime_error("invalid result");
    if(r.alive){if(r.frame!=900)throw runtime_error("unexpected duration");highest=d;passes++;best=r;if(!previous){rangeStart=d;if(d>lower)reversals++;}}
    else if(previous)ranges.push_back({rangeStart,d-1});previous=r.alive;end=r;
    int len=snprintf(line,sizeof(line),"%s,%d,%d,%d,%.17g,%.17g\n",job.id.c_str(),d,int(r.alive),r.frame,r.hp,r.shield);if(len<0||len>=int(sizeof(line)))throw runtime_error("stage format overflow");stages.append(line,len); if(!r.alive)break;
   }
   if(previous)ranges.push_back({rangeStart,upper});
   if(gzwrite(gz,stages.data(),stages.size())!=int(stages.size()))throw runtime_error("gzip write failed");
   summary<<"{\"id\":\""<<job.id<<"\",\"highestPass\":"<<highest<<",\"passCount\":"<<passes<<",\"reversals\":"<<reversals<<",\"atCeiling\":"<<(end.alive?"true":"false")<<",\"bestResult\":";outputResult(summary,best,17);summary<<",\"passRanges\":[";
   for(size_t k=0;k<ranges.size();k++){if(k)summary<<',';summary<<'['<<ranges[k].first<<','<<ranges[k].second<<']';}summary<<"]}\n";
   int completed=++done;if(completed%500==0){lock_guard<mutex>guard(log);cout<<"completed="<<completed<<"/"<<jobs.size()<<" elapsed="<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<endl;}
  }
  if(failed)throw runtime_error("another worker failed");summary.close();int rc=gzclose(gz);gz=nullptr;if(rc!=Z_OK)throw runtime_error("gzip close failed");filesystem::rename(stem+".csv.gz.partial",stem+".csv.gz");filesystem::rename(stem+".jsonl.partial",stem+".jsonl");
 }catch(const exception&e){failed=true;lock_guard<mutex>guard(log);cerr<<e.what()<<endl;if(gz)gzclose(gz);}});
 for(auto&t:workers)t.join();if(failed||done!=int(jobs.size()))return 1;
 cout<<"complete configurations="<<done<<" stages="<<1LL*done*(upper-lower+1)<<" seconds="<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<endl;
}catch(const exception&e){cerr<<e.what()<<endl;return 1;}}
