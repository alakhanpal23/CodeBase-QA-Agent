'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Plus, Trash2, GitBranch, FileText, Package, ArrowLeft, Loader2, MessageSquare } from 'lucide-react';
import { useRepos, useIngestRepo, useDeleteRepo } from '@/hooks/useApi';

export default function ReposPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const { data: repos, isLoading, error } = useRepos();
  const ingestMutation = useIngestRepo();
  const deleteMutation = useDeleteRepo();

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    
    // Validate GitHub URL
    const githubUrlPattern = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/;
    if (!githubUrlPattern.test(repoUrl.trim())) {
      alert('Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)');
      return;
    }
    
    try {
      const repoName = repoUrl.split('/').slice(-2).join('-').replace(/\.git$/, '');
      await ingestMutation.mutateAsync({ 
        source: 'github',
        url: repoUrl.trim(),
        repo_id: repoName,
        include_globs: ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.go', '**/*.rb', '**/*.php', '**/*.cs', '**/*.cpp', '**/*.c', '**/*.h', '**/*.md', '**/*.txt', '**/*.json', '**/*.yml', '**/*.yaml'],
        exclude_globs: ['.git/**', 'node_modules/**', 'dist/**', 'build/**', '.venv/**', '__pycache__/**', '*.pyc', '.DS_Store']
      });
      setRepoUrl('');
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to ingest repository';
      alert(`Error: ${errorMessage}`);
      console.error('Failed to ingest repository:', error);
    }
  };

  const handleDelete = async (repoId: string) => {
    if (!confirm(`Are you sure you want to delete the repository "${repoId}"? This action cannot be undone.`)) return;
    
    try {
      await deleteMutation.mutateAsync(repoId);
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to delete repository';
      alert(`Error: ${errorMessage}`);
      console.error('Failed to delete repository:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors border"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Repository Management</h1>
              <p className="text-gray-600 mt-1">Add and manage your codebase repositories</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-sm text-gray-500">
              {repos?.length || 0} repositories
            </div>
            <Link
              href="/chat"
              className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2"
            >
              <MessageSquare className="w-4 h-4" />
              Start Chatting
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Plus className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Add New Repository</h2>
              <p className="text-gray-600 text-sm">Connect a GitHub repository to start asking questions</p>
            </div>
          </div>
          <form onSubmit={handleIngest} className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repository"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed transition-colors"
                  disabled={ingestMutation.isPending}
                  required
                />
              </div>
              <button
                type="submit"
                disabled={ingestMutation.isPending || !repoUrl.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 text-white rounded-lg transition-all duration-200 flex items-center gap-2 font-medium shadow-sm hover:shadow-md disabled:shadow-none"
              >
                {ingestMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                {ingestMutation.isPending ? 'Processing...' : 'Add Repository'}
              </button>
            </div>
          </form>
          {ingestMutation.error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm font-medium">Ingestion Failed</p>
              <p className="text-red-600 text-sm mt-1">
                {(ingestMutation.error as any)?.response?.data?.detail || 
                 ingestMutation.error.message || 
                 'An unexpected error occurred'}
              </p>
            </div>
          )}
          {ingestMutation.isSuccess && (
            <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800 text-sm font-medium">Repository Added Successfully!</p>
              <p className="text-green-600 text-sm mt-1">
                The repository has been ingested and is ready for querying.
              </p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Your Repositories</h2>
                <p className="text-gray-600 text-sm mt-1">Manage your connected repositories and their indexing status</p>
              </div>
              {repos && repos.length > 0 && (
                <div className="text-sm text-gray-500">
                  Total: {repos.reduce((acc, repo) => acc + repo.file_count, 0)} files, {repos.reduce((acc, repo) => acc + repo.chunk_count, 0)} chunks
                </div>
              )}
            </div>
          </div>
          
          {isLoading ? (
            <div className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Loading repositories...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <div className="text-red-600 mb-2">Failed to load repositories</div>
              <p className="text-sm text-gray-500">
                {(error as any)?.response?.data?.detail || 
                 (error as any)?.message || 
                 'An unexpected error occurred'}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : !repos || repos.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Package className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No repositories yet</h3>
              <p className="text-gray-600 mb-4">Add your first repository to start asking questions about your codebase</p>
              <div className="text-sm text-gray-500">
                Supported: GitHub public and private repositories
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {repos.map((repo) => (
                <div key={repo.repo_id} className="p-6 hover:bg-gray-50/50 transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl">
                        <GitBranch className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold text-gray-900 text-lg">{repo.name}</h3>
                          <div className="flex items-center gap-2">
                            {repo.chunk_count > 0 ? (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1"></div>
                                Indexed
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full mr-1"></div>
                                Processing
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">Repository ID: {repo.repo_id}</p>
                        <div className="flex items-center gap-6 text-sm text-gray-500">
                          <div className="flex items-center gap-1.5">
                            <FileText className="w-4 h-4" />
                            <span className="font-medium">{repo.file_count.toLocaleString()}</span>
                            <span>files</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Package className="w-4 h-4" />
                            <span className="font-medium">{repo.chunk_count.toLocaleString()}</span>
                            <span>chunks</span>
                          </div>
                          {repo.chunk_count > 0 && (
                            <div className="flex items-center gap-1.5 text-green-600">
                              <span>Ready for queries</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDelete(repo.repo_id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-red-200 hover:border-red-300"
                        title="Delete repository"
                      >
                        {deleteMutation.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}