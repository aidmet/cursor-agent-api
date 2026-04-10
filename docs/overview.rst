Overview
========

What this SDK does
------------------

**cursor-agent-sdk** is `published on PyPI <https://pypi.org/project/cursor-agent-sdk/>`__ as the
package name ``cursor-agent-sdk``. It wraps the HTTP API at ``https://api.cursor.com/v0`` (the
`Cursor Cloud Agents API <https://cursor.com/docs/cloud-agent/api/endpoints>`__) so you can script
the same workflows you might otherwise drive from the Cursor Dashboard (Cloud Agents).

This package is **not** maintained by Cursor; it is a community wrapper.

For terminology and lifecycle in more detail, see :doc:`concepts`.

Clients and agents
------------------

* **SyncClient** / **AsyncClient** — One client per process (or logical app). Holds your API key
  (HTTP Basic: key as username, empty password) and issues raw requests.

* **Agent** / **AsyncAgent** — Returned by :meth:`SyncClient.new_agent` (or :meth:`AsyncClient.new_agent`).
  Remembers the GitHub **repo** (or **pr_url**) and, after :meth:`Agent.create`, the remote agent
  **id**. Use :meth:`Agent.follow_up` for more prompts on the *same* cloud agent.

* **CursorClient** — Alias for :class:`SyncClient` (backward compatibility).

Errors
------

HTTP failures raise :exc:`cursor_agent.CursorAPIError` with ``status_code`` and ``response`` set when
available.

Further reading
---------------

* `Cursor Cloud Agents API — endpoints <https://cursor.com/docs/cloud-agent/api/endpoints>`__
* `Cursor APIs overview <https://cursor.com/docs/api>`__
