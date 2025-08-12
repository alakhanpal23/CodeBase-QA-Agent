'use client';

import { useState } from 'react';
import { Editor } from '@monaco-editor/react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Snippet } from '@/types';

interface CodeSnippetProps {
  snippet: Snippet;
}

export default function CodeSnippet({ snippet }: CodeSnippetProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getLanguage = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    const langMap: Record<string, string> = {
      js: 'javascript',
      ts: 'typescript',
      py: 'python',
      java: 'java',
      cpp: 'cpp',
      c: 'c',
      go: 'go',
      rs: 'rust',
      php: 'php',
      rb: 'ruby',
      cs: 'csharp',
      json: 'json',
      yaml: 'yaml',
      yml: 'yaml',
      md: 'markdown',
      html: 'html',
      css: 'css',
      scss: 'scss',
      sql: 'sql',
    };
    return langMap[ext || ''] || 'plaintext';
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          <span className="font-mono text-sm">{snippet.path}</span>
          <span className="text-xs text-gray-500">
            Lines {snippet.window_start}-{snippet.window_end}
          </span>
        </div>
      </button>
      
      {isExpanded && (
        <div className="border-t">
          <Editor
            height="300px"
            language={getLanguage(snippet.path)}
            value={snippet.code}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              lineNumbersMinChars: Math.max(3, snippet.window_end.toString().length),
              glyphMargin: false,
              folding: false,
              lineDecorationsWidth: 0,
              theme: 'vs-light',
            }}
            onMount={(editor) => {
              // Highlight the original snippet lines
              const model = editor.getModel();
              if (model) {
                const startLine = snippet.start - snippet.window_start + 1;
                const endLine = snippet.end - snippet.window_start + 1;
                editor.deltaDecorations([], [
                  {
                    range: {
                      startLineNumber: startLine,
                      startColumn: 1,
                      endLineNumber: endLine,
                      endColumn: model.getLineMaxColumn(endLine),
                    },
                    options: {
                      className: 'bg-yellow-100',
                      isWholeLine: true,
                    },
                  },
                ]);
              }
            }}
          />
        </div>
      )}
    </div>
  );
}