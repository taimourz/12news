import { useState } from 'react';

export default function NewsCard({ newsStories, storyType, featured = false }) {
    const [failedImages, setFailedImages] = useState(new Set());
    
    const handleImageError = (storyTitle) => {
        setFailedImages(prev => new Set([...prev, storyTitle]));
    };
    
    return (
        <aside className="mainTwo">
            {storyType && <p className="section-label">{storyType}</p>}
            
            {newsStories.length === 0 && (
                <p className="status-message">No {storyType} stories right now.</p>
            )}
            
            {newsStories.slice(0, featured ? 3 : 5).map((story, index) => (
                <div 
                    key={story.title + index} 
                    className={`must-read-card ${index === 0 && featured ? 'featured' : ''}`}
                >
                    {story.imageUrl && !failedImages.has(story.title) && (
                        <img 
                            src={story.imageUrl} 
                            alt={story.title}
                            onError={() => handleImageError(story.title)}
                        />
                    )}
                    <h4>
                        <a href={story.url}>{story.title}</a>
                    </h4>
                    {story.summary && (
                        <p className="story-summary">{story.summary}</p>
                    )}
                    {story.author && (
                        <p className="story-meta">{story.author}</p>
                    )}
                </div>
            ))}
        </aside>
    );
}