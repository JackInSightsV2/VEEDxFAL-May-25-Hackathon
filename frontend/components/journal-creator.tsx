"use client";

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import JournalInput from '@/components/journal-input';
import VideoUpload from '@/components/video-upload';
import StyleSettings from '@/components/style-settings';
import ProcessingStatus from '@/components/processing-status';
import VideoPreview from '@/components/video-preview';
import { JournalData } from '@/lib/types';
import { submitJournalData, checkVideoStatus } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

export default function JournalCreator() {
  const [activeStep, setActiveStep] = useState<'input' | 'style' | 'processing' | 'preview'>('input');
  const [inputMethod, setInputMethod] = useState<'text' | 'video'>('text');
  const [journalData, setJournalData] = useState<JournalData>({
    content: '',
    videoFile: null,
    gender: '',
    age: '',
    style: 'ghibli',
    prompt: '',
  });
  const [videoId, setVideoId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState('1-3 minutes');
  const { toast } = useToast();

  const handleTextSubmit = (text: string, prompt: string) => {
    setJournalData(prev => ({ ...prev, content: text, prompt }));
    setActiveStep('style');
  };

  const handleVideoSubmit = (file: File) => {
    setJournalData(prev => ({ ...prev, videoFile: file }));
    setActiveStep('style');
  };

  const handleStyleSubmit = async (styleData: { gender: string; age: string; style: string; name?: string; voicePreference?: string }) => {
    try {
      const updatedJournalData = { ...journalData, ...styleData };
      setJournalData(updatedJournalData);
      setActiveStep('processing');
      
      // Reset progress state
      setProgress(0);
      setEstimatedTimeRemaining('1-3 minutes');
      
      const response = await submitJournalData(updatedJournalData);
      
      setVideoId(response.videoId);
      
      // Set a 4-minute timeout to prevent infinite waiting
      const timeoutId = setTimeout(() => {
        clearInterval(pollingInterval);
        toast({
          variant: "destructive",
          title: "Generation Timeout",
          description: "Video generation is taking longer than expected. Please try again.",
        });
        setActiveStep('input');
      }, 240000); // 4 minutes timeout
      
      const pollingInterval = setInterval(async () => {
        const status = await checkVideoStatus(response.videoId);
        
        // Update progress and time remaining from backend
        setProgress(status.progress);
        if (status.estimatedTimeRemaining) {
          setEstimatedTimeRemaining(status.estimatedTimeRemaining);
        }
        
        if (status.status === 'completed') {
          clearInterval(pollingInterval);
          clearTimeout(timeoutId);
          setVideoUrl(status.videoUrl);
          setActiveStep('preview');
          toast({
            title: "Video Created!",
            description: "Your journal video is ready to view and share.",
          });
        } else if (status.status === 'failed') {
          clearInterval(pollingInterval);
          clearTimeout(timeoutId);
          toast({
            variant: "destructive",
            title: "Generation Failed",
            description: status.error || "There was an error creating your video. Please try again.",
          });
          setActiveStep('input');
        }
      }, 15000); // Check every 15 seconds instead of 30
      
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Submission Error",
        description: "Failed to submit your journal data. Please try again.",
      });
      console.error("Error submitting journal data:", error);
    }
  };

  const handleReset = () => {
    setJournalData({
      content: '',
      videoFile: null,
      gender: '',
      age: '',
      style: 'ghibli',
      prompt: '',
    });
    setVideoId(null);
    setVideoUrl(null);
    setProgress(0);
    setEstimatedTimeRemaining('1-3 minutes');
    setActiveStep('input');
    setInputMethod('text');
  };

  return (
    <section id="journal-creator" className="py-16 px-6 sm:px-10 md:px-12 lg:px-24">
      <div className="max-w-4xl mx-auto">
        <Card className="overflow-hidden border-primary/10 bg-white/5 backdrop-blur-md shadow-xl shadow-primary/5">
          {activeStep === 'input' && (
            <div className="p-6 md:p-8 relative">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-secondary to-accent"></div>
              <h2 className="text-2xl font-bold mb-6 text-center gradient-text">Share Your Day</h2>
              <Tabs defaultValue={inputMethod} onValueChange={(v) => setInputMethod(v as 'text' | 'video')}>
                <TabsList className="grid w-full grid-cols-2 mb-8 bg-white/10">
                  <TabsTrigger value="text">Write Journal</TabsTrigger>
                  <TabsTrigger value="video">Upload Video</TabsTrigger>
                </TabsList>
                <TabsContent value="text">
                  <JournalInput onSubmit={handleTextSubmit} />
                </TabsContent>
                <TabsContent value="video">
                  <VideoUpload onSubmit={handleVideoSubmit} />
                </TabsContent>
              </Tabs>
            </div>
          )}

          {activeStep === 'style' && (
            <StyleSettings 
              onSubmit={handleStyleSubmit}
              onBack={() => setActiveStep('input')}
              initialValues={{
                gender: journalData.gender,
                age: journalData.age,
                style: journalData.style,
                name: journalData.name,
                voicePreference: journalData.voicePreference
              }}
            />
          )}

          {activeStep === 'processing' && (
            <ProcessingStatus 
              videoId={videoId}
              onCancel={handleReset}
              progress={progress}
              estimatedTimeRemaining={estimatedTimeRemaining}
            />
          )}

          {activeStep === 'preview' && videoUrl && (
            <VideoPreview 
              videoUrl={videoUrl}
              onCreateNew={handleReset}
            />
          )}
        </Card>
      </div>
    </section>
  );
}