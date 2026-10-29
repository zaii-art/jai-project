HOW TO RUN
  1. pip install flask
  2. python app.py
  3. open http://127.0.0.1:5000

LOGINS
  Admin : admin / admin123
  User  : your name + your ID number (example: Ck / 2024102)

MIDTERM FEATURES
  Sets, relations, access matrix, Boolean access rule, number theory (ID mod 2, GCD, LCM), logic proof, backup.

MENU (kept short on purpose)
  Check access | Users (admin) | Math & Logic | Tools | Campus | Admin (admin)
  Tap a group, then use the small tabs under the title to switch pages.
    Math & Logic : Sets, Relations, Number theory, Logic proof
    Tools        : Sort & search, Cryptography, Probability
    Campus       : Map, Tree, State machine

FINAL PROJECT FEATURES
  Cryptography   : Caesar cipher E(x)=(x+k) mod 26, SHA-256 hashing (login now compares hashes)
  Algorithms     : merge sort (recursive) and bubble sort with comparison counts, linear and binary search
  Campus map     : graph of locations, Dijkstra shortest route, BFS connectivity, recursive all-routes, adjacency matrix
  Trees          : campus tree, recursive preorder / postorder, height, leaves, recursive path finder
  Probability    : counting C(n,k) and P(n,k), probability, random variable X (hypergeometric), E[X], Var(X), simulation
  State machine  : Idle, Login, Access Granted, Access Denied, Navigating, Monitoring, Exit

All logic is in app.py (Part 1 = midterm, Part 1B = final project, Part 2 = Flask). The page only draws results.
