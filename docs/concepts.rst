Concepts
========

This page names the main ideas behind **cursor-agent-sdk** and the
`Cursor Cloud Agents API <https://cursor.com/docs/cloud-agent/api/endpoints>`__. For install and
copy-paste examples, see :doc:`quickstart`.

Remote service vs this library
-------------------------------

The **Cursor Cloud Agents API** is Cursor’s hosted HTTP API (``api.cursor.com``, paths under
``/v0``). It creates **cloud agents** that work against **GitHub** repositories or pull requests.

**cursor-agent-sdk** is a thin Python wrapper: it does not run the agent itself—it sends the same
requests you could send with ``curl`` or ``httpx``, with typed methods and a small **agent**
abstraction so you do not have to track ids and sources by hand.

Authentication
----------------

Every request must include your **Cloud Agents API key**. The service expects **HTTP Basic** auth:
**username** = the key, **password** empty. Both :class:`SyncClient` and :class:`AsyncClient` apply
that for you when you pass the key to the constructor.

Keys are issued from the Cursor Dashboard (**Cloud Agents**). They are **secrets**: load them from
environment variables or a secret store, not from source control.

Client
------

A **client** (:class:`SyncClient` or :class:`AsyncClient`) represents:

* The **base URL** (default ``https://api.cursor.com``).
* **Connection settings** (timeouts, and optionally a custom :class:`httpx.Client` /
  :class:`httpx.AsyncClient` via ``from_httpx_client``).
* **Credentials** used for every call.

Create **one client** per logical app or long-lived process. It is cheap to reuse; you typically do
**not** create a new client per HTTP call.

:class:`CursorClient` is an alias for :class:`SyncClient`.

Agent handle
------------

An **agent** (:class:`Agent` or :class:`AsyncAgent`) is **not** the remote worker by itself—it is a
**handle** in your process that remembers:

* **Source** — a GitHub **repository URL** and optional **ref** (branch/tag/commit), *or* a
  **pull request URL** (``pr_url``). Set when you call :meth:`SyncClient.new_agent`.
* **Identity** — after a successful :meth:`Agent.create`, the **cloud agent id** returned by the API
  (e.g. ``bc_…``). Later :meth:`Agent.follow_up` calls use that id.

So: **new_agent** chooses *where* work happens; **create** starts the remote run and stores *which*
run; **follow_up** sends more instructions to **that same** run.

If you already have an id from a previous session, :meth:`Agent.attach` sets the handle to that id
and clears source fields—use **follow_up** / **refresh** only, not another **create** on the same
handle unless you use a **new** :meth:`SyncClient.new_agent` for a separate run.

Lifecycle (high level)
----------------------

#. **Bind source** — ``client.new_agent(repo=…, ref=…)`` or ``new_agent(pr_url=…)``.
#. **Start work** — ``agent.create(prompt, …)`` once per handle (``POST /v0/agents``).
#. **Continue** — ``agent.follow_up(prompt, …)`` (``POST /v0/agents/{id}/followup``).
#. **Observe** — ``agent.refresh``, ``agent.conversation``, or webhooks if you configure them on
   **create** (see Cursor’s API docs).

Launch-only options—``model``, ``target``, ``webhook``, ``images`` on **create**—do not apply to
**follow_up**, which only takes prompt text and optional images.

Sync vs async
-------------

* **SyncClient** / **Agent** — blocking calls; simplest for scripts and notebooks.
* **AsyncClient** / **AsyncAgent** — ``await`` each network call; use inside ``asyncio`` when your
  app is already async (e.g. web servers, concurrent tasks).

The HTTP surface is the same; only the calling style changes.

Low-level vs high-level
-----------------------

* **High-level** — :meth:`Agent.create` and :meth:`Agent.follow_up` keep **id** and **source**
  consistent and match the mental model above.
* **Low-level** — :meth:`SyncClient.launch_agent`, :meth:`SyncClient.followup`, etc. map directly to
  routes; you pass **agent_id** yourself. Use when you need full control or are not using the
  :class:`Agent` helper.

Errors
------

Failed HTTP responses raise :exc:`cursor_agent.CursorAPIError`, with ``status_code`` and often the
underlying :class:`httpx.Response` attached for logging or debugging.
