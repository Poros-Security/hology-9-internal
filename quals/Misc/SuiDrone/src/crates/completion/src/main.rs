use serde::Deserialize;
use serde_json::json;
use std::io::Read;
use std::{
    env, fs,
    path::PathBuf,
    sync::Arc,
    time::{SystemTime, UNIX_EPOCH},
};
use suidrone_completion::Store;
use suidrone_sim::Recording;
use tiny_http::{Header, Response, Server, StatusCode};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Redeem {
    attempt_id: String,
    recording: Recording,
}
fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}
fn required(name: &str) -> String {
    env::var(name).unwrap_or_else(|_| panic!("Missing required organizer setting: {name}"))
}
fn main() {
    let dev = env::args().any(|x| x == "--dev");
    let (flag, db, game, challenge, bind) = if dev {
        let root = PathBuf::from(".native-dev");
        fs::create_dir_all(&root).unwrap();
        (
            "FLAG{suidrone_local_test_only}".into(),
            root.join("attempts.sqlite"),
            "development".into(),
            "suidrone-native".into(),
            "127.0.0.1:8787".into(),
        )
    } else {
        (
            required("GZCTF_FLAG"),
            PathBuf::from(required("SUIDRONE_DB")),
            "dynamic".into(),
            "suidrone".into(),
            env::var("SUIDRONE_BIND").unwrap_or("127.0.0.1:8787".into()),
        )
    };
    assert!(!flag.is_empty(), "Backend flag is empty");
    let store = Arc::new(Store::open(&db, game, challenge).expect("attempt database"));
    let server = Arc::new(Server::http(&bind).expect("completion listen"));
    println!("SuiDrone completion service listening on {bind}; 4 bounded replay workers");
    let mut workers = vec![];
    for _ in 0..4 {
        let (server, store, flag) = (
            server.clone(),
            store.clone(),
            flag.clone(),
        );
        workers.push(std::thread::spawn(move || {
            for mut request in server.incoming_requests() {
                let respond = |request: tiny_http::Request, code: u16, value: serde_json::Value| {
                    let response = Response::from_string(value.to_string())
                        .with_status_code(StatusCode(code))
                        .with_header(
                            Header::from_bytes("Content-Type", "application/json").unwrap(),
                        )
                        .with_header(Header::from_bytes("Cache-Control", "no-store").unwrap());
                    let _ = request.respond(response);
                };
                if request.method().as_str() == "GET" && request.url() == "/health" {
                    respond(
                        request,
                        200,
                        json!({"status":"ok","protocol":suidrone_sim::VERSION}),
                    );
                    continue;
                }
                if request.method().as_str() != "POST"
                    || !["/v1/attempts", "/v1/complete"].contains(&request.url())
                {
                    respond(request, 404, json!({"error":"Not found"}));
                    continue;
                }
                // Each DynamicContainer belongs to one GZCTF team. This fixed
                // internal owner scopes SQLite records inside that instance.
                let team = 1;
                if request.url() == "/v1/attempts" {
                    match store.create(team, now()) {
                        Ok(a) => respond(request, 201, serde_json::to_value(a).unwrap()),
                        Err(_) => respond(
                            request,
                            429,
                            json!({"error":"Attempt could not be started. Retry later."}),
                        ),
                    }
                    continue;
                }
                const MAX_BODY: usize = 12 * 1024 * 1024;
                // No chunked/unbounded submissions. Terminate TLS and enforce read deadlines at the supplied proxy.
                if request.body_length().is_none_or(|n| n > MAX_BODY) {
                    respond(request, 413, json!({"error":"Flight recording too large"}));
                    continue;
                }
                let mut body = Vec::new();
                if std::io::Read::take(request.as_reader(), (MAX_BODY + 1) as u64)
                    .read_to_end(&mut body)
                    .is_err()
                    || body.len() > MAX_BODY
                {
                    respond(request, 400, json!({"error":"Invalid flight recording"}));
                    continue;
                }
                let payload = match serde_json::from_slice::<Redeem>(&body) {
                    Ok(p) => p,
                    Err(_) => {
                        respond(request, 400, json!({"error":"Invalid flight recording"}));
                        continue;
                    }
                };
                match store.redeem(team, &payload.attempt_id, &payload.recording, now()) {
                    Ok(()) => respond(request, 200, json!({"flag":flag})),
                    Err(_) => respond(
                        request,
                        403,
                        json!({"error":"Flight did not verify, or attempt is unavailable."}),
                    ),
                }
            }
        }));
    }
    for worker in workers {
        worker.join().unwrap();
    }
}
