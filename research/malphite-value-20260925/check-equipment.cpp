#include "web.cpp"
int main(){
 Item extra{};extra.id=900001;extra.kind=-1;extra.cat=0;extra.unique=true;extra.hiddenInUi=true;extra.hp=175;extra.hpp=.17;extra.a=extra.m=12;
 int fourth=ITEMS.size();ITEMS.push_back(extra);
 auto baseline=makeBuild({24,27,33});auto augmented=makeBuild(vector<int>{24,27,33,fourth});
 if(augmented.ids.size()!=4||abs(augmented.hp-baseline.hp-175)>1e-9||abs(augmented.hpp-baseline.hpp-.17)>1e-9||abs(augmented.a-baseline.a-12)>1e-9||abs(augmented.m-baseline.m-12)>1e-9)return 1;
 for(int k=0;k<NK;k++)if(baseline.n(k)!=augmented.n(k))return 2;
 cout<<"{\"equipmentCount\":4,\"flatHpDelta\":"<<augmented.hp-baseline.hp<<",\"hpPercentDelta\":"<<augmented.hpp-baseline.hpp<<",\"armorDelta\":"<<augmented.a-baseline.a<<",\"magicResistDelta\":"<<augmented.m-baseline.m<<",\"ordinaryEffectsUnchanged\":true,\"serializedIds\":["<<itemIdsJson(augmented.ids)<<"]}"<<endl;
}
