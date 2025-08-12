'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Code, FileText, Clock, Zap, Settings, Plus } from 'lucide-react';
import { useRepos, useQueryCodebase } from '@/hooks/useApi';
import { useAppStore } from '@/store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import ReactMarkdown from 'react-markdown';
import CodeSnippet from '@/components/CodeSnippet';

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [showRepoSelector, setShowRepoSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { data: repos } = useRepos();
  const queryMutation = useQueryCodebase();
  
  const {
    selectedRepos,
    chatHistory,
    setSelectedRepos,
    addChatMessage,
    updateChatMessage,
    clearChatHistory,
  } = useAppStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || selectedRepos.length === 0) return;

    const messageId = Date.now().toString();
    const newMessage = {
      id: messageId,
      question: question.trim(),
      timestamp: Date.now(),
      isLoading: true,
    };

    addChatMessage(newMessage);
    setQuestion('');

    try {
      const response = await queryMutation.mutateAsync({
        question: question.trim(),
        repo_ids: selectedRepos,
        k: 5,
      });

      updateChatMessage(messageId, {
        response,
        isLoading: false,
      });
    } catch (error) {
      updateChatMessage(messageId, {
        response: {
          answer: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          citations: [],
          snippets: [],
          latency_ms: 0,
        },
        isLoading: false,
      });
    }
  };

  const toggleRepoSelection = (repoId: string) => {
    if (selectedRepos.includes(repoId)) {
      setSelectedRepos(selectedRepos.filter(id => id !== repoId));
    } else {
      setSelectedRepos([...selectedRepos, repoId]);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-semibold text-gray-900">CodeBase QA</h1>
          <p className="text-sm text-gray-500 mt-1">AI-powered code assistant</p>
        </div>
        
        <div className="p-4">
          <Button
            onClick={() => setShowRepoSelector(!showRepoSelector)}
            variant="outline"
            className="w-full justify-start"
          >
            <Settings className="w-4 h-4 mr-2" />
            Repositories ({selectedRepos.length})
          </Button>
        </div>

        {showRepoSelector && (
          <div className="px-4 pb-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Select Repositories</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <ScrollArea className="h-48">
                  {!repos || repos.length === 0 ? (
                    <p className="text-sm text-gray-500">No repositories available</p>
                  ) : (
                    <div className="space-y-2">
                      {repos.map((repo) => (
                        <div
                          key={repo.repo_id}
                          className={`p-2 rounded-md border cursor-pointer transition-colors ${
                            selectedRepos.includes(repo.repo_id)
                              ? 'bg-blue-50 border-blue-200'
                              : 'hover:bg-gray-50'
                          }`}
                          onClick={() => toggleRepoSelection(repo.repo_id)}
                        >
                          <div className="text-sm font-medium">{repo.name}</div>
                          <div className="text-xs text-gray-500">
                            {repo.file_count} files • {repo.chunk_count} chunks
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="flex-1" />
        
        <div className="p-4 border-t border-gray-200">
          <Button
            onClick={clearChatHistory}
            variant="ghost"
            size="sm"
            className="w-full"
          >
            Clear History
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="p-6">
              {chatHistory.length === 0 ? (
                <div className="flex items-center justify-center h-96">
                  <div className="text-center max-w-md">
                    <Bot className="w-16 h-16 text-blue-400 mx-auto mb-6" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-3">
                      Welcome to CodeBase QA Agent
                    </h3>
                    <p className="text-gray-600 mb-6 leading-relaxed">
                      Ask questions about your codebase and get intelligent answers with code snippets, citations, and context.
                    </p>
                    {selectedRepos.length === 0 ? (
                      <div className="space-y-3">
                        <Badge variant="outline" className="text-orange-600 border-orange-200">
                          ⚠️ Select repositories to get started
                        </Badge>
                        <p className="text-sm text-gray-500">
                          Choose repositories from the sidebar to begin asking questions.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                          ✅ Ready to answer questions
                        </Badge>
                        <p className="text-sm text-gray-500">
                          Try asking: "How does authentication work?" or "Show me the main API endpoints"
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-6 max-w-4xl mx-auto">
                  {chatHistory.map((message) => (
                    <div key={message.id} className="space-y-4">
                      {/* User Message */}
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <Card>
                            <CardContent className="p-4">
                              <p className="text-gray-900">{message.question}</p>
                            </CardContent>
                          </Card>
                        </div>
                      </div>

                      {/* AI Response */}
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                          <Bot className="w-4 h-4 text-green-600" />
                        </div>
                        <div className="flex-1">
                          {message.isLoading ? (
                            <Card className="border-blue-200 bg-blue-50">
                              <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                  <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                  </div>
                                  <span className="text-sm text-blue-700 font-medium">Analyzing your codebase...</span>
                                </div>
                                <div className="mt-2 text-xs text-blue-600">
                                  Searching through {selectedRepos.length} repositor{selectedRepos.length === 1 ? 'y' : 'ies'}
                                </div>
                              </CardContent>
                            </Card>
                          ) : message.response ? (
                            <div className="space-y-4">
                              <Card>
                                <CardContent className="p-4">
                                  <div className="flex items-center gap-4 mb-3 text-xs text-gray-500">
                                    <div className="flex items-center gap-1">
                                      <Clock className="w-3 h-3" />
                                      {message.response.latency_ms}ms
                                    </div>
                                    {message.response.mode && (
                                      <Badge variant="secondary" className="text-xs">
                                        <Zap className="w-3 h-3 mr-1" />
                                        {message.response.mode}
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="prose prose-sm max-w-none">
                                    <ReactMarkdown>{message.response.answer}</ReactMarkdown>
                                  </div>
                                </CardContent>
                              </Card>

                              {message.response.citations.length > 0 && (
                                <Card>
                                  <CardHeader className="pb-3">
                                    <CardTitle className="text-sm flex items-center gap-2">
                                      <FileText className="w-4 h-4" />
                                      Citations ({message.response.citations.length})
                                    </CardTitle>
                                  </CardHeader>
                                  <CardContent className="pt-0">
                                    <div className="space-y-2">
                                      {message.response.citations.map((citation, idx) => (
                                        <div key={idx} className="p-3 bg-gray-50 rounded-md">
                                          <div className="font-mono text-sm">{citation.path}</div>
                                          <div className="text-xs text-gray-500">
                                            Lines {citation.start}-{citation.end} • Score: {citation.score.toFixed(2)}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </CardContent>
                                </Card>
                              )}

                              {message.response.snippets.length > 0 && (
                                <Card>
                                  <CardHeader className="pb-3">
                                    <CardTitle className="text-sm flex items-center gap-2">
                                      <Code className="w-4 h-4" />
                                      Code Snippets ({message.response.snippets.length})
                                    </CardTitle>
                                  </CardHeader>
                                  <CardContent className="pt-0">
                                    <div className="space-y-4">
                                      {message.response.snippets.map((snippet, idx) => (
                                        <CodeSnippet key={idx} snippet={snippet} />
                                      ))}
                                    </div>
                                  </CardContent>
                                </Card>
                              )}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <Input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={
                  selectedRepos.length === 0
                    ? "Select repositories first..."
                    : "Ask a question about your codebase..."
                }
                disabled={queryMutation.isPending || selectedRepos.length === 0}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={queryMutation.isPending || !question.trim() || selectedRepos.length === 0}
              >
                {queryMutation.isPending ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}