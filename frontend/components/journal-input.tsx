"use client";

import { useState } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { 
  Lightbulb, 
  ArrowRight, 
  RefreshCw,
  CornerDownRight
} from 'lucide-react';
import { cn } from '../lib/utils';

interface JournalInputProps {
  onSubmit: (text: string, prompt: string) => void;
}

const EXAMPLE_PROMPTS = [
  "What was the highlight of your day?",
  "Did you learn something new today?",
  "What made you smile today?",
  "What are you grateful for today?",
  "What challenged you today?",
  "Who did you connect with today?",
  "What are you looking forward to tomorrow?",
  "How did you take care of yourself today?",
];

export default function JournalInput({ onSubmit }: JournalInputProps) {
  const [journalText, setJournalText] = useState('');
  const [activePrompt, setActivePrompt] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const getRandomPrompt = () => {
    const currentPrompts = [...EXAMPLE_PROMPTS];
    if (activePrompt) {
      const currentIndex = currentPrompts.indexOf(activePrompt);
      if (currentIndex > -1) {
        currentPrompts.splice(currentIndex, 1);
      }
    }
    const randomIndex = Math.floor(Math.random() * currentPrompts.length);
    setActivePrompt(currentPrompts[randomIndex]);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJournalText(e.target.value);
    setIsTyping(true);
    const timeout = setTimeout(() => setIsTyping(false), 1000);
    return () => clearTimeout(timeout);
  };

  const handleSubmit = () => {
    if (journalText.trim()) {
      onSubmit(journalText, activePrompt);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-4">
        <Card className="p-4 flex-1 bg-card border border-border">
          <Textarea
            placeholder="Tell me about your day..."
            className="min-h-[200px] resize-none border-0 focus-visible:ring-0 p-0"
            value={journalText}
            onChange={handleTextChange}
          />
          <div className="flex justify-between items-center mt-4">
            <div className="text-xs text-muted-foreground">
              {journalText.length > 0 
                ? isTyping 
                  ? 'Typing...' 
                  : `${journalText.length} characters`
                : 'Start typing...'}
            </div>
            {activePrompt && (
              <div className="text-sm text-muted-foreground flex items-center">
                <span className="italic mr-2">&ldquo;{activePrompt}&rdquo;</span>
                <CornerDownRight size={14} />
              </div>
            )}
          </div>
        </Card>
      </div>
      
      <p className="text-sm text-muted-foreground text-center">
        Up to 5 story points will be taken from your day and turned into video.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <Button 
          variant="outline" 
          className="gap-2 flex-1 sm:flex-none"
          onClick={getRandomPrompt}
        >
          <Lightbulb size={16} />
          <span>{activePrompt ? 'Another Prompt' : 'Need a Prompt?'}</span>
          <RefreshCw size={14} className={cn(
            "ml-1 transition-transform duration-500",
            activePrompt && "rotate-180"
          )} />
        </Button>
        
        <Button 
          onClick={handleSubmit}
          disabled={!journalText.trim()}
          className="gap-2 flex-1"
        >
          Continue
          <ArrowRight size={16} />
        </Button>
      </div>
    </div>
  );
}