import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { ArrowLeft, ArrowRight, PaintBucket } from 'lucide-react';

interface StyleSettingsProps {
  onSubmit: (data: { gender: string; age: string; style: string; name?: string }) => void;
  onBack: () => void;
  initialValues: {
    gender: string;
    age: string;
    style: string;
    name?: string;
  };
}

const styles = [
  { id: 'ghibli', name: 'Studio Ghibli', description: 'Dreamy, hand-drawn animation style' },
  { id: 'pixar', name: 'Pixar', description: 'Vibrant 3D animation with expressive characters' },
  { id: 'anime', name: 'Anime', description: 'Japanese animation style with bold colors' },
  { id: 'watercolor', name: 'Watercolor', description: 'Soft, painterly aesthetic with gentle colors' },
  { id: 'cyberpunk', name: 'Cyberpunk', description: 'Futuristic neon aesthetic with high contrast' },
  { id: 'blog-female', name: 'Blog (Female)', description: 'A blog-like video of a presenter talking about your day' },
  { id: 'blog-male', name: 'Blog (Male)', description: 'A blog-like video of a presenter talking about your day' },
  { id: 'realistic', name: 'Realistic', description: 'Standard video generation' },
];

export default function StyleSettings({ onSubmit, onBack, initialValues }: StyleSettingsProps) {
  const [formData, setFormData] = useState({
    gender: initialValues.gender || '',
    age: initialValues.age || '',
    style: initialValues.style || 'ghibli',
    name: initialValues.name || '',
    voicePreference: initialValues.gender === 'non-binary' ? 'feminine' : '',
  });

  const isBlogStyle = formData.style.startsWith('blog-');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.gender && formData.age && (!isBlogStyle || formData.name)) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 md:p-8">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-secondary to-accent"></div>
      <h2 className="text-2xl font-bold mb-6 text-center gradient-text">Customize Your Video</h2>
      
      <div className="space-y-8">
        <div className="space-y-4">
          <Label htmlFor="gender">Gender</Label>
          <Select
            value={formData.gender}
            onValueChange={(value) => {
              setFormData({ 
                ...formData, 
                gender: value,
                voicePreference: value === 'non-binary' ? 'feminine' : ''
              });
            }}
            required
          >
            <SelectTrigger id="gender">
              <SelectValue placeholder="Select gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="non-binary">Non-binary</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {formData.gender === 'non-binary' && (
          <div className="space-y-4">
            <Label htmlFor="voice-preference">Voice Preference</Label>
            <Select
              value={formData.voicePreference}
              onValueChange={(value) => setFormData({ ...formData, voicePreference: value })}
              required
            >
              <SelectTrigger id="voice-preference">
                <SelectValue placeholder="Select voice preference" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="feminine">Feminine Voice</SelectItem>
                <SelectItem value="masculine">Masculine Voice</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
        
        <div className="space-y-4">
          <Label htmlFor="age">Age Group</Label>
          <Select
            value={formData.age}
            onValueChange={(value) => setFormData({ ...formData, age: value })}
            required
          >
            <SelectTrigger id="age">
              <SelectValue placeholder="Select age group" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="teen">Teen (13-19)</SelectItem>
              <SelectItem value="young-adult">Young Adult (20-29)</SelectItem>
              <SelectItem value="adult">Adult (30-49)</SelectItem>
              <SelectItem value="senior">Senior (50+)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <PaintBucket className="h-4 w-4 text-primary" />
            <Label>Visual Style</Label>
          </div>
          
          <RadioGroup
            value={formData.style}
            onValueChange={(value) => setFormData({ ...formData, style: value })}
            className="grid gap-4 grid-cols-1 sm:grid-cols-2"
          >
            {styles.map((style) => (
              <div key={style.id} className="relative">
                <RadioGroupItem
                  value={style.id}
                  id={style.id}
                  className="peer sr-only"
                />
                <Label
                  htmlFor={style.id}
                  className="flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5 hover:bg-muted/50"
                >
                  <span className="font-medium">{style.name}</span>
                  <span className="text-sm text-muted-foreground">{style.description}</span>
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        {isBlogStyle && (
          <div className="space-y-4">
            <Label htmlFor="presenter-name">What is your name</Label>
            <Input
              id="presenter-name"
              placeholder="Enter your name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="bg-white/5 border-primary/10"
            />
            <p className="text-sm text-muted-foreground">
              Your name will be used in the video
            </p>
          </div>
        )}
      </div>
      
      <div className="flex justify-between mt-8">
        <Button type="button" variant="outline" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button 
          type="submit" 
          disabled={!formData.gender || !formData.age || (isBlogStyle && !formData.name) || (formData.gender === 'non-binary' && !formData.voicePreference)}
        >
          Create Video
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}