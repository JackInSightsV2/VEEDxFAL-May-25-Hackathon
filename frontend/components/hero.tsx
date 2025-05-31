'use client';

import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

export default function Hero() {
  const router = useRouter();

  const handleSeeExamples = () => {
    router.push('/examples');
  };

  return (
    <div className="relative overflow-hidden py-24 px-6 sm:px-10 md:px-12 lg:px-24">      
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <div className="inline-flex items-center justify-center px-6 py-2 mb-8 border border-secondary/20 rounded-full bg-white/5 backdrop-blur-sm shadow-lg animate-float">
          <Sparkles className="h-5 w-5 mr-2 text-secondary animate-pulse" />
          <span className="text-sm font-medium">Transform your daily thoughts into cinematic stories</span>
        </div>
        
        <h1 className="mt-6 text-4xl md:text-5xl lg:text-7xl font-bold tracking-tight">
          Turn your <span className="text-secondary">daily journal</span> into
          <br />
          <span className="text-secondary">beautiful videos</span>
        </h1>
        
        <p className="mt-8 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto backdrop-blur-sm bg-white/5 p-4 rounded-2xl">
          Share your day in a whole new way. Our AI transforms your thoughts into stunning, 
          shareable videos for TikTok, Instagram, and more.
        </p>
        
        <div className="mt-12 flex justify-center">
          <Button 
            onClick={handleSeeExamples}
            size="lg" 
            variant="outline" 
            className="text-base border-2 backdrop-blur-sm bg-white/5 hover:bg-secondary/5 transition-colors duration-300"
          >
            See Examples
          </Button>
        </div>
      </div>
    </div>
  );
}