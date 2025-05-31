"use client";

import { useState, useEffect } from 'react';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface ProcessingStatusProps {
  videoId: string | null;
  onCancel: () => void;
  progress?: number;
  estimatedTimeRemaining?: string;
}

export default function ProcessingStatus({ 
  videoId, 
  onCancel, 
  progress = 0, 
  estimatedTimeRemaining = '1-3 minutes'
}: ProcessingStatusProps) {
  const [displayedProgress, setDisplayedProgress] = useState(0);
  const [showTips, setShowTips] = useState(true);
  const [currentTipIndex, setCurrentTipIndex] = useState(0);

  const tips = [
    "We're transforming your journal into a visual story...",
    "Our AI is selecting the perfect visual style for your narrative...",
    "Creating stunning visual sequences based on your content...",
    "Adding cinematic transitions to bring your story to life...",
    "Optimizing your video for social media sharing...",
  ];

  // Smooth progress animation effect
  useEffect(() => {
    const interval = setInterval(() => {
      setDisplayedProgress((prevDisplayed) => {
        // If we have real backend progress, smoothly move towards it
        if (progress > 0) {
          const diff = progress - prevDisplayed;
          if (Math.abs(diff) > 0.5) {
            // If there's a significant difference, move towards backend progress
            return prevDisplayed + (diff * 0.1); // Move 10% of the way towards target
          } else {
            // If we're close to backend progress, use it directly
            return progress;
          }
        } else {
          // Fallback: reach 100% in 3 minutes (180 seconds) if no backend updates
          // This means increment by ~0.056% every 100ms (100/180/10 ≈ 0.056)
          const incrementPerTick = 100 / (180 * 10); // 3 minutes = 180 seconds, 10 ticks per second
          return Math.min(prevDisplayed + incrementPerTick, 100);
        }
      });
    }, 100); // Update every 100ms for smooth animation

    return () => clearInterval(interval);
  }, [progress]);

  // When backend progress changes significantly, adjust displayed progress
  useEffect(() => {
    if (progress > displayedProgress + 5) {
      // If backend jumped ahead significantly, quickly catch up
      setDisplayedProgress(progress - 2); // Slightly behind so animation can catch up smoothly
    }
  }, [progress, displayedProgress]);

  useEffect(() => {
    // Rotate tips
    const tipInterval = setInterval(() => {
      setCurrentTipIndex((prev) => (prev + 1) % tips.length);
    }, 5000);
    
    return () => clearInterval(tipInterval);
  }, [tips.length]);

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
            strokeDashoffset={283 - (283 * displayedProgress) / 100}
            className="text-primary transition-all duration-300 ease-in-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-2xl font-semibold">
          {Math.round(displayedProgress)}%
        </div>
      </div>
      
      <h2 className="text-2xl font-bold mb-2">Creating Your Video</h2>
      <p className="text-muted-foreground mb-6">
        This process typically takes a few minutes. Estimated time remaining: {estimatedTimeRemaining}
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