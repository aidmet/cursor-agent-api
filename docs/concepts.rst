Concepts
========

Ideas behind **cursor-agent-sdk**—how to think before you read the API list. Hands-on steps:
:doc:`quickstart`.

The API vs this library
-----------------------

**Anchor:** Cursor runs cloud work **on their servers**; this SDK only **sends HTTP requests** from your machine.

Cursor exposes a hosted **Cursor Cloud Agents API** (`Cursor Cloud Agents API docs
<https://cursor.com/docs/cloud-agent/api/endpoints>`__). “Cloud agents” are remote jobs tied to
GitHub repos or PRs.

**cursor-agent-sdk** packages those calls in Python. It does **not** embed Cursor’s IDE, run models
locally, or guarantee PR outcomes—only what the API returns.

**What this is NOT**

* A replacement for the official HTTP docs (behaviour and limits live there).
* A way to drive the **desktop Cursor app**; it is **dashboard-style Cloud Agents**, via key + HTTP.

Authentication
--------------

**Anchor:** Your **Cloud Agents API key** is the credential; the client attaches it to every
request (Basic auth: key as username, empty password).

Get the key under Dashboard → **Cloud Agents**. Treat it like a password: env vars or a secret
manager, not a committed file.

**What this is NOT**

* The same key family as “any Cursor login” by assumption—use the key type the dashboard labels for
  Cloud Agents / this API.

Client = one front door to the HTTP API
---------------------------------------

**Anchor:** A **client** is the long-lived object that knows **base URL**, **timeouts**, and **who
you are** (the key).

Use **one** :class:`SyncClient` or :class:`AsyncClient` per app or process. Reuse it; do not spin a
new client per call. :class:`CursorClient` is the same as :class:`SyncClient`.

**What this is NOT**

* A “session” with a single cloud agent—agents are separate handles (below).

Agent = local bookmark for one remote run
------------------------------------------

**Anchor:** An **Agent** (or **AsyncAgent**) is a **Python object in your process** that remembers
**where** work targets GitHub (**repo** + **ref**, or **pr_url**) and, after you start it, **which**
remote run you are talking to (**id**).

It is **not** the worker process on Cursor’s side—it is your **handle** to that run.

.. code-block:: python

   agent = client.new_agent(
       repo="https://github.com/org/repo",
       ref="main",
   )
   # agent knows "where" — not yet "which run"

After :meth:`Agent.create`, the handle stores the returned **id**. :meth:`Agent.follow_up` sends
more text to **that same** id. :meth:`Agent.attach` sets **id** when you already know it (e.g. after
a restart) and skips a new **create** on that handle.

**What this is NOT**

* A second **create** on the same handle for “another task”—that starts a conflicting story. New
  independent run → **new** ``new_agent(...)`` (or a new client + agent pattern you choose).

Lifecycle in three beats
-------------------------

**Anchor:** **Pick a repo** → **start one run** → **add prompts to that run**.

.. code-block:: python

   agent = client.new_agent(repo="https://github.com/org/repo", ref="main")
   agent.create("Implement feature X.")       # first message — creates remote run, stores id
   agent.follow_up("Add tests.")              # same run
   agent.follow_up("Open a PR when ready.")  # still same run

Optional extras (model, branch/PR targets, webhooks, images) belong on **create**, not on routine
**follow_up**—follow-ups are mostly “more text” (and optional images) on the same run.

**What this is NOT**

* **create** repeated on the same handle for every message—that would fight the model above. First
  instruction **create**; later ones **follow_up**.

Sync vs async
-------------

**Anchor:** Same API shape; **sync** blocks until each call returns, **async** uses ``await`` and
fits ``asyncio`` apps.

* Scripts and notebooks → :class:`SyncClient` / :class:`Agent`.
* Servers or async pipelines → :class:`AsyncClient` / :class:`AsyncAgent`.

**What this is NOT**

* Async is not “stronger”—only choose it when your program is already async.

Helpers vs raw client methods
-----------------------------

**Anchor:** **Agent** methods keep **id** and **source** consistent; **client** methods like
``launch_agent`` / ``followup`` expect you to pass **agent_id** yourself.

Prefer **Agent** until you need something only the low-level calls expose.

**What this is NOT**

* Two different backends—same service, different amount of bookkeeping in Python.

When things fail
----------------

**Anchor:** HTTP errors become :exc:`cursor_agent.CursorAPIError` so you can log ``status_code`` and
inspect ``response`` without guessing strings.
