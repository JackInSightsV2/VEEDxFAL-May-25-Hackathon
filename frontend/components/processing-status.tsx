"use client";

import { useState, useEffect } from 'react';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ProcessingStatusProps {
  videoId: string | null;
  onCancel: () => void;
}

export default function ProcessingStatus({ videoId, onCancel }: ProcessingStatusProps) {
  const [progress, setProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(480); // 8 minutes in seconds
  const [showTips, setShowTips] = useState(true);
  const [currentTipIndex, setCurrentTipIndex] = useState(0);

  const tips = [
    "We're transforming your journal into a visual story...",
    "Our AI is selecting the perfect visual style for your narrative...",
    "Creating stunning visual sequences based on your content...",
    "Adding cinematic transitions to bring your story to life...",
    "Optimizing your video for social media sharing...",
  ];

  useEffect(() => {
    // Simulate progress
    const totalTime = 480; // 8 minutes in seconds
    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + (100 / totalTime / 10);
        return newProgress > 100 ? 100 : newProgress;
      });
      
      setTimeRemaining((prev) => {
        const newTime = prev - 0.1;
        return newTime < 0 ? 0 : newTime;
      });
    }, 100); // Update every 0.1 seconds
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Rotate tips
    const tipInterval = setInterval(() => {
      setCurrentTipIndex((prev) => (prev + 1) % tips.length);
    }, 5000);
    
    return () => clearInterval(tipInterval);
  }, []);

  const formatTimeRemaining = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-6 md:p-8 text-center">
      <div className="relative w-24 h-24 mx-auto mb-6">
        <svg className="w-24 h-24 rotate-[-90deg]" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            className="text-muted/20"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray="283"
            strokeDashoffset={283 - (283 * progress) / 100}
            className="text-primary transition-all duration-300 ease-in-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-2xl font-semibold">
          {Math.round(progress)}%
        </div>
      </div>
      
      <h2 className="text-2xl font-bold mb-2">Creating Your Video</h2>
      <p className="text-muted-foreground mb-6">
        This process takes approximately 8 minutes. Estimated time remaining: {formatTimeRemaining(timeRemaining)}
      </p>
      
      <div className="relative h-20 mb-8 overflow-hidden">
        {tips.map((tip, index) => (
          <p
            key={index}
            className={cn(
              "absolute inset-0 flex items-center justify-center transition-opacity duration-1000",
              currentTipIndex === index ? "opacity-100" : "opacity-0"
            )}
          >
            {tip}
          </p>
        ))}
      </div>
      
      <div className="flex justify-center">
        <Button
          variant="outline"
          onClick={onCancel}
          className="gap-2"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}