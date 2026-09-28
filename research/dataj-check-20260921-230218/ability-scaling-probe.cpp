#include "../../tank-lab/src/engine-web.hpp"

// Isolate skill arithmetic from combat timing, items, mitigation and overhealing.
// Expected values are checked separately against the captured DataJ descriptions.
int main() {
  cout << setprecision(12) << "[";
  bool first = true;
  for (int i = 0; i < int(HEROES.size()); ++i) {
    auto h = HEROES[i];
    const bool selected = h.kind == 0 || h.kind == 1 || h.kind == 2 ||
        h.kind == 3 || h.kind == 5 || h.kind == 7 || h.kind == 8 ||
        h.kind == 9 || h.kind == 12 || h.kind == 16;
    if (!selected || (h.star != 3 && !(h.kind == 2 && h.star == 2))) continue;
    h.as = 0; // No incidental attacks during the three-second HoT probe.
    h.ad = 0; // Separate skill-added damage from ordinary attack damage.
    Scenario sc{i, 0, 0, 0, 0, 0};
    for (double ap : {100., 118., 150., 200.}) {
      auto build = makeBuild({-1, -1, -1});
      build.ap = ap / 100. - 1.;
      Options options;
      options.seconds = 3;
      options.dps = options.targetRes = options.wound = 0;
      Sim sim(h, sc, build, 0, options);
      sim.capture = false;
      sim.hp = 1; // Leave enough missing health to observe the full heal.
      sim.cast();
      const double castHeal = sim.r.skillHeal;
      const double castDamage = sim.r.damage;
      const double castShield = sim.r.granted;
      const double growth = sim.r.growth;
      double attackHeal = 0, attackDamage = 0, hotHeal = 0;
      if (h.kind == 3 || h.kind == 8 || h.kind == 9 || h.kind == 12) {
        const double beforeHeal = sim.r.heal, beforeDamage = sim.r.damage;
        sim.attack();
        attackHeal = sim.r.heal - beforeHeal;
        attackDamage = sim.r.damage - beforeDamage;
      }
      if (h.kind == 5) {
        sim.run();
        hotHeal = sim.r.skillHeal;
      }
      if (!first) cout << ',';
      first = false;
      cout << "{\"heroId\":" << h.id << ",\"kind\":" << h.kind
           << ",\"star\":" << h.star << ",\"ap\":" << ap
           << ",\"maxHp\":" << sim.H << ",\"castHeal\":" << castHeal
           << ",\"castShield\":" << castShield << ",\"castDamage\":" << castDamage
           << ",\"growth\":" << growth << ",\"attackHeal\":" << attackHeal
           << ",\"attackDamage\":" << attackDamage << ",\"hotHeal\":" << hotHeal << '}';
    }
  }
  cout << "]\n";
}
