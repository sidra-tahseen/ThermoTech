import { useState } from "react";

import Header from "./components/Header";
import Pipeline from "./components/Pipeline";
import KPICards from "./components/KPICards";
import Sidebar from "./components/Sidebar";
import Map from "./components/Map";
import CriticalEvent from "./components/CriticalEvent";
import TrendChart from "./components/TrendChart";

function App() {
  const [filters, setFilters] = useState({
    categories: {
      PERSISTENT_SOURCE: true,
      NEW_ABNORMAL_EVENT: true,
      OTHER_ANOMALY: true,
    },
    timeRange: "24H",
    minFrp: 0,
  });

  return (
    <div className="app">
      <Header />

      <main className="dashboard">
        <Pipeline />

        <KPICards />

        <div className="workspace">
          <Sidebar
            filters={filters}
            setFilters={setFilters}
          />

          <section className="main-content">
            <Map filters={filters} />
            <TrendChart />
          </section>

          <CriticalEvent />
        </div>
      </main>
    </div>
  );
}

export default App;