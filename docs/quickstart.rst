Quickstart
==========

Install
-------

Install from `PyPI <https://pypi.org/project/cursor-agent-sdk/>`__ (recommended)::

   pip install cursor-agent-sdk

To work on the SDK from a git clone, use an editable install::

   pip install -e .

Python **3.10+** is required.

Authentication
--------------

Create an API key in the Cursor Dashboard under **Cloud Agents**.

The API expects **Basic authentication**: username = API key, password empty (same as
``curl -u 'YOUR_KEY': ...``).

Set an environment variable for local runs::

   set CURSOR_API_KEY=your-key-here

Minimal sync example
--------------------

.. code-block:: python

   import os
   from cursor_agent import SyncClient

   with SyncClient(os.environ["CURSOR_API_KEY"]) as client:
       agent = client.new_agent(
           repo="https://github.com/octocat/Hello-World",
           ref="main",
       )
       out = agent.create("Add a one-line note to README.md.")
       print(out)
       agent.follow_up("Keep the tone neutral.")

Minimal async example
---------------------

.. code-block:: python

   import asyncio
   import os
   from cursor_agent import AsyncClient

   async def main():
       async with AsyncClient(os.environ["CURSOR_API_KEY"]) as client:
           agent = client.new_agent(
               repo="https://github.com/octocat/Hello-World",
               ref="main",
           )
           await agent.create("Update the README.")
           await agent.follow_up("Be concise.")

   asyncio.run(main())

For contributors: build these docs locally
-------------------------------------------

If you are editing the Sphinx sources in the repository, regenerate HTML like this (from the repo root)::

   cd docs
   make.bat html

On Linux or macOS, use ``make html`` instead of ``make.bat html``. Then open ``_build/html/index.html`` in a browser.
