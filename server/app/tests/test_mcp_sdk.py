"""Protocol test using the standard Python MCP client, no external network."""
import asyncio
import importlib
import json

import httpx
import pytest
from fastapi import FastAPI


def test_sdk_store_audit_roundtrip(tmp_path, monkeypatch):
    pytest.importorskip('mcp')
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from app.core import config, audit
    monkeypatch.setenv('IVYEA_OPS_DATA_DIR', str(tmp_path))
    importlib.reload(config)
    from app.services import mcp_tokens, store_artifacts
    from app.routers import mcp_server
    importlib.reload(mcp_server)
    mcp_tokens.init_db()
    audit.init_db()
    token = mcp_tokens.issue('SDK', scopes=['read','write'])
    app = FastAPI()
    app.include_router(mcp_server.router, prefix='/api/mcp')
    snapshot = store_artifacts.import_snapshot({
        'store_id':'demo', 'platform':'emag', 'marketplace':'RO',
        'captured_at':'2026-10-28T02:00:00Z', 'source':'synthetic-test',
        'coverage':['demo'], 'limitations':['Not real store evidence'], 'data':{}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                headers={'Authorization':f"Bearer {token['token']}"}) as http:
            async with streamable_http_client('http://testserver/api/mcp', http_client=http) as (read, write, _):
                async with ClientSession(read, write) as client:
                    assert (await client.initialize()).serverInfo.name == 'ivyea-ops'
                    names = {t.name for t in (await client.list_tools()).tools}
                    assert {'ivyea_store_snapshot','ivyea_report_save','ivyea_report_read'} <= names
                    found = await client.call_tool('ivyea_store_snapshot', {'store_id':'demo'})
                    assert not found.isError
                    assert json.loads(found.content[0].text) == snapshot
                    saved = await client.call_tool('ivyea_report_save', {'store_id':'demo', 'snapshot_id':snapshot['snapshot_id'], 'title':'Audit', 'markdown':'Demo'})
                    assert not saved.isError
                    report = json.loads(saved.content[0].text)
                    readback = await client.call_tool('ivyea_report_read', {'report_id':report['report_id']})
                    assert not readback.isError
                    assert json.loads(readback.content[0].text) == report
                    missing = await client.call_tool('ivyea_store_snapshot', {'store_id':'missing'})
                    assert missing.isError
    asyncio.run(run())
