'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Eye, Clock, Zap } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '@/types';
import CodeSnippet from './CodeSnippet';

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [selectedSnippet, setSelectedSnippet] = useState<string | null>(null);

  if (message.isLoading) {
    return (
      <div className="mb-6">
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <p className="font-medium text-blue-900">{message.question}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="animate-pulse flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-300 rounded-full"></div>
            <span className="text-gray-600">Thinking...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!message.response) return null;

  const { response } = message;

  return (
    <div className="mb-6">
      <div className="bg-blue-50 p-4 rounded-lg mb-4">
        <p className="font-medium text-blue-900">{message.question}</p>
      </div>
      
      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center gap-4 mb-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {response.latency_ms}ms
          </div>
          {response.mode && (
            <div className="flex items-center gap-1">
              <Zap className="w-4 h-4" />
              {response.mode}
            </div>
          )}
          {response.confidence && (
            <div className="flex items-center gap-1">
              <span>Confidence: {Math.round(response.confidence * 100)}%</span>
            </div>
          )}
        </div>

        <div className="prose max-w-none mb-6">
          <ReactMarkdown>{response.answer}</ReactMarkdown>
        </div>

        {response.citations.length > 0 && (
          <div className="mb-6">
            <h4 className="font-medium mb-3">Citations</h4>
            <div className="space-y-2">
              {response.citations.map((citation, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <span className="font-mono text-sm">{citation.path}</span>
                    <span className="text-gray-500 ml-2">
                      Lines {citation.start}-{citation.end}
                    </span>
                    <span className="text-gray-400 ml-2">
                      Score: {citation.score.toFixed(2)}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      const snippet = response.snippets.find(
                        s => s.path === citation.path && s.start === citation.start
                      );
                      if (snippet) {
                        setSelectedSnippet(
                          selectedSnippet === `${citation.path}-${citation.start}` 
                            ? null 
                            : `${citation.path}-${citation.start}`
                        );
                      }
                    }}
                    className="flex items-center gap-1 px-3 py-1 bg-blue-100 hover:bg-blue-200 rounded text-sm text-blue-700"
                  >
                    <Eye className="w-4 h-4" />
                    View Snippet
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {response.snippets.length > 0 && (
          <div>
            <h4 className="font-medium mb-3">Code Snippets</h4>
            <div className="space-y-4">
              {response.snippets.map((snippet, index) => {
                const snippetId = `${snippet.path}-${snippet.start}`;
                const isSelected = selectedSnippet === snippetId;
                
                return (
                  <div
                    key={index}
                    className={`transition-all ${
                      isSelected ? 'ring-2 ring-blue-500' : ''
                    }`}
                  >
                    <CodeSnippet snippet={snippet} />
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}