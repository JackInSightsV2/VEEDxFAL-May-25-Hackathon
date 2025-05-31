/**
 * Frontend Integration Examples for ASYNC Video Generation API
 * 
 * All API calls now use concurrent processing by default for maximum speed.
 * No need to specify async_mode - everything is async!
 */

const API_BASE_URL = 'http://localhost:8000'; // Adjust to your backend URL

// Example 1: Generate video from uploaded file (with video upload)
async function generateVideoFromFile(videoFile, options = {}) {
    const formData = new FormData();
    formData.append('video', videoFile);
    
    // Optional parameters (will use sensible defaults if not provided)
    if (options.mood) formData.append('mood', options.mood);
    if (options.gender) formData.append('gender', options.gender);
    if (options.age_group) formData.append('age_group', options.age_group);
    if (options.visual_style) formData.append('visual_style', options.visual_style);
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        console.log('✅ Video generated successfully!');
        console.log(`📁 Job ID: ${result.job_id}`);
        console.log(`🎬 Final video: ${result.video}`);
        console.log(`⚡ Processing time: ${result.processing_time}s`);
        console.log(`📊 Success rate: ${result.success_rate}`);
        
        return result;
        
    } catch (error) {
        console.error('❌ Error generating video:', error);
        throw error;
    }
}

// Example 2: Generate video directly from text (no file upload needed)
async function generateVideoFromText(text, options = {}) {
    const formData = new FormData();
    formData.append('text', text);
    
    // Set defaults for text-based generation
    formData.append('mood', options.mood || 'Reflective');
    formData.append('gender', options.gender || 'female');
    formData.append('age_group', options.age_group || '26-35');
    formData.append('visual_style', options.visual_style || 'Studio Ghibli');
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate-from-text`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        console.log('✅ Video generated from text successfully!');
        console.log(`📁 Job ID: ${result.job_id}`);
        console.log(`🎬 Final video: ${result.video}`);
        console.log(`📝 Generated narration: ${result.generated_text}`);
        console.log(`⚡ Processing time: ${result.processing_time}s`);
        console.log(`🎞️ Video duration: ${result.video_duration}s`);
        console.log(`📊 Success rate: ${result.success_rate}`);
        
        return result;
        
    } catch (error) {
        console.error('❌ Error generating video from text:', error);
        throw error;
    }
}

// Example 3: React component using the API
function VideoGeneratorComponent() {
    const [isGenerating, setIsGenerating] = React.useState(false);
    const [result, setResult] = React.useState(null);
    const [text, setText] = React.useState('');
    const [options, setOptions] = React.useState({
        mood: 'Reflective',
        gender: 'female',
        age_group: '26-35',
        visual_style: 'Studio Ghibli'
    });

    const handleGenerateFromText = async () => {
        if (!text.trim()) {
            alert('Please enter some text first!');
            return;
        }

        setIsGenerating(true);
        setResult(null);

        try {
            const result = await generateVideoFromText(text, options);
            setResult(result);
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="video-generator">
            <h2>🎬 ASYNC Video Generator</h2>
            
            <div className="form-group">
                <label>Text to convert to video:</label>
                <textarea 
                    value={text} 
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Enter your story or description here..."
                    rows="4"
                />
            </div>

            <div className="options-grid">
                <div className="form-group">
                    <label>Visual Style:</label>
                    <select 
                        value={options.visual_style} 
                        onChange={(e) => setOptions({...options, visual_style: e.target.value})}
                    >
                        <option value="Studio Ghibli">Studio Ghibli</option>
                        <option value="Pixar">Pixar</option>
                        <option value="Anime">Anime</option>
                        <option value="Watercolor">Watercolor</option>
                        <option value="Cyberpunk">Cyberpunk</option>
                        <option value="Realistic">Realistic</option>
                        <option value="blog-female">Blog (Female)</option>
                        <option value="blog-male">Blog (Male)</option>
                        <option value="blog-nonbinary">Blog (Non-binary)</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Gender:</label>
                    <select 
                        value={options.gender} 
                        onChange={(e) => setOptions({...options, gender: e.target.value})}
                    >
                        <option value="female">Female</option>
                        <option value="male">Male</option>
                        <option value="non-binary">Non-binary</option>
                    </select>
                </div>

                {options.gender === 'non-binary' && (
                    <div className="form-group">
                        <label>Voice Style (for non-binary):</label>
                        <select 
                            value={options.voice_style || 'female'} 
                            onChange={(e) => setOptions({...options, voice_style: e.target.value})}
                        >
                            <option value="female">Female Voice</option>
                            <option value="male">Male Voice</option>
                        </select>
                        <small>Blog avatars only support male/female, so please choose your preferred voice style.</small>
                    </div>
                )}

                <div className="form-group">
                    <label>Age Group:</label>
                    <select 
                        value={options.age_group} 
                        onChange={(e) => setOptions({...options, age_group: e.target.value})}
                    >
                        <option value="18-25">18-25</option>
                        <option value="26-35">26-35</option>
                        <option value="36-45">36-45</option>
                        <option value="46-55">46-55</option>
                        <option value="55+">55+</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Mood:</label>
                    <select 
                        value={options.mood} 
                        onChange={(e) => setOptions({...options, mood: e.target.value})}
                    >
                        <option value="Reflective">Reflective</option>
                        <option value="Energetic">Energetic</option>
                        <option value="Peaceful">Peaceful</option>
                        <option value="Adventurous">Adventurous</option>
                    </select>
                </div>
            </div>

            <button 
                onClick={handleGenerateFromText} 
                disabled={isGenerating || !text.trim()}
                className="generate-btn"
            >
                {isGenerating ? '⚡ Generating Video (ASYNC)...' : '🎬 Generate Video'}
            </button>

            {result && (
                <div className="result">
                    <h3>✅ Video Generated Successfully!</h3>
                    <p><strong>Job ID:</strong> {result.job_id}</p>
                    <p><strong>Processing Time:</strong> {result.processing_time}s ⚡</p>
                    <p><strong>Videos Created:</strong> {result.generated_videos}</p>
                    <p><strong>Success Rate:</strong> {result.success_rate}</p>
                    <p><strong>Video Duration:</strong> {result.video_duration}s</p>
                    
                    <div className="generated-content">
                        <h4>Generated Narration:</h4>
                        <p>{result.generated_text}</p>
                    </div>
                    
                    <div className="video-container">
                        <h4>Final Video:</h4>
                        <video controls width="400">
                            <source src={result.video} type="video/mp4" />
                            Your browser does not support video playback.
                        </video>
                    </div>
                </div>
            )}
        </div>
    );
}

// Example 4: Simple JavaScript usage examples
async function runExamples() {
    console.log('🚀 Testing ASYNC Video Generation API...');
    
    // Example with text input
    try {
        const textResult = await generateVideoFromText(
            "Today I discovered a hidden garden behind my apartment. The flowers were blooming in vibrant colors, and butterflies danced among the petals. It felt like finding a secret paradise in the middle of the city.",
            {
                visual_style: 'Studio Ghibli',
                gender: 'female',
                age_group: '26-35',
                mood: 'Peaceful'
            }
        );
        
        console.log('Text-based generation successful:', textResult);
        
    } catch (error) {
        console.error('Text-based generation failed:', error);
    }
}

// Example 5: API parameter reference
const API_PARAMETERS = {
    // Required for /generate endpoint
    video: 'File object (from file input)',
    
    // Required for /generate-from-text endpoint  
    text: 'String - the story/description to convert to video',
    
    // Optional parameters for both endpoints
    mood: ['Reflective', 'Energetic', 'Peaceful', 'Adventurous'], // Default: 'Reflective'
    gender: ['female', 'male', 'non-binary'], // Default: varies by endpoint
    age_group: ['18-25', '26-35', '36-45', '46-55', '55+'], // Default: varies by endpoint
    voice_style: ['female', 'male'], // For non-binary users only - chooses voice/avatar style since blog avatars only support male/female
    visual_style: [
        'Studio Ghibli',    // Animated, magical style
        'Pixar',           // 3D animated style  
        'Anime',           // Japanese animation style
        'Watercolor',      // Artistic watercolor style
        'Cyberpunk',       // Futuristic sci-fi style
        'Realistic',       // Photorealistic style
        'blog-female',     // Female avatar for blog content
        'blog-male',        // Male avatar for blog content
        'blog-nonbinary'   // Non-binary avatar for blog content
    ]
};

// Example response structure
const EXAMPLE_RESPONSE = {
    job_id: "job_20241210_123456_abc123",
    video: "/path/to/final_narrated_video.mp4",
    original_text: "Your input text...",
    generated_text: "AI-generated narration...",
    key_phrases: [
        "A positive scene showing...",
        "Another scene depicting..."
    ],
    generated_videos: 3,
    video_duration: 15.2,
    processing_time: 45.7,
    success_rate: "100.0%",
    job_folder: "/path/to/job/folder",
    gender: "female",
    age_group: "26-35", 
    visual_style: "Studio Ghibli",
    mode: "ASYNC"
};

console.log('📚 Frontend integration examples loaded!');
console.log('📖 Check the console for API parameter reference and example responses.'); 