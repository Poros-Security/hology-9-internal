from dataclasses import dataclass
import secrets

from tickets import sign, verify


@dataclass(frozen=True)
class Slice:
    name: str
    sst: int
    sd: str
    dnn: str = "internet"

    @property
    def snssai(self):
        return f"{self.sst}-{self.sd}"


FREE = Slice("Free", 1, "000001")
PREMIUM = Slice("Premium", 1, "000099")
TELEMETRY = Slice("Telemetry", 2, "000001", "iot")
SLICES = (FREE, PREMIUM, TELEMETRY)
SUPI = "imsi-001010000000042"


class Denied(ValueError):
    pass


@dataclass
class Plan:
    target: Slice
    revision: int = 1
    approval: str = ""
    closed: bool = False


class Network:
    def __init__(self, *, secure=False, strict_tickets=False, bind_revision=False):
        self.secure = secure
        self.strict_tickets = secure or strict_tickets
        self.bind_revision = secure or bind_revision
        self.registered = False
        self.authorized = None
        self.active = None
        self.requested = None
        self.cache = {}
        self.events = []
        self.completed = False
        self.context = secrets.token_hex(12)
        self.ticket_key = secrets.token_bytes(32)
        self.approval_key = secrets.token_bytes(32)
        self.issued = set()
        self.handover = False
        self.plans = {}
        self.committed_plan = None

    def log(self, message):
        self.events.append(message)
        self.events = self.events[-24:]

    def register(self):
        self.registered = True
        self.log(f"AMF: authenticated {SUPI}; UDM subscribed NSSAI={FREE.snssai}")
        return "Registration accepted. Subscribed slice: 1-000001 (Free)."

    def authorize(self, sst, sd, dnn):
        if not self.registered:
            raise Denied("AMF: register the SIM first.")
        target = next((s for s in SLICES if (s.sst, s.sd, s.dnn) == (sst, sd, dnn)), None)
        if target is None:
            raise Denied("NSSF: unknown S-NSSAI/DNN combination; consult slices.")
        self.requested = target
        self.authorized = None
        self.active = None
        self.log(f"UE -> NSSF: requested={target.snssai} dnn={dnn}")
        key = (SUPI, sst, sd, dnn)
        if key in self.cache:
            self.log(f"NSSF: cache HIT key={key}; ALLOW reused")
        else:
            self.log(f"NSSF: cache MISS key={key}; querying subscription")
            if target != FREE:
                self.log(f"UDM: DENY {target.snssai}; absent from subscription")
                raise Denied("UDM: requested slice is not included in the Free subscription.")
            self.cache[key] = True
            self.log("UDM: ALLOW; positive decision cached")
        self.authorized = target
        self.log(f"NSSF -> AMF: Allowed NSSAI={target.snssai}")
        return f"Allowed NSSAI: {target.snssai} ({target.name})."

    def session(self, dnn):
        if self.authorized is None:
            raise Denied("SMF: no authorized slice. Request authorization first.")
        if dnn != self.authorized.dnn:
            raise Denied("SMF: DNN does not match the authorization.")
        self.active = self.authorized
        self.log(f"SMF -> UPF: installed route for {self.active.snssai}, DNN={dnn}")
        return f"PDU session established: {self.active.name} / {dnn}."

    def export_ticket(self):
        if self.active != FREE:
            raise Denied("Broker: a Free PDU session is required for diagnostics.")
        nonce = secrets.token_hex(12)
        self.issued.add(nonce)
        token = sign({"kind": "handover", "ctx": self.context, "supi": SUPI,
                      "scope": "inspect", "jti": nonce}, self.ticket_key)
        self.log("Issuer: emitted inspect ticket using pair-map codec v1")
        return token

    def import_ticket(self, token):
        try:
            claims = verify(token, self.ticket_key, strict=self.strict_tickets)
        except (ValueError, TypeError, RecursionError):
            raise Denied("Broker: invalid ticket.") from None
        if (claims.get("kind") != "handover" or claims.get("ctx") != self.context
                or claims.get("supi") != SUPI or claims.get("jti") not in self.issued
                or claims.get("scope") not in ("inspect", "handover")):
            raise Denied("Broker: ticket context, scope or nonce rejected.")
        self.issued.remove(claims["jti"])
        self.handover = claims["scope"] == "handover"
        self.log(f"Broker: verified ticket; object decoder v2 scope={claims['scope']}")
        return f"Broker capability: {claims['scope']}."

    def require_handover(self):
        if not self.handover:
            raise Denied("Broker: handover capability required.")

    def plan_create(self, sst, sd, dnn):
        self.require_handover()
        if self.active is None:
            raise Denied("Broker: establish a source PDU session first.")
        target = self.find_slice(sst, sd, dnn)
        if len(self.plans) >= 8:
            raise Denied("Broker: plan limit reached. Reset to start a new context.")
        identifier = secrets.token_hex(8)
        self.plans[identifier] = Plan(target)
        self.log(f"Broker: created plan {identifier} revision=1")
        return identifier

    @staticmethod
    def find_slice(sst, sd, dnn):
        target = next((s for s in SLICES if (s.sst, s.sd, s.dnn) == (sst, sd, dnn)), None)
        if target is None:
            raise Denied("NSSF: unknown S-NSSAI/DNN combination; consult slices.")
        return target

    def get_plan(self, identifier):
        self.require_handover()
        plan = self.plans.get(identifier)
        if plan is None or plan.closed:
            raise Denied("Broker: plan not found or already committed.")
        return plan

    def plan_check(self, identifier):
        plan = self.get_plan(identifier)
        if plan.target != FREE:
            self.log(f"Policy: plan {identifier} revision={plan.revision} DENY")
            raise Denied("Policy: target slice is not included in the Free subscription.")
        plan.approval = sign({"kind": "approval", "ctx": self.context, "plan": identifier,
                              "revision": plan.revision, "snssai": plan.target.snssai,
                              "dnn": plan.target.dnn}, self.approval_key)
        self.log(f"Policy: plan {identifier} revision={plan.revision} ALLOW")
        return plan.approval

    def plan_edit(self, identifier, sst, sd, dnn):
        plan = self.get_plan(identifier)
        plan.target = self.find_slice(sst, sd, dnn)
        plan.revision += 1
        if self.bind_revision:
            plan.approval = ""
        self.log(f"Broker: updated plan {identifier} revision={plan.revision}")
        return f"Plan updated: {identifier} revision={plan.revision}."

    def plan_commit(self, approval):
        self.require_handover()
        try:
            receipt = verify(approval, self.approval_key, strict=True)
        except (ValueError, TypeError, RecursionError):
            raise Denied("SMF: invalid policy receipt.") from None
        if receipt.get("kind") != "approval" or receipt.get("ctx") != self.context:
            raise Denied("SMF: receipt context rejected.")
        plan = self.get_plan(receipt.get("plan"))
        if approval != plan.approval:
            raise Denied("SMF: policy approval missing or superseded.")
        if self.bind_revision and (receipt.get("revision") != plan.revision
                                  or receipt.get("snssai") != plan.target.snssai
                                  or receipt.get("dnn") != plan.target.dnn):
            raise Denied("SMF: policy revision mismatch.")
        # The worker checks the stored approval but dereferences the mutable plan.
        self.authorized = plan.target
        self.active = None
        self.requested = plan.target
        plan.closed = True
        self.committed_plan = receipt["plan"]
        self.log(f"SMF: committed receipt revision={receipt['revision']}; plan revision={plan.revision}")
        return f"Handover committed. Allowed NSSAI: {plan.target.snssai} ({plan.target.name})."

    def plan_status(self, identifier):
        plan = self.get_plan(identifier)
        return {"id": identifier, "revision": plan.revision,
                "target": plan.target.snssai, "dnn": plan.target.dnn,
                "approval_present": bool(plan.approval)}

    def surf(self, target):
        if target not in ("portal", "vault"):
            raise Denied("DNS: unknown service. Available services: portal, vault.")
        if self.active is None:
            raise Denied("UPF: no PDU session. Establish a session first.")
        if target == "portal":
            self.log("UPF -> portal: 200 OK")
            return "Free captive portal: connected. Your billing plan is FREE."
        if self.active != PREMIUM:
            self.log("UPF -> vault: 403 PREMIUM_SLICE_REQUIRED")
            raise Denied("Vault: 403 PREMIUM_SLICE_REQUIRED (1-000099).")
        self.completed = True
        self.log("UPF -> vault: 200 OK; premium slice verified")
        return "Vault: 200 OK; premium slice verified."

    def evidence(self):
        return {
            "scenario_id": "sui5g-free-surfing",
            "challenge_version": 2,
            "mode": "SIMULATED",
            "subscription": "FREE",
            "subscribed_nssai": FREE.snssai,
            "authorized_nssai": self.authorized.snssai if self.authorized else None,
            "active_nssai": self.active.snssai if self.active else None,
            "handover_capability": self.handover,
            "committed_plan": self.committed_plan,
            "impact_verified": self.completed,
        }
