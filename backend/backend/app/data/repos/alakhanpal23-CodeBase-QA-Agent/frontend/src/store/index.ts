import { create } from 'zustand';
import { ChatMessage, Repository } from '@/types';

interface AppState {
  selectedRepos: string[];
  chatHistory: ChatMessage[];
  setSelectedRepos: (repos: string[]) => void;
  addChatMessage: (message: ChatMessage) => void;
  updateChatMessage: (id: string, updates: Partial<ChatMessage>) => void;
  clearChatHistory: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedRepos: [],
  chatHistory: [],
  setSelectedRepos: (repos) => set({ selectedRepos: repos }),
  addChatMessage: (message) =>
    set((state) => ({ chatHistory: [...state.chatHistory, message] })),
  updateChatMessage: (id, updates) =>
    set((state) => ({
      chatHistory: state.chatHistory.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),
  clearChatHistory: () => set({ chatHistory: [] }),
}));