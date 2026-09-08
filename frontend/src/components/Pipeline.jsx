const stages = [
  {
    number: "01",
    title: "DETECT",
    description: "VIIRS 375m",
  },
  {
    number: "02",
    title: "ANALYSE",
    description: "Temporal",
  },
  {
    number: "03",
    title: "CLASSIFY",
    description: "AI + Spectral",
  },
  {
    number: "04",
    title: "PRIORITISE",
    description: "FRP / Risk",
  },
  {
    number: "05",
    title: "ALERT",
    description: "EOC Dispatch",
  },
];

function Pipeline() {
  return (
    <section className="pipeline">
      {stages.map((stage, index) => (
        <div className="pipeline-stage" key={stage.number}>
          <div className="stage-number">{stage.number}</div>

          <div>
            <div className="stage-title">{stage.title}</div>
            <div className="stage-description">{stage.description}</div>
          </div>

          {index < stages.length - 1 && (
            <div className="pipeline-arrow">→</div>
          )}
        </div>
      ))}
    </section>
  );
}

export default Pipeline;