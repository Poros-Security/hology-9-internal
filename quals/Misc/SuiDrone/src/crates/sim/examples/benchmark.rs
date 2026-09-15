use suidrone_sim::{Scenario, Simulation};
fn main() {
    let mut sim = Simulation::new(Scenario::default()).unwrap();
    let mut times = Vec::new();
    let start = std::time::Instant::now();
    for _ in 0..30_000 {
        let t = std::time::Instant::now();
        sim.step();
        times.push(t.elapsed().as_secs_f64() * 1000.);
    }
    times.sort_by(f64::total_cmp);
    println!(
        "{}",
        serde_json::json!({"test":"single-drone-rust-physics","ticks":times.len(),"elapsed_seconds":start.elapsed().as_secs_f64(),"mean_ms":times.iter().sum::<f64>()/times.len() as f64,"p95_ms":times[times.len()*95/100],"p99_ms":times[times.len()*99/100],"max_ms":times.last(),"step_budget_ms":20})
    );
}
