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
  const { toast } = useToast();

  const handleTextSubmit = (text: string, prompt: string) => {
    setJournalData(prev => ({ ...prev, content: text, prompt }));
    setActiveStep('style');
  };

  const handleVideoSubmit = (file: File) => {
    setJournalData(prev => ({ ...prev, videoFile: file }));
    setActiveStep('style');
  };

  const handleStyleSubmit = async (styleData: { gender: string; age: string; style: string }) => {
    try {
      setJournalData(prev => ({ ...prev, ...styleData }));
      setActiveStep('processing');
      
      const response = await submitJournalData({
        ...journalData,
        ...styleData
      });
      
      setVideoId(response.videoId);
      
      const pollingInterval = setInterval(async () => {
        const status = await checkVideoStatus(response.videoId);
        if (status.status === 'completed') {
          clearInterval(pollingInterval);
          setVideoUrl(status.videoUrl);
          setActiveStep('preview');
          toast({
            title: "Video Created!",
            description: "Your journal video is ready to view and share.",
          });
        } else if (status.status === 'failed') {
          clearInterval(pollingInterval);
          toast({
            variant: "destructive",
            title: "Generation Failed",
            description: "There was an error creating your video. Please try again.",
          });
          setActiveStep('input');
        }
      }, 30000);
      
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
                style: journalData.style
              }}
            />
          )}

          {activeStep === 'processing' && (
            <ProcessingStatus 
              videoId={videoId}
              onCancel={handleReset}
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