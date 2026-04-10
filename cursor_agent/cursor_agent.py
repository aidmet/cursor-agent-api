from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.cursor.com"


class CursorAPIError(Exception):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


def _raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = response.text
        try:
            body = response.json()
            if isinstance(body, dict) and "message" in body:
                detail = str(body["message"])
            elif isinstance(body, dict) and "error" in body:
                detail = str(body["error"])
        except ValueError:
            pass
        raise CursorAPIError(
            f"{response.status_code} {response.reason_phrase}: {detail}",
            status_code=response.status_code,
            response=response,
        ) from e


def _normalize_agent_source(
    repo: str | None,
    ref: str | None,
    pr_url: str | None,
) -> tuple[str | None, str | None, str | None]:
    if repo is not None:
        r = repo.strip()
        if not r:
            raise ValueError("repo must be a non-empty string when provided")
        out_repo: str | None = r
    else:
        out_repo = None

    if pr_url is not None:
        p = pr_url.strip()
        if not p:
            raise ValueError("pr_url must be a non-empty string when provided")
        out_pr: str | None = p
    else:
        out_pr = None

    if ref is not None:
        rf = ref.strip()
        out_ref: str | None = rf if rf else None
    else:
        out_ref = None

    return out_repo, out_ref, out_pr


def _launch_agent_json_body(
    *,
    prompt: str,
    repository: str | None = None,
    ref: str | None = None,
    pr_url: str | None = None,
    model: str | None = None,
    target: dict[str, Any] | None = None,
    webhook: dict[str, Any] | None = None,
    images: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if pr_url is None and repository is None:
        raise ValueError("launch_agent() requires either repository or pr_url")

    prompt_body: dict[str, Any] = {"text": prompt}
    if images is not None:
        prompt_body["images"] = images

    source: dict[str, Any] = {}
    if pr_url is not None:
        source["prUrl"] = pr_url
    else:
        source["repository"] = repository
    if ref is not None:
        source["ref"] = ref

    body: dict[str, Any] = {"prompt": prompt_body, "source": source}
    if model is not None:
        body["model"] = model
    if target is not None:
        body["target"] = target
    if webhook is not None:
        body["webhook"] = webhook

    return body


class SyncClient:
    """
    Synchronous client for the Cursor Cloud Agents API.

    See https://cursor.com/docs/cloud-agent/api/endpoints

    Authentication uses HTTP Basic auth: API key as username, empty password
    (equivalent to ``curl -u YOUR_API_KEY: ...``).
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
    ) -> None:
        self._owns_client = True
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            auth=(api_key, ""),
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    @classmethod
    def from_httpx_client(cls, client: httpx.Client) -> SyncClient:
        """Wrap an existing :class:`httpx.Client` (you manage base URL and auth)."""
        obj = cls.__new__(cls)
        obj._owns_client = False
        obj._client = client
        return obj

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> SyncClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _json(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        r = self._client.request(method, path, json=json, params=params)
        _raise_for_status(r)
        if not r.content:
            return {}
        return r.json()

    def new_agent(
        self,
        repo: str | None = None,
        *,
        ref: str | None = None,
        pr_url: str | None = None,
    ) -> Agent:
        """
        Create an :class:`Agent` bound to a GitHub repo or PR.

        Pass ``repo`` (repository URL) or ``pr_url`` — same rules as ``POST /v0/agents`` ``source``.
        Use :meth:`Agent.create` for the first prompt, then :meth:`Agent.follow_up` for more.
        """
        if repo is None and pr_url is None:
            raise ValueError("new_agent() requires either repo or pr_url")
        return Agent(self, repo=repo, ref=ref, pr_url=pr_url)

    def me(self) -> dict[str, Any]:
        """``GET /v0/me`` — API key metadata."""
        return self._json("GET", "/v0/me")

    def list_models(self) -> dict[str, Any]:
        """``GET /v0/models`` — models available for agents."""
        return self._json("GET", "/v0/models")

    def list_repositories(self) -> dict[str, Any]:
        """``GET /v0/repositories`` — GitHub repositories accessible to the key."""
        return self._json("GET", "/v0/repositories")

    def list_agents(self) -> dict[str, Any]:
        """``GET /v0/agents`` — list cloud agents."""
        return self._json("GET", "/v0/agents")

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        """``GET /v0/agents/{id}`` — agent status and details."""
        return self._json("GET", f"/v0/agents/{agent_id}")

    def get_conversation(self, agent_id: str) -> dict[str, Any]:
        """``GET /v0/agents/{id}/conversation``."""
        return self._json("GET", f"/v0/agents/{agent_id}/conversation")

    def launch_agent(
        self,
        *,
        prompt: str,
        repository: str | None = None,
        ref: str | None = None,
        pr_url: str | None = None,
        model: str | None = None,
        target: dict[str, Any] | None = None,
        webhook: dict[str, Any] | None = None,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        ``POST /v0/agents`` — start a new agent.

        Provide either ``repository`` (and optionally ``ref``) or ``pr_url`` for the source.
        """
        body = _launch_agent_json_body(
            prompt=prompt,
            repository=repository,
            ref=ref,
            pr_url=pr_url,
            model=model,
            target=target,
            webhook=webhook,
            images=images,
        )
        return self._json("POST", "/v0/agents", json=body)

    def followup(
        self,
        agent_id: str,
        *,
        prompt: str,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """``POST /v0/agents/{id}/followup``."""
        p: dict[str, Any] = {"text": prompt}
        if images is not None:
            p["images"] = images
        return self._json("POST", f"/v0/agents/{agent_id}/followup", json={"prompt": p})

    def stop_agent(self, agent_id: str) -> dict[str, Any]:
        """``POST /v0/agents/{id}/stop``."""
        return self._json("POST", f"/v0/agents/{agent_id}/stop")

    def delete_agent(self, agent_id: str) -> dict[str, Any]:
        """``DELETE /v0/agents/{id}``."""
        return self._json("DELETE", f"/v0/agents/{agent_id}")


class AsyncClient:
    """
    Async client for the Cursor Cloud Agents API (:class:`httpx.AsyncClient`).

    Use ``async with AsyncClient(...)`` or call :meth:`aclose` when done.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
    ) -> None:
        self._owns_client = True
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            auth=(api_key, ""),
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    @classmethod
    def from_httpx_client(cls, client: httpx.AsyncClient) -> AsyncClient:
        """Wrap an existing :class:`httpx.AsyncClient` (you manage base URL and auth)."""
        obj = cls.__new__(cls)
        obj._owns_client = False
        obj._client = client
        return obj

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def _json(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        r = await self._client.request(method, path, json=json, params=params)
        _raise_for_status(r)
        if not r.content:
            return {}
        return r.json()

    def new_agent(
        self,
        repo: str | None = None,
        *,
        ref: str | None = None,
        pr_url: str | None = None,
    ) -> AsyncAgent:
        if repo is None and pr_url is None:
            raise ValueError("new_agent() requires either repo or pr_url")
        return AsyncAgent(self, repo=repo, ref=ref, pr_url=pr_url)

    async def me(self) -> dict[str, Any]:
        return await self._json("GET", "/v0/me")

    async def list_models(self) -> dict[str, Any]:
        return await self._json("GET", "/v0/models")

    async def list_repositories(self) -> dict[str, Any]:
        return await self._json("GET", "/v0/repositories")

    async def list_agents(self) -> dict[str, Any]:
        return await self._json("GET", "/v0/agents")

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        return await self._json("GET", f"/v0/agents/{agent_id}")

    async def get_conversation(self, agent_id: str) -> dict[str, Any]:
        return await self._json("GET", f"/v0/agents/{agent_id}/conversation")

    async def launch_agent(
        self,
        *,
        prompt: str,
        repository: str | None = None,
        ref: str | None = None,
        pr_url: str | None = None,
        model: str | None = None,
        target: dict[str, Any] | None = None,
        webhook: dict[str, Any] | None = None,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        body = _launch_agent_json_body(
            prompt=prompt,
            repository=repository,
            ref=ref,
            pr_url=pr_url,
            model=model,
            target=target,
            webhook=webhook,
            images=images,
        )
        return await self._json("POST", "/v0/agents", json=body)

    async def followup(
        self,
        agent_id: str,
        *,
        prompt: str,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        p: dict[str, Any] = {"text": prompt}
        if images is not None:
            p["images"] = images
        return await self._json(
            "POST", f"/v0/agents/{agent_id}/followup", json={"prompt": p}
        )

    async def stop_agent(self, agent_id: str) -> dict[str, Any]:
        return await self._json("POST", f"/v0/agents/{agent_id}/stop")

    async def delete_agent(self, agent_id: str) -> dict[str, Any]:
        return await self._json("DELETE", f"/v0/agents/{agent_id}")


class Agent:
    """
    One :class:`Agent` instance maps to one Cursor cloud agent (one id from the API).

    Use with :class:`SyncClient`. Call :meth:`create` once (``POST /v0/agents``), then
    :meth:`follow_up` for further prompts. Or :meth:`attach` and :meth:`follow_up` only.
    """

    def __init__(
        self,
        client: SyncClient,
        *,
        repo: str | None = None,
        ref: str | None = None,
        pr_url: str | None = None,
    ) -> None:
        self._client = client
        self._id: str | None = None
        self._repo, self._ref, self._pr_url = _normalize_agent_source(repo, ref, pr_url)

    @property
    def id(self) -> str | None:
        return self._id

    def create(
        self,
        prompt: str,
        *,
        model: str | None = None,
        target: dict[str, Any] | None = None,
        webhook: dict[str, Any] | None = None,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Create the cloud agent (``POST /v0/agents``).

        Requires ``repo`` / ``pr_url`` from :meth:`SyncClient.new_agent`. Call at most once per
        :class:`Agent` instance; for more prompts use :meth:`follow_up`.
        """
        if self._id is not None:
            raise RuntimeError(
                "This agent already has a cloud id: use follow_up() for more prompts, "
                "or use client.new_agent(...) for a separate agent."
            )
        if not self._repo and not self._pr_url:
            raise RuntimeError(
                "No repository context: create the agent with client.new_agent(repo=...) or "
                "new_agent(pr_url=...). If you only have an existing cloud id, use attach() and "
                "follow_up()."
            )
        data = self._client.launch_agent(
            prompt=prompt,
            repository=self._repo,
            ref=self._ref,
            pr_url=self._pr_url,
            model=model,
            target=target,
            webhook=webhook,
            images=images,
        )
        aid = data.get("id")
        if isinstance(aid, str):
            self._id = aid
        return data

    def follow_up(
        self,
        prompt: str,
        *,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """``POST /v0/agents/{id}/followup`` — send another prompt to the same cloud agent."""
        if not self._id:
            raise RuntimeError(
                "No cloud agent yet: call create() first (with repo from new_agent), "
                "or attach(agent_id)."
            )
        return self._client.followup(self._id, prompt=prompt, images=images)

    def refresh(self) -> dict[str, Any]:
        """``GET /v0/agents/{id}`` — latest status (requires :meth:`create` or :meth:`attach`)."""
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return self._client.get_agent(self._id)

    def conversation(self) -> dict[str, Any]:
        """``GET /v0/agents/{id}/conversation``."""
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return self._client.get_conversation(self._id)

    def stop(self) -> dict[str, Any]:
        """``POST /v0/agents/{id}/stop``."""
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return self._client.stop_agent(self._id)

    def delete(self) -> dict[str, Any]:
        """``DELETE /v0/agents/{id}``."""
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return self._client.delete_agent(self._id)

    def attach(self, agent_id: str) -> None:
        """Use an existing agent id (e.g. from a previous session) for follow-ups and status."""
        self._id = agent_id
        self._repo = None
        self._ref = None
        self._pr_url = None


class AsyncAgent:
    """
    Async counterpart to :class:`Agent` for use with :class:`AsyncClient`.

    Methods mirror :class:`Agent` but are async.
    """

    def __init__(
        self,
        client: AsyncClient,
        *,
        repo: str | None = None,
        ref: str | None = None,
        pr_url: str | None = None,
    ) -> None:
        self._client = client
        self._id: str | None = None
        self._repo, self._ref, self._pr_url = _normalize_agent_source(repo, ref, pr_url)

    @property
    def id(self) -> str | None:
        return self._id

    async def create(
        self,
        prompt: str,
        *,
        model: str | None = None,
        target: dict[str, Any] | None = None,
        webhook: dict[str, Any] | None = None,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if self._id is not None:
            raise RuntimeError(
                "This agent already has a cloud id: use follow_up() for more prompts, "
                "or use client.new_agent(...) for a separate agent."
            )
        if not self._repo and not self._pr_url:
            raise RuntimeError(
                "No repository context: create the agent with client.new_agent(repo=...) or "
                "new_agent(pr_url=...). If you only have an existing cloud id, use attach() and "
                "follow_up()."
            )
        data = await self._client.launch_agent(
            prompt=prompt,
            repository=self._repo,
            ref=self._ref,
            pr_url=self._pr_url,
            model=model,
            target=target,
            webhook=webhook,
            images=images,
        )
        aid = data.get("id")
        if isinstance(aid, str):
            self._id = aid
        return data

    async def follow_up(
        self,
        prompt: str,
        *,
        images: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not self._id:
            raise RuntimeError(
                "No cloud agent yet: call create() first (with repo from new_agent), "
                "or attach(agent_id)."
            )
        return await self._client.followup(self._id, prompt=prompt, images=images)

    async def refresh(self) -> dict[str, Any]:
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return await self._client.get_agent(self._id)

    async def conversation(self) -> dict[str, Any]:
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return await self._client.get_conversation(self._id)

    async def stop(self) -> dict[str, Any]:
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return await self._client.stop_agent(self._id)

    async def delete(self) -> dict[str, Any]:
        if not self._id:
            raise RuntimeError("No agent id: call create() or attach().")
        return await self._client.delete_agent(self._id)

    def attach(self, agent_id: str) -> None:
        self._id = agent_id
        self._repo = None
        self._ref = None
        self._pr_url = None


# Backward compatibility — :class:`CursorClient` was the original name for the sync client.
CursorClient = SyncClient
