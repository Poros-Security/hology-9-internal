use base64::{Engine as _, engine::general_purpose::STANDARD};
use ed25519_dalek::{Signature, VerifyingKey};
use rand::RngCore;
use rusqlite::{Connection, OptionalExtension, params};
use sha2::{Digest, Sha256};
use std::{collections::HashSet, path::Path, sync::Mutex};
use suidrone_sim::{Attempt, Recording, Scenario, validate_completion};

pub fn verify_team(token: &str, key: &VerifyingKey) -> Result<i32, &'static str> {
    if token.len() > 160 {
        return Err("Challenge seal could not be verified.");
    }
    let (id, signature) = token
        .split_once(':')
        .ok_or("Challenge seal could not be verified.")?;
    let team = id
        .parse::<i32>()
        .map_err(|_| "Challenge seal could not be verified.")?;
    // Canonical form removes ambiguous IDs; GZCTF itself issues decimal positive IDs.
    if team <= 0 || team.to_string() != id {
        return Err("Challenge seal could not be verified.");
    }
    let bytes = STANDARD
        .decode(signature)
        .map_err(|_| "Challenge seal could not be verified.")?;
    let signature =
        Signature::from_slice(&bytes).map_err(|_| "Challenge seal could not be verified.")?;
    key.verify_strict(format!("GZCTF_TEAM_{team}").as_bytes(), &signature)
        .map_err(|_| "Challenge seal could not be verified.")?;
    Ok(team)
}

pub fn public_key(base64: &str) -> Result<VerifyingKey, String> {
    let decoded = STANDARD
        .decode(base64.trim())
        .map_err(|_| "Expected GZCTF game PublicKey in standard base64")?;
    let bytes: [u8; 32] = decoded
        .try_into()
        .map_err(|_| "Game public key must be 32 bytes")?;
    VerifyingKey::from_bytes(&bytes).map_err(|_| "Invalid game public key".into())
}
pub fn allowlist(path: &Path) -> Result<HashSet<i32>, String> {
    std::fs::read_to_string(path)
        .map_err(|_| "Cannot read allowed-team file".to_owned())?
        .lines()
        .map(str::trim)
        .filter(|s| !s.is_empty() && !s.starts_with('#'))
        .map(|s| {
            s.parse::<i32>()
                .ok()
                .filter(|n| *n > 0)
                .ok_or_else(|| "Invalid allowed-team ID".to_owned())
        })
        .collect()
}

pub struct Store {
    db: Mutex<Connection>,
    pub game_id: String,
    pub challenge_id: String,
}
impl Store {
    pub fn open(path: &Path, game_id: String, challenge_id: String) -> Result<Self, String> {
        let db = Connection::open(path).map_err(|e| e.to_string())?;
        db.execute_batch("PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000; CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,team INTEGER NOT NULL,game TEXT NOT NULL,challenge TEXT NOT NULL,created INTEGER NOT NULL,expires INTEGER NOT NULL,scenario TEXT NOT NULL,redeemed_hash TEXT);").map_err(|e|e.to_string())?;
        Ok(Self {
            db: Mutex::new(db),
            game_id,
            challenge_id,
        })
    }
    pub fn create(&self, team: i32, now: u64) -> Result<Attempt, &'static str> {
        let db = self.db.lock().map_err(|_| "Service unavailable")?;
        db.execute(
            "DELETE FROM attempts WHERE expires < ?",
            [now.saturating_sub(86400)],
        )
        .map_err(|_| "Service unavailable")?;
        let count:u64=db.query_row("SELECT COUNT(*) FROM attempts WHERE team=? AND game=? AND challenge=? AND created>?",params![team,self.game_id,self.challenge_id,now.saturating_sub(3600)],|r|r.get(0)).map_err(|_|"Service unavailable")?;
        if count >= 10 {
            return Err("Attempt limit reached. Retry later.");
        }
        let mut bytes = [0u8; 24];
        rand::thread_rng().fill_bytes(&mut bytes);
        let id = bytes.iter().map(|b| format!("{b:02x}")).collect::<String>();
        let scenario = Scenario {
            entrance: (bytes[0] % 4),
            ..Scenario::default()
        };
        let attempt = Attempt {
            id,
            game_id: self.game_id.clone(),
            challenge_id: self.challenge_id.clone(),
            expires_at: now + 4 * 3600,
            scenario,
        };
        db.execute("INSERT INTO attempts(id,team,game,challenge,created,expires,scenario) VALUES(?,?,?,?,?,?,?)",params![attempt.id,team,self.game_id,self.challenge_id,now,attempt.expires_at,serde_json::to_string(&attempt.scenario).unwrap()]).map_err(|_|"Service unavailable")?;
        Ok(attempt)
    }
    pub fn redeem(
        &self,
        team: i32,
        id: &str,
        record: &Recording,
        now: u64,
    ) -> Result<(), &'static str> {
        if id.len() != 48 || !id.bytes().all(|c| c.is_ascii_hexdigit()) {
            return Err("Completion could not be verified.");
        }
        let hash = format!(
            "{:x}",
            Sha256::digest(serde_json::to_vec(record).map_err(|_| "Invalid flight")?)
        );
        let scenario = {
            let db = self.db.lock().map_err(|_| "Service unavailable")?;
            let row:Option<(u64,String,Option<String>)>=db.query_row("SELECT expires,scenario,redeemed_hash FROM attempts WHERE id=? AND team=? AND game=? AND challenge=?",params![id,team,self.game_id,self.challenge_id],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?))).optional().map_err(|_|"Service unavailable")?;
            let (expiry, scenario, redeemed) = row.ok_or("Completion could not be verified.")?;
            if now >= expiry {
                return Err("Attempt expired. Start a new attempt.");
            }
            if let Some(previous) = redeemed {
                return if previous == hash {
                    Ok(())
                } else {
                    Err("Attempt already redeemed with a different flight.")
                };
            }
            serde_json::from_str::<Scenario>(&scenario).map_err(|_| "Service unavailable")?
        };
        validate_completion(record, &scenario)?;
        let db = self.db.lock().map_err(|_| "Service unavailable")?;
        db.execute(
            "UPDATE attempts SET redeemed_hash=? WHERE id=? AND team=? AND redeemed_hash IS NULL",
            params![hash, id, team],
        )
        .map_err(|_| "Service unavailable")?;
        let stored: String = db
            .query_row(
                "SELECT redeemed_hash FROM attempts WHERE id=? AND team=?",
                params![id, team],
                |r| r.get(0),
            )
            .map_err(|_| "Service unavailable")?;
        if stored == hash {
            Ok(())
        } else {
            Err("Attempt already redeemed with a different flight.")
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::{Signer, SigningKey};
    fn token(key: &SigningKey, id: i32) -> String {
        format!(
            "{id}:{}",
            STANDARD.encode(key.sign(format!("GZCTF_TEAM_{id}").as_bytes()).to_bytes())
        )
    }
    #[test]
    fn exact_gzctf_contract() {
        let key = SigningKey::from_bytes(&[7; 32]);
        let t = token(&key, 12);
        assert_eq!(verify_team(&t, &key.verifying_key()), Ok(12));
        assert!(verify_team(&t.replacen("12:", "13:", 1), &key.verifying_key()).is_err());
        assert!(verify_team(&t, &SigningKey::from_bytes(&[8; 32]).verifying_key()).is_err());
        assert!(verify_team("12:broken", &key.verifying_key()).is_err());
        assert!(verify_team(&format!("0{t}"), &key.verifying_key()).is_err());
    }
    #[test]
    fn ownership_expiration_and_scope_fail_closed() {
        let s = Store::open(Path::new(":memory:"), "game".into(), "challenge".into()).unwrap();
        let a = s.create(12, 10000).unwrap();
        let r = Recording::new(a.scenario.clone());
        assert!(s.redeem(13, &a.id, &r, 10001).is_err());
        assert!(s.redeem(12, &a.id, &r, a.expires_at).is_err());
        assert!(s.redeem(12, &a.id, &r, 10001).is_err());
        for _ in 0..9 {
            s.create(12, 10001).unwrap();
        }
        assert!(s.create(12, 10001).is_err());
    }
    #[test]
    fn redeemed_attempt_is_scoped_to_game_and_challenge() {
        let mut s = Store::open(Path::new(":memory:"), "game".into(), "challenge".into()).unwrap();
        let a = s.create(12, 10000).unwrap();
        let r = Recording::new(a.scenario.clone());
        // Seed a previously verified hash to isolate scope checks from flight validity.
        let hash = format!("{:x}", Sha256::digest(serde_json::to_vec(&r).unwrap()));
        s.db.lock()
            .unwrap()
            .execute(
                "UPDATE attempts SET redeemed_hash=? WHERE id=?",
                params![hash, a.id],
            )
            .unwrap();
        assert!(s.redeem(12, &a.id, &r, 10001).is_ok());
        s.game_id = "wrong-game".into();
        assert!(s.redeem(12, &a.id, &r, 10001).is_err());
        s.game_id = "game".into();
        s.challenge_id = "wrong-challenge".into();
        assert!(s.redeem(12, &a.id, &r, 10001).is_err());
    }
}
