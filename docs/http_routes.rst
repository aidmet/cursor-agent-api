HTTP routes
============

The client methods map to the **Cursor Cloud Agents API** base URL
``https://api.cursor.com`` (paths under ``/v0``). Async methods are identical but
must be ``await``\ ed.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Client method
     - HTTP
   * - :meth:`SyncClient.me` / :meth:`AsyncClient.me`
     - ``GET /v0/me``
   * - :meth:`SyncClient.list_models` / :meth:`AsyncClient.list_models`
     - ``GET /v0/models``
   * - :meth:`SyncClient.list_repositories` / :meth:`AsyncClient.list_repositories`
     - ``GET /v0/repositories``
   * - :meth:`SyncClient.list_agents` / :meth:`AsyncClient.list_agents`
     - ``GET /v0/agents``
   * - :meth:`SyncClient.get_agent` / :meth:`AsyncClient.get_agent`
     - ``GET /v0/agents/{id}``
   * - :meth:`SyncClient.get_conversation` / :meth:`AsyncClient.get_conversation`
     - ``GET /v0/agents/{id}/conversation``
   * - :meth:`SyncClient.launch_agent` / :meth:`AsyncClient.launch_agent`
     - ``POST /v0/agents``
   * - :meth:`SyncClient.followup` / :meth:`AsyncClient.followup`
     - ``POST /v0/agents/{id}/followup``
   * - :meth:`SyncClient.stop_agent` / :meth:`AsyncClient.stop_agent`
     - ``POST /v0/agents/{id}/stop``
   * - :meth:`SyncClient.delete_agent` / :meth:`AsyncClient.delete_agent`
     - ``DELETE /v0/agents/{id}``

High-level :meth:`Agent.create` and :meth:`Agent.follow_up` call ``launch_agent`` and ``followup``
respectively, while keeping the agent id on the handle.
