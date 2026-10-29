"""
app.py - ALL the Python of the Campus Access Control System, in ONE file.

  Part 1: YOUR original code (same names: students, faculty, staff, visitors,
          authorized_user, restricted_user, facilities, access_relation,
          get_user_type, check_access, view_sets, view_relations, view_matrix,
          explain_system, add_user) - returning data instead of printing, plus
          user IDs, an editable relation, an access log and saving to a file.
  Part 2: Flask - the page and the API.

The whole website (HTML + CSS + JavaScript) is ONE file: templates/index.html
The page only DRAWS things. Every decision (login, access rule, proof, math) is made here.

Run:    pip install flask
        python app.py          then open  http://127.0.0.1:5000
Login:  admin / admin123        or a user: name + ID number (example: Ck / 2024102)
"""
import hashlib
import heapq
import hmac
import json
import os
import random
from collections import deque
from datetime import datetime
from functools import wraps
from math import comb, gcd, perm

from flask import Flask, jsonify, render_template, request, session

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

# =====================================================================
#  PART 1 - YOUR ORIGINAL CODE
# =====================================================================

# ---- SETS ----
students = {"Nathaniel", "Ck", "Luke"}
faculty = {"Sir. Tabaghak", "Sir. Ramil"}
staff = {"Mayet", "Simpor"}
visitors = {"Visitor1", "Visitor2"}
authorized_user = {"Ck", "Sir. Tabaghak", "Mayet"}
restricted_user = {"Luke"}

# every user also has an ID number (used for the number theory check)
user_ids = {"Nathaniel": 2024101, "Ck": 2024102, "Luke": 2024103,
            "Sir. Tabaghak": 1001, "Sir. Ramil": 1002,
            "Mayet": 3001, "Simpor": 3002, "Visitor1": 9001, "Visitor2": 9002}

facilities = [
    "Library",
    "ComLab",
    "Faculty Room",
    "Office",
    "ComLec"
]

user_types = [
    "Student",
    "Faculty",
    "Staff",
    "Visitor"
]

# ---- RELATION: (user type, facility). The admin can change it on the Relations page ----
access_relation = {
    ("Student", "Library"),
    ("Student", "ComLab"),
    ("Student", "ComLec"),

    ("Faculty", "Library"),
    ("Faculty", "ComLab"),
    ("Faculty", "Faculty Room"),
    ("Faculty", "Office"),
    ("Faculty", "ComLec"),

    ("Staff", "Library"),
    ("Staff", "Office"),
}

settings = {"even_rule": False}      # NUMBER THEORY: ComLab needs an even ID (ID mod 2 = 0)
access_log = []                      # the last 50 checks

SETS_BY_TYPE = {"Student": students, "Faculty": faculty, "Staff": staff, "Visitor": visitors}


def get_user_type(name):
    if name in students:
        return "Student"

    elif name in faculty:
        return "Faculty"

    elif name in staff:
        return "Staff"

    elif name in visitors:
        return "Visitor"

    else:
        return "Unknown"


def _decide(user_type, is_authorized, is_restricted, user_id, facility):
    """YOUR rule:  allowed = (type is in the relation  OR  authorized for the Library)
                            AND NOT restricted  [AND even ID for ComLab, if that rule is on]"""
    in_relation = (user_type, facility) in access_relation
    via_authorized = facility == "Library" and is_authorized
    P = in_relation or via_authorized
    id_is_even = user_id % 2 == 0                                     # number theory: ID mod 2
    id_rule_failed = facility == "ComLab" and settings["even_rule"] and not id_is_even
    allowed = P and not is_restricted and not id_rule_failed
    return {"in_relation": in_relation, "via_authorized": via_authorized, "P": P,
            "id_is_even": id_is_even, "id_rule_failed": id_rule_failed, "allowed": allowed}


def check_access(name, user_id, facility):
    """Returns the result AND the step-by-step process (nothing is printed)."""
    user_type = get_user_type(name)
    is_authorized = name in authorized_user
    is_restricted = name in restricted_user
    r = _decide(user_type, is_authorized, is_restricted, user_id, facility)
    yes = lambda value: "true" if value else "false"

    if r["in_relation"]:
        relation_text = f"({user_type}, {facility}) is in the relation"
    elif r["via_authorized"]:
        relation_text = f"{name} is authorized for Library"
    else:
        relation_text = f"({user_type}, {facility}) is not in the relation"
    steps = [
        {"ok": user_type != "Unknown", "title": "Find the user type",
         "detail": f"{name} belongs to the set of {user_type}s" if user_type != "Unknown"
         else f"{name} is in no set (Unknown)"},
        {"ok": r["P"], "title": "Look up the relation", "detail": relation_text},
        {"ok": not is_restricted, "title": "Apply NOT restricted",
         "detail": "R = True, so \u00acR = False" if is_restricted else "R = False, so \u00acR = True"},
    ]
    if facility == "ComLab":
        text = f"{user_id} mod 2 = {user_id % 2}, ID is {'even' if r['id_is_even'] else 'odd'}"
        if settings["even_rule"]:
            text += ", rule satisfied" if r["id_is_even"] else ", even-ID rule fails"
        else:
            text += " (rule is off)"
        steps.append({"ok": not r["id_rule_failed"], "title": "Number theory check", "detail": text})
    extra = "\u2227 even ID " if facility == "ComLab" and settings["even_rule"] else ""
    steps.append({"ok": r["allowed"], "title": "Final decision",
                  "detail": f"relation \u2227 \u00acR {extra}= {yes(r['allowed'])}"})
    return {"name": name, "user_id": user_id, "user_type": user_type, "facility": facility,
            "allowed": r["allowed"], "steps": steps}


def view_sets():
    """The sets, with the letters used in the logic proof (S, F, T, V, A, R)."""
    return [
        {"key": "Student", "letter": "S", "title": "Students", "members": sorted(students)},
        {"key": "Faculty", "letter": "F", "title": "Faculty", "members": sorted(faculty)},
        {"key": "Staff", "letter": "T", "title": "Staff", "members": sorted(staff)},
        {"key": "Visitor", "letter": "V", "title": "Visitors", "members": sorted(visitors)},
        {"key": "A", "letter": "A", "title": "Authorized users", "members": sorted(authorized_user)},
        {"key": "R", "letter": "R", "title": "Restricted users", "members": sorted(restricted_user)},
    ]


def view_relations():
    return [list(pair) for pair in sorted(access_relation)]


def view_matrix():
    """The access matrix is built from the relation, so toggling a cell changes the real rules."""
    return [[1 if (t, f) in access_relation else 0 for f in facilities] for t in user_types]


def explain_system():
    return """=================================
       SYSTEM EXPLANATION
=================================
1. PROPOSITIONAL LOGIC

   Example Library Rule:    L = (S OR F OR T OR A) AND NOT R

   S = STUDENT    F = FACULTY    T = STAFF
   A = AUTHORIZED R = RESTRICTED

2. SETS
   Users are classified into sets: students, faculty, staff,
   visitors, authorized users, restricted users.

3. RELATIONS
   Access is represented as (USER TYPE, FACILITY).
   Example: (STUDENT, LIBRARY) means a student can access the library.

4. BOOLEAN EXPRESSIONS
   The program uses AND, OR, NOT.
   Example:  (is_student or is_faculty) and not is_restricted

5. MATRICES
   Rows represent user types, columns represent facilities.
   1 = allowed, 0 = denied.

6. NUMBER THEORY
   The computer laboratory checks ID mod 2 = 0.
   If the remainder is zero, the ID number is even.

7. LOGICAL CONSISTENCY / PROOF
   If a user is restricted, then R = True.
   The rule contains  P AND NOT R,  so:
       True AND False = False
       False AND False = False
   The result is always False. Therefore a restricted user
   cannot receive normal access. This proves that the access
   restriction rule is logically consistent."""


def proof_check():
    """Runs the real rule on every restricted user and on every user type with R = True."""
    cases, bad = 0, []
    for name in [n for n in user_ids if n in restricted_user]:
        for f in facilities:
            cases += 1
            if check_access(name, user_ids.get(name, 0), f)["allowed"]:
                bad.append(f"{name} at {f}")
    for t in user_types:
        for a in (False, True):
            for f in facilities:
                cases += 1
                if _decide(t, a, True, 0, f)["allowed"]:
                    bad.append(f"{t} at {f}")
    return cases, bad


# ---------------- users ----------------
def user_info(name):
    return {"name": name, "type": get_user_type(name), "id": user_ids.get(name),
            "authorized": name in authorized_user, "restricted": name in restricted_user}


def all_names():
    return list(user_ids)


def remove_user(name):
    for s in (students, faculty, staff, visitors, authorized_user, restricted_user):
        s.discard(name)
    user_ids.pop(name, None)


def add_user(name, user_id, user_type, authorized, restricted, original=""):
    """Your add_user(), with an ID. If 'original' is given, that user is edited instead."""
    name = name.strip()
    if not name:
        return False, "Type a name first."
    if user_type not in SETS_BY_TYPE:
        return False, "Invalid choice."
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return False, "Enter a number for the ID."
    for other, other_id in user_ids.items():
        if other == original:
            continue
        if other.lower() == name.lower():
            return False, f'"{other}" already exists (names are not case sensitive).'
        if other_id == user_id:
            return False, f"ID {user_id} already belongs to {other}."
    if original:
        remove_user(original)
    SETS_BY_TYPE[user_type].add(name)
    user_ids[name] = user_id
    if authorized:
        authorized_user.add(name)
    if restricted:
        restricted_user.add(name)
    return True, f"{name} {'updated' if original else 'added'}"


def toggle_relation(user_type, facility):
    pair = (user_type, facility)
    if user_type in user_types and facility in facilities:
        access_relation.symmetric_difference_update({pair})


# ---------------- saving / backup ----------------
def relation_list():
    """The relation as 'Type|Facility' text, in a steady order."""
    return [f"{t}|{f}" for t in user_types for f in facilities if (t, f) in access_relation]


def export_data():
    return {"users": {n: {"t": get_user_type(n), "id": user_ids[n], "a": int(n in authorized_user),
                          "r": int(n in restricted_user)} for n in user_ids},
            "rel": relation_list(), "even": settings["even_rule"], "log": list(access_log)}


def import_data(d):
    """Check the data first, then replace everything. Raises ValueError if it is not valid."""
    if not isinstance(d, dict) or not isinstance(d.get("users"), dict) or not isinstance(d.get("rel"), list):
        raise ValueError("bad data")
    users = {}
    for n, u in d["users"].items():
        if not isinstance(u, dict) or u.get("t") not in SETS_BY_TYPE:
            raise ValueError("bad user")
        users[str(n)] = (u["t"], int(u["id"]), bool(u.get("a")), bool(u.get("r")))
    pairs = set()
    for x in d["rel"]:
        pair = tuple(x.split("|", 1)) if isinstance(x, str) else tuple(x) if isinstance(x, (list, tuple)) else ()
        if len(pair) == 2 and pair[0] in user_types and pair[1] in facilities:
            pairs.add(pair)
    for group in (students, faculty, staff, visitors, authorized_user, restricted_user):
        group.clear()
    user_ids.clear()
    for n, (t, i, a, r) in users.items():
        SETS_BY_TYPE[t].add(n)
        user_ids[n] = i
        if a:
            authorized_user.add(n)
        if r:
            restricted_user.add(n)
    access_relation.clear()
    access_relation.update(pairs)
    settings["even_rule"] = bool(d.get("even"))
    access_log[:] = [x for x in d["log"] if isinstance(x, dict)][:50] if isinstance(d.get("log"), list) else []


DEFAULT_DATA = json.loads(json.dumps(export_data()))   # the starting data, used by "Reset"
DEFAULT_DATA["log"] = []


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(export_data(), f, indent=2)
    except OSError:
        pass


def load_data():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            import_data(json.load(f))
    except (OSError, ValueError, TypeError, KeyError):
        pass



# =====================================================================
#  PART 1B - THE FINAL PROJECT FEATURES (pure Python, no Flask here)
# =====================================================================

# ---------------------------------------------------------------------
#  1. CRYPTOGRAPHY
#     Caesar cipher:  E(x) = (x + k) mod 26      D(y) = (y - k) mod 26
#     SHA-256 hash:   a one-way fingerprint, so passwords are not stored or compared as plain text
# ---------------------------------------------------------------------
def caesar(text, k, decrypt=False):
    """Shift every letter by k places. Returns (new text, first few worked steps)."""
    k = -k if decrypt else k
    out, steps = [], []
    for ch in text:
        if ch.isascii() and ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            x = ord(ch) - base                      # A=0 ... Z=25
            y = (x + k) % 26                        # the shift, wrapped around by mod 26
            out.append(chr(y + base))
            if len(steps) < 6:
                sign = "+" if k >= 0 else "-"
                steps.append(f"{ch}: x = {x}, ({x} {sign} {abs(k)}) mod 26 = {y}, so {chr(y + base)}")
        else:
            out.append(ch)                          # digits, spaces and symbols stay the same
    return "".join(out), steps


def sha256(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------
#  2. SORTING AND SEARCHING  (they count their comparisons so you can compare speed)
# ---------------------------------------------------------------------
def user_rows():
    return [{"name": n, "type": get_user_type(n), "id": user_ids[n]} for n in user_ids]


def merge_sort(rows, key):
    """Merge sort: split in half, sort each half (recursion), then merge. About n log n comparisons."""
    count = [0]

    def sort(a):
        if len(a) <= 1:
            return a
        mid = len(a) // 2
        left, right = sort(a[:mid]), sort(a[mid:])
        merged, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            count[0] += 1
            if key(left[i]) <= key(right[j]):
                merged.append(left[i]); i += 1
            else:
                merged.append(right[j]); j += 1
        return merged + left[i:] + right[j:]

    return sort(list(rows)), count[0]


def bubble_sort(rows, key):
    """Bubble sort: swap neighbours that are out of order. About n squared comparisons."""
    a, count = list(rows), 0
    for i in range(len(a) - 1):
        swapped = False
        for j in range(len(a) - 1 - i):
            count += 1
            if key(a[j]) > key(a[j + 1]):
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a, count


def linear_search(names, target):
    """Check one by one from the start. Up to n steps."""
    steps = []
    for i, n in enumerate(names):
        hit = n.lower() == target
        steps.append({"text": f'Position {i}: "{n}" {"= match" if hit else "is not it"}', "hit": hit})
        if hit:
            return i, steps
    return -1, steps


def binary_search(names, target):
    """Needs a SORTED list. Look at the middle, throw away the wrong half. About log2(n) steps."""
    lo, hi, steps = 0, len(names) - 1, []
    while lo <= hi:
        mid = (lo + hi) // 2
        here = names[mid].lower()
        if here == target:
            steps.append({"text": f'Middle (position {mid}) is "{names[mid]}" = match', "hit": True})
            return mid, steps
        if here < target:
            steps.append({"text": f'Middle "{names[mid]}" comes before the target, keep the right half', "hit": False})
            lo = mid + 1
        else:
            steps.append({"text": f'Middle "{names[mid]}" comes after the target, keep the left half', "hit": False})
            hi = mid - 1
    return -1, steps


# ---------------------------------------------------------------------
#  3 + 6. GRAPH (campus map) and RECURSION (all routes)
#     Vertices = locations, edges = paths, weights = walking distance in metres
# ---------------------------------------------------------------------
CAMPUS_EDGES = [("Gate", "Library", 50), ("Gate", "Office", 80), ("Library", "ComLab", 30),
                ("Library", "ComLec", 60), ("ComLab", "ComLec", 20), ("ComLec", "Faculty Room", 40),
                ("Office", "Faculty Room", 25)]
CAMPUS = {}                                                  # adjacency list: {place: {neighbour: distance}}
for _a, _b, _w in CAMPUS_EDGES:
    CAMPUS.setdefault(_a, {})[_b] = _w
    CAMPUS.setdefault(_b, {})[_a] = _w
CAMPUS_NODES = ["Gate"] + facilities
CAMPUS_POS = {"Gate": [40, 120], "Library": [130, 45], "ComLab": [250, 45], "ComLec": [300, 120],
              "Faculty Room": [250, 200], "Office": [130, 200]}


def all_routes(graph, a, b, path=None):
    """RECURSION: from a, try every neighbour not yet visited; stop when we reach b (depth first search)."""
    path = (path or []) + [a]
    if a == b:                                               # base case
        return [path]
    routes = []
    for nxt in sorted(graph[a]):
        if nxt not in path:                                  # never walk in circles
            routes += all_routes(graph, nxt, b, path)        # recursive case
    return routes


def route_length(graph, path):
    return sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1))


def shortest_route(graph, a, b):
    """Dijkstra: always expand the closest unfinished place first."""
    dist = {n: float("inf") for n in graph}
    dist[a], prev, heap = 0, {}, [(0, a)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u].items():
            if d + w < dist[v]:
                dist[v], prev[v] = d + w, u
                heapq.heappush(heap, (dist[v], v))
    if dist[b] == float("inf"):
        return None, None
    path = [b]
    while path[-1] != a:
        path.append(prev[path[-1]])
    return path[::-1], dist[b]


def reachable(graph, start):
    """Breadth first search: everything we can walk to from start."""
    seen, queue = {start}, deque([start])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


def graph_info():
    matrix = [[1 if m in CAMPUS[n] else 0 for m in CAMPUS_NODES] for n in CAMPUS_NODES]
    return {"nodes": CAMPUS_NODES, "pos": CAMPUS_POS, "edges": CAMPUS_EDGES, "matrix": matrix,
            "connected": len(reachable(CAMPUS, "Gate")) == len(CAMPUS)}


# ---------------------------------------------------------------------
#  7. TREE (campus organisation) with RECURSIVE traversal
# ---------------------------------------------------------------------
CAMPUS_TREE = {"Campus": {"Academic Building": {"Library": {}, "ComLab": {}, "ComLec": {}},
                          "Admin Building": {"Office": {}, "Faculty Room": {}}}}


def tree_json(name, kids):
    return {"name": name, "children": [tree_json(k, v) for k, v in kids.items()]}


def preorder(name, kids):                                    # parent first, then children
    out = [name]
    for k, v in kids.items():
        out += preorder(k, v)
    return out


def postorder(name, kids):                                   # children first, then parent
    out = []
    for k, v in kids.items():
        out += postorder(k, v)
    return out + [name]


def tree_height(kids):
    return 0 if not kids else 1 + max(tree_height(v) for v in kids.values())


def count_leaves(name, kids):
    return 1 if not kids else sum(count_leaves(k, v) for k, v in kids.items())


def find_in_tree(name, kids, target):
    """RECURSION: the path from the root down to target, or None."""
    if name == target:
        return [name]
    for k, v in kids.items():
        sub = find_in_tree(k, v, target)
        if sub:
            return [name] + sub
    return None


def tree_info(find=""):
    root, kids = next(iter(CAMPUS_TREE.items()))
    return {"tree": tree_json(root, kids), "preorder": preorder(root, kids), "postorder": postorder(root, kids),
            "height": tree_height(kids), "leaves": count_leaves(root, kids), "found": find_in_tree(root, kids, find) if find else None}


# ---------------------------------------------------------------------
#  4 + 5. COUNTING, PROBABILITY and a RANDOM VARIABLE
#     X = number of users who get access, among k users picked at random (no repeats).
#     This is the hypergeometric distribution:  P(X = x) = C(g, x) * C(n - g, k - x) / C(n, k)
# ---------------------------------------------------------------------
def granted_flags(facility):
    return [_decide(get_user_type(n), n in authorized_user, n in restricted_user, user_ids[n], facility)["allowed"]
            for n in user_ids]


def probability_lab(facility, k, trials):
    flags = granted_flags(facility)
    n, g = len(flags), sum(flags)
    if n == 0:
        raise ValueError("There are no users yet.")
    if not 1 <= k <= n:
        raise ValueError(f"Pick a sample size between 1 and {n}.")
    if not 1 <= trials <= 20000:
        raise ValueError("Trials must be between 1 and 20000.")
    p = g / n
    low, high = max(0, k - (n - g)), min(g, k)
    pmf = {x: comb(g, x) * comb(n - g, k - x) / comb(n, k) for x in range(low, high + 1)}
    mean = k * p
    var = k * p * (1 - p) * (n - k) / (n - 1) if n > 1 else 0.0
    counts, hits = {x: 0 for x in pmf}, 0
    for _ in range(trials):
        counts[sum(random.sample(flags, k))] += 1            # one random group of k users
        hits += random.choice(flags)                         # one random single user
    return {"facility": facility, "n": n, "g": g, "k": k, "trials": trials,
            "ways_choose": comb(n, k), "ways_line_up": perm(n, k),
            "p_exact": p, "p_sim": hits / trials,
            "pmf": [{"x": x, "exact": pmf[x], "sim": counts[x] / trials} for x in pmf],
            "mean_exact": mean, "var_exact": var,
            "mean_sim": sum(x * c for x, c in counts.items()) / trials}


# ---------------------------------------------------------------------
#  8. FINITE STATE MACHINE   (state, event) -> next state
# ---------------------------------------------------------------------
FSM_STATES = ["Idle", "Login", "Access Granted", "Access Denied", "Navigating", "Monitoring", "Exit"]
FSM = {
    "Idle": {"sign_in": "Login"},
    "Login": {"access_granted": "Access Granted", "access_denied": "Access Denied", "leave": "Exit"},
    "Access Granted": {"access_granted": "Access Granted", "access_denied": "Access Denied",
                       "navigate": "Navigating", "monitor": "Monitoring", "leave": "Exit"},
    "Access Denied": {"access_granted": "Access Granted", "access_denied": "Access Denied", "leave": "Exit"},
    "Navigating": {"arrive": "Access Granted", "access_granted": "Access Granted",
                   "access_denied": "Access Denied", "leave": "Exit"},
    "Monitoring": {"stop": "Access Granted", "access_granted": "Access Granted",
                   "access_denied": "Access Denied", "leave": "Exit"},
    "Exit": {"restart": "Login"},
}

# =====================================================================
#  PART 2 - FLASK (the page + the API)
#  The whole website is ONE file: templates/index.html (HTML + CSS + JS).
# =====================================================================
app = Flask(__name__)
app.secret_key = "change-this-secret-key"
app.json.sort_keys = False
ADMIN_USER = "admin"
ADMIN_HASH = sha256("admin123")      # only the hash is kept in the code, not the password
load_data()


def login_required(role=None):
    def deco(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "role" not in session:
                return jsonify(error="Please sign in again."), 401
            if role and session["role"] != role:
                return jsonify(error="Admins only."), 403
            return view(*args, **kwargs)
        return wrapper
    return deco



def fsm_fire(event):
    """Move the signed-in person's state machine. Returns True if the event was allowed in this state."""
    state = session.get("fsm", "Idle")
    nxt = FSM.get(state, {}).get(event)
    if nxt is None:
        return False
    session["fsm"] = nxt
    session["fsm_hist"] = (session.get("fsm_hist", []) + [f"{state} -> {nxt}"])[-8:]
    return True


def fsm_start():
    session["fsm"], session["fsm_hist"] = "Idle", []
    fsm_fire("sign_in")


@app.before_request
def drop_removed_user():
    """If an admin removed this user, sign them out."""
    if session.get("role") == "user" and session.get("me") not in user_ids:
        session.clear()


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------- login
@app.get("/api/session")
def api_session():
    return jsonify(role=session.get("role"), me=session.get("me"))


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    u, p = str(data.get("username", "")).strip(), str(data.get("password", ""))
    if u.lower() == ADMIN_USER and hmac.compare_digest(sha256(p), ADMIN_HASH):
        session.clear()
        session.update(role="admin", me=None)
        fsm_start()
        return jsonify(role="admin", me=None)
    name = next((n for n in user_ids if n.lower() == u.lower()), None)
    if name and hmac.compare_digest(sha256(p.strip()), sha256(user_ids[name])):   # compare hashes, not plain text
        session.clear()
        session.update(role="user", me=name)
        fsm_start()
        return jsonify(role="user", me=name)
    return jsonify(error="Wrong username or password."), 401


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


# ---------------------------------------------------------------- the data the page draws
@app.get("/api/state")
@login_required()
def api_state():
    """Admins get everything. A user only gets other people's ID numbers hidden (null)."""
    admin = session["role"] == "admin"
    me = session.get("me")
    state = export_data()
    if not admin:
        for n, u in state["users"].items():
            if n != me:
                u["id"] = None
        state["log"] = []
        info = user_info(me)
        state["mine"] = {f: check_access(me, info["id"], f)["allowed"] for f in facilities}
    return jsonify(state)


# ---------------------------------------------------------------- everyone
@app.post("/api/check")
@login_required()
def api_check():
    d = request.get_json(silent=True) or {}
    facility = d.get("facility")
    if facility not in facilities:
        return jsonify(error="Invalid facility."), 400
    if session["role"] == "admin" and d.get("user") == "__o":          # "Someone not registered"
        name = str(d.get("other_name", "")).strip() or "Unregistered person"
        try:
            user_id = int(d.get("other_id"))
        except (TypeError, ValueError):
            return jsonify(error="Enter a number for the ID."), 400
    else:
        name = session["me"] if session["role"] == "user" else str(d.get("user", ""))
        if name not in user_ids:
            return jsonify(error="Unknown user."), 400
        user_id = user_ids[name]
    result = check_access(name, user_id, facility)
    access_log.insert(0, {"n": name, "f": facility, "ok": result["allowed"],
                          "t": datetime.now().strftime("%I:%M:%S %p")})
    del access_log[50:]
    save_data()
    fsm_fire("access_granted" if result["allowed"] else "access_denied")
    return jsonify(result)


@app.post("/api/calc")
@login_required()
def api_calc():
    d = request.get_json(silent=True) or {}
    try:
        a, b = int(d.get("a")), int(d.get("b"))
        if a == 0 or b == 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Enter two non-zero numbers."), 400
    g = gcd(a, b)
    return jsonify(a=a, b=b, gcd=g, lcm=abs(a * b) // g, mod=a % b)


@app.get("/api/proof")
@login_required()
def api_proof():
    cases, bad = proof_check()
    return jsonify(cases=cases, violations=bad)


# ---------------------------------------------------------------- admin only
@app.post("/api/users/save")
@login_required("admin")
def api_users_save():
    d = request.get_json(silent=True) or {}
    ok, message = add_user(str(d.get("name", "")), d.get("id"), d.get("type"),
                           bool(d.get("authorized")), bool(d.get("restricted")),
                           original=str(d.get("original", "")))
    if ok:
        save_data()
    return jsonify(ok=ok, message=message), (200 if ok else 400)


@app.post("/api/users/delete")
@login_required("admin")
def api_users_delete():
    name = str((request.get_json(silent=True) or {}).get("name", ""))
    if name in user_ids:
        remove_user(name)
        save_data()
    return jsonify(ok=True)


@app.post("/api/relations/toggle")
@login_required("admin")
def api_toggle():
    key = str((request.get_json(silent=True) or {}).get("key", ""))
    if "|" in key:
        toggle_relation(*key.split("|", 1))
        save_data()
    return jsonify(ok=True)


@app.post("/api/even")
@login_required("admin")
def api_even():
    settings["even_rule"] = bool((request.get_json(silent=True) or {}).get("even"))
    save_data()
    return jsonify(ok=True)


@app.post("/api/log/clear")
@login_required("admin")
def api_log_clear():
    access_log.clear()
    save_data()
    return jsonify(ok=True)


@app.get("/api/backup/export")
@login_required("admin")
def api_export():
    return jsonify(export_data())


@app.post("/api/backup/import")
@login_required("admin")
def api_import():
    try:
        import_data(request.get_json(silent=True))
    except (ValueError, TypeError, KeyError, AttributeError):
        return jsonify(error="That text is not valid backup data."), 400
    save_data()
    return jsonify(ok=True)


@app.post("/api/backup/reset")
@login_required("admin")
def api_reset():
    import_data(DEFAULT_DATA)
    save_data()
    return jsonify(ok=True)


# ---------------------------------------------------------------- final project features
@app.post("/api/crypto/caesar")
@login_required()
def api_caesar():
    d = request.get_json(silent=True) or {}
    try:
        k = int(d.get("k"))
    except (TypeError, ValueError):
        return jsonify(error="The key k must be a whole number."), 400
    text = str(d.get("text", ""))[:200]
    out, steps = caesar(text, k, decrypt=d.get("mode") == "decrypt")
    return jsonify(result=out, steps=steps, k_mod=k % 26)


@app.post("/api/crypto/hash")
@login_required()
def api_hash():
    text = str((request.get_json(silent=True) or {}).get("text", ""))[:200]
    return jsonify(hash=sha256(text), bits=len(sha256(text)) * 4)


@app.get("/api/crypto/credentials")
@login_required()
def api_credentials():
    names = list(user_ids) if session["role"] == "admin" else [session["me"]]
    return jsonify(rows=[{"name": n, "hash": sha256(user_ids[n])[:24]} for n in names])


@app.post("/api/algo/sort")
@login_required()
def api_sort():
    d = request.get_json(silent=True) or {}
    by, algo = d.get("by"), d.get("algo")
    if by not in ("name", "type", "id") or algo not in ("merge", "bubble"):
        return jsonify(error="Invalid choice."), 400
    if by == "id" and session["role"] != "admin":
        return jsonify(error="Only admins can sort by ID number."), 403
    key = {"name": lambda r: r["name"].lower(), "type": lambda r: (r["type"], r["name"].lower()), "id": lambda r: r["id"]}[by]
    rows, count = (merge_sort if algo == "merge" else bubble_sort)(user_rows(), key)
    admin = session["role"] == "admin"
    return jsonify(rows=[{"name": r["name"], "type": r["type"], "id": r["id"] if admin else None} for r in rows],
                   comparisons=count, n=len(rows))


@app.post("/api/algo/search")
@login_required()
def api_search():
    d = request.get_json(silent=True) or {}
    target, method = str(d.get("query", "")).strip().lower(), d.get("method")
    if not target or method not in ("linear", "binary"):
        return jsonify(error="Type a name to search for."), 400
    names = sorted(user_ids, key=str.lower)                  # binary search needs a sorted list
    pos, steps = (linear_search if method == "linear" else binary_search)(names, target)
    return jsonify(found=pos >= 0, name=names[pos] if pos >= 0 else None, steps=steps, n=len(names))


@app.get("/api/graph")
@login_required()
def api_graph():
    return jsonify(graph_info())


@app.post("/api/graph/route")
@login_required()
def api_route():
    d = request.get_json(silent=True) or {}
    a, b = d.get("start"), d.get("end")
    if a not in CAMPUS or b not in CAMPUS:
        return jsonify(error="Pick two places."), 400
    fastest, dist = shortest_route(CAMPUS, a, b)
    routes = all_routes(CAMPUS, a, b)
    return jsonify(shortest=fastest, distance=dist,
                   routes=[{"path": r, "length": route_length(CAMPUS, r)} for r in sorted(routes, key=lambda r: route_length(CAMPUS, r))])


@app.get("/api/tree")
@login_required()
def api_tree():
    return jsonify(tree_info(str(request.args.get("find", ""))))


@app.post("/api/prob")
@login_required()
def api_prob():
    d = request.get_json(silent=True) or {}
    if d.get("facility") not in facilities:
        return jsonify(error="Invalid facility."), 400
    try:
        return jsonify(probability_lab(d["facility"], int(d.get("k")), int(d.get("trials"))))
    except (TypeError, ValueError) as e:
        return jsonify(error=str(e) if str(e) and "invalid literal" not in str(e) else "Enter whole numbers."), 400


@app.get("/api/fsm")
@login_required()
def api_fsm():
    state = session.get("fsm", "Idle")
    return jsonify(state=state, events=FSM.get(state, {}), history=session.get("fsm_hist", []),
                   states=FSM_STATES, table=[[s, e, n] for s, ev in FSM.items() for e, n in ev.items()])


@app.post("/api/fsm/event")
@login_required()
def api_fsm_event():
    event = str((request.get_json(silent=True) or {}).get("event", ""))
    if not fsm_fire(event):
        return jsonify(error=f'"{event}" is not allowed in state {session.get("fsm", "Idle")}.'), 400
    return jsonify(ok=True)



if __name__ == "__main__":
    app.run(debug=True)
