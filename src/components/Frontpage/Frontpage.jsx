import { useState } from 'react'
import "./Frontpage.css"



export default function Frontpage({heroArticle, relatedFrontPage }){
  const [showMore, setShowMore] = useState(false)
    return(
        <div>

        <article className="mainOne">
          <p className="section-label">Front Page</p>
          {heroArticle ? (
            <>
              <h2>{heroArticle.title}</h2>
              {heroArticle.imageUrl && (
                <img src={heroArticle.imageUrl} alt={heroArticle.title} width="300" />
              )}
              {relatedFrontPage.length > 0 && (
                <>
                  <p>More from the front page</p>
                  <ul>
                    {relatedFrontPage.map((story) => (
                      <li key={story.title}>
                        <a href={story.url} target="_blank" rel="noreferrer">
                          {story.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </>
              )}
              {heroArticle.summary && (
                <p>
                  {showMore ? heroArticle.summary : `${heroArticle.summary.slice(0, 160)}...`}
                  {heroArticle.summary.length > 160 && (
                    <button
                      type="button"
                      className="link-button"
                      onClick={() => setShowMore((prev) => !prev)}
                    >
                      {showMore ? 'read less' : 'read more'}
                    </button>
                  )}
                  <a className="link-button" href={heroArticle.url} target="_blank" rel="noreferrer">
                    Read full story ↗
                  </a>
                </p>
              )}
            </>
          ) : (
            <p className="status-message">No front-page articles available.</p>
          )}
        </article>

        </div>
    )
}


