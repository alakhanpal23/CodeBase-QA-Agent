#!/usr/bin/env python3
"""
CLI script for ingesting GitHub repositories.
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

from app.core.schemas import IngestRequest


@click.command()
@click.option('--url', required=True, help='GitHub repository URL')
@click.option('--repo', required=True, help='Repository ID (e.g., org/repo)')
@click.option('--branch', default='main', help='Branch to clone (default: main)')
@click.option('--include', default='**/*.py,**/*.ts,**/*.js', help='File patterns to include')
@click.option('--exclude', default='.git/**,node_modules/**,dist/**,build/**,.venv/**', help='File patterns to exclude')
@click.option('--api-url', default='http://localhost:8000', help='API server URL')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def ingest_repo(url, repo, branch, include, exclude, api_url, verbose):
    """Ingest a GitHub repository into the codebase QA system."""
    
    # Parse glob patterns
    include_globs = [p.strip() for p in include.split(',') if p.strip()]
    exclude_globs = [p.strip() for p in exclude.split(',') if p.strip()]
    
    # Create request
    request = IngestRequest(
        source="github",
        url=url,
        branch=branch,
        repo_id=repo,
        include_globs=include_globs,
        exclude_globs=exclude_globs
    )
    
    if verbose:
        click.echo(f"Repository URL: {url}")
        click.echo(f"Repository ID: {repo}")
        click.echo(f"Branch: {branch}")
        click.echo(f"Include patterns: {include_globs}")
        click.echo(f"Exclude patterns: {exclude_globs}")
        click.echo(f"API URL: {api_url}")
        click.echo()
    
    # Send request to API
    asyncio.run(_ingest_repository(request, api_url, verbose))


async def _ingest_repository(request: IngestRequest, api_url: str, verbose: bool):
    """Send ingestion request to the API."""
    try:
        async with httpx.AsyncClient() as client:
            if verbose:
                click.echo("Sending ingestion request...")
            
            response = await client.post(
                f"{api_url}/ingest",
                json=request.dict(),
                timeout=300.0  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                click.echo("✅ Repository ingested successfully!")
                click.echo(f"Files processed: {result['files_processed']}")
                click.echo(f"Chunks stored: {result['chunks_stored']}")
                click.echo(f"Elapsed time: {result['elapsed_time']:.2f}s")
                
                if result.get('commit_sha'):
                    click.echo(f"Commit SHA: {result['commit_sha']}")
                    
            else:
                click.echo(f"❌ Ingestion failed: {response.status_code}")
                click.echo(response.text)
                sys.exit(1)
                
    except httpx.ConnectError:
        click.echo(f"❌ Failed to connect to API server at {api_url}")
        click.echo("Make sure the server is running with: uvicorn backend.app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    ingest_repo()
