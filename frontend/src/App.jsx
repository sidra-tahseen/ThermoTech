import Header from "./components/Header";
import Pipeline from "./components/Pipeline";
import KPICards from "./components/KPICards";
import Sidebar from "./components/Sidebar";
import Map from "./components/Map";
import CriticalEvent from "./components/CriticalEvent";
import TrendChart from "./components/TrendChart";

function App() {
  return (
    <div className="app">
      <Header />

      <main className="dashboard">
        <Pipeline />

        <KPICards />

        <div className="workspace">
          <Sidebar />

          <section className="main-content">
            <Map />
            <TrendChart />
          </section>

          <CriticalEvent />
        </div>
      </main>
    </div>
  );
}

export default App;