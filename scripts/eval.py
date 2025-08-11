#!/usr/bin/env python3
"""
Evaluation script for testing retrieval precision on canned Q&A pairs.
"""

import asyncio
import sys
import json
from pathlib import Path
import click
import httpx
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.schemas import QueryRequest


@click.command()
@click.option('--repo', required=True, help='Repository ID to evaluate')
@click.option('--api-url', default='http://localhost:8000', help='API server URL')
@click.option('--output', default='eval_results.json', help='Output file for results')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def eval_qa(repo, api_url, output, verbose):
    """Evaluate the QA system on canned questions."""
    
    # Define test questions and expected patterns
    test_cases = [
        {
            "question": "Where is authentication implemented?",
            "expected_patterns": ["auth", "login", "authenticate", "jwt", "token"],
            "expected_files": ["auth", "login", "jwt", "middleware"]
        },
        {
            "question": "How is routing handled?",
            "expected_patterns": ["route", "router", "endpoint", "path"],
            "expected_files": ["route", "router", "main", "app"]
        },
        {
            "question": "Where are database models defined?",
            "expected_patterns": ["model", "database", "db", "schema"],
            "expected_files": ["model", "db", "schema", "database"]
        },
        {
            "question": "How is error handling implemented?",
            "expected_patterns": ["error", "exception", "try", "catch", "except"],
            "expected_files": ["error", "exception", "handler"]
        },
        {
            "question": "Where is configuration managed?",
            "expected_patterns": ["config", "settings", "env", "environment"],
            "expected_files": ["config", "settings", "env"]
        }
    ]
    
    if verbose:
        click.echo(f"Evaluating repository: {repo}")
        click.echo(f"API URL: {api_url}")
        click.echo(f"Output file: {output}")
        click.echo()
    
    # Run evaluation
    results = asyncio.run(_run_evaluation(test_cases, repo, api_url, verbose))
    
    # Save results
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    _print_summary(results)
    
    click.echo(f"\nResults saved to: {output}")


async def _run_evaluation(test_cases: List[Dict], repo: str, api_url: str, verbose: bool) -> Dict[str, Any]:
    """Run evaluation on test cases."""
    results = {
        "repo": repo,
        "api_url": api_url,
        "test_cases": [],
        "summary": {}
    }
    
    async with httpx.AsyncClient() as client:
        for i, test_case in enumerate(test_cases, 1):
            if verbose:
                click.echo(f"Testing case {i}/{len(test_cases)}: {test_case['question']}")
            
            case_result = await _evaluate_case(client, test_case, repo, api_url)
            results["test_cases"].append(case_result)
            
            if verbose:
                _print_case_result(case_result)
                click.echo()
    
    # Calculate summary statistics
    results["summary"] = _calculate_summary(results["test_cases"])
    
    return results


async def _evaluate_case(client: httpx.AsyncClient, test_case: Dict, repo: str, api_url: str) -> Dict[str, Any]:
    """Evaluate a single test case."""
    question = test_case["question"]
    expected_patterns = test_case["expected_patterns"]
    expected_files = test_case["expected_files"]
    
    # Send query
    try:
        response = await client.post(
            f"{api_url}/query",
            json={
                "question": question,
                "repo_ids": [repo],
                "k": 6
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Analyze results
            precision_at_k = _calculate_precision_at_k(
                result["citations"],
                expected_patterns,
                expected_files
            )
            
            return {
                "question": question,
                "answer": result["answer"],
                "citations": result["citations"],
                "latency_ms": result["latency_ms"],
                "precision_at_k": precision_at_k,
                "expected_patterns": expected_patterns,
                "expected_files": expected_files,
                "success": True
            }
        else:
            return {
                "question": question,
                "error": f"API error: {response.status_code}",
                "success": False
            }
            
    except Exception as e:
        return {
            "question": question,
            "error": str(e),
            "success": False
        }


def _calculate_precision_at_k(citations: List[Dict], expected_patterns: List[str], expected_files: List[str]) -> float:
    """Calculate precision@k for retrieved citations."""
    if not citations:
        return 0.0
    
    relevant_count = 0
    
    for citation in citations:
        # Check if citation content matches expected patterns
        content = citation.get("content", "").lower()
        path = citation.get("path", "").lower()
        
        # Check content patterns
        content_match = any(pattern.lower() in content for pattern in expected_patterns)
        
        # Check file patterns
        file_match = any(pattern.lower() in path for pattern in expected_files)
        
        if content_match or file_match:
            relevant_count += 1
    
    return relevant_count / len(citations)


def _calculate_summary(test_cases: List[Dict]) -> Dict[str, Any]:
    """Calculate summary statistics."""
    successful_cases = [case for case in test_cases if case.get("success", False)]
    
    if not successful_cases:
        return {
            "total_cases": len(test_cases),
            "successful_cases": 0,
            "success_rate": 0.0,
            "avg_precision_at_k": 0.0,
            "avg_latency_ms": 0.0
        }
    
    avg_precision = sum(case["precision_at_k"] for case in successful_cases) / len(successful_cases)
    avg_latency = sum(case["latency_ms"] for case in successful_cases) / len(successful_cases)
    
    return {
        "total_cases": len(test_cases),
        "successful_cases": len(successful_cases),
        "success_rate": len(successful_cases) / len(test_cases),
        "avg_precision_at_k": avg_precision,
        "avg_latency_ms": avg_latency
    }


def _print_case_result(case_result: Dict):
    """Print a single case result."""
    if case_result.get("success", False):
        click.echo(f"  ✅ Success")
        click.echo(f"  Precision@K: {case_result['precision_at_k']:.3f}")
        click.echo(f"  Latency: {case_result['latency_ms']}ms")
        click.echo(f"  Citations: {len(case_result['citations'])}")
    else:
        click.echo(f"  ❌ Failed: {case_result.get('error', 'Unknown error')}")


def _print_summary(results: Dict[str, Any]):
    """Print evaluation summary."""
    summary = results["summary"]
    
    click.echo("\n" + "="*50)
    click.echo("EVALUATION SUMMARY")
    click.echo("="*50)
    click.echo(f"Repository: {results['repo']}")
    click.echo(f"Total test cases: {summary['total_cases']}")
    click.echo(f"Successful cases: {summary['successful_cases']}")
    click.echo(f"Success rate: {summary['success_rate']:.1%}")
    click.echo(f"Average Precision@K: {summary['avg_precision_at_k']:.3f}")
    click.echo(f"Average latency: {summary['avg_latency_ms']:.1f}ms")
    click.echo("="*50)


if __name__ == '__main__':
    eval_qa()
