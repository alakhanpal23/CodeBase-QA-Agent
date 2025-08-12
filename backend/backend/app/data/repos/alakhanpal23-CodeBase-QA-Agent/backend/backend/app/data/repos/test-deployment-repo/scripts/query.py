#!/usr/bin/env python3
"""
CLI script for querying codebases.
"""

import asyncio
import sys
import os
from pathlib import Path
import click
import httpx
import json

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.schemas import QueryRequest


@click.command()
@click.option('--repo', required=True, help='Repository ID (e.g., org/repo)')
@click.option('--q', 'question', required=True, help='Question to ask about the codebase')
@click.option('--k', default=6, help='Number of chunks to retrieve (default: 6)')
@click.option('--api-url', default='http://localhost:8000', help='API server URL')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
def query(question, repo, k, api_url, verbose, json_output):
    """Query a codebase with a natural language question."""
    
    # Create request
    request = QueryRequest(
        question=question,
        repo_ids=[repo],
        k=k
    )
    
    if verbose:
        click.echo(f"Question: {question}")
        click.echo(f"Repository: {repo}")
        click.echo(f"Chunks to retrieve: {k}")
        click.echo(f"API URL: {api_url}")
        click.echo()
    
    # Send request to API
    asyncio.run(_query_codebase(request, api_url, verbose, json_output))


async def _query_codebase(request: QueryRequest, api_url: str, verbose: bool, json_output: bool):
    """Send query request to the API."""
    try:
        async with httpx.AsyncClient() as client:
            if verbose:
                click.echo("Sending query request...")
            
            response = await client.post(
                f"{api_url}/query",
                json=request.dict(),
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if json_output:
                    click.echo(json.dumps(result, indent=2))
                else:
                    _display_result(result)
                    
            else:
                click.echo(f"❌ Query failed: {response.status_code}")
                click.echo(response.text)
                sys.exit(1)
                
    except httpx.ConnectError:
        click.echo(f"❌ Failed to connect to API server at {api_url}")
        click.echo("Make sure the server is running with: uvicorn backend.app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


def _display_result(result):
    """Display query result in a user-friendly format."""
    click.echo("🤖 Answer:")
    click.echo(result['answer'])
    click.echo()
    
    if result['citations']:
        click.echo("📚 Citations:")
        for i, citation in enumerate(result['citations'], 1):
            click.echo(f"  {i}. {citation['path']}:{citation['start']}-{citation['end']} (score: {citation['score']:.3f})")
            
            # Show a preview of the code if available
            if citation.get('content'):
                content = citation['content']
                if len(content) > 100:
                    content = content[:100] + "..."
                click.echo(f"     {content}")
                click.echo()
    else:
        click.echo("📚 No citations found")
    
    click.echo(f"⏱️  Latency: {result['latency_ms']}ms")


if __name__ == '__main__':
    query()
