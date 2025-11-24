import { useEffect, useMemo, useState } from 'react'
import  Header  from './components/Header/Header.jsx'

const footerColumns = [
  [
    'CONTACT',
    'CONTRIBUTION GUIDELINES',
    'CODE OF ETHICS',
    'AI POLICY',
    'TERM OF USE',
    'PRIVACY',
    'COMMENT MODERATION',
  ],
  [
    'SUBSCRIBE TO NEWSPAPER',
    'REPRODUCTION COPYRIGHTS',
    'ADVERTISE ON DAWN.COM',
    'BRANDED CONTENT',
    'CAREERS',
    'OBITUARIES',
  ],
  ['PRAYER TIMING', 'STOCK/FOREX/GOLD', 'WEATHER'],
  ['DAWN', 'PRISM', 'IMAGES', 'SPECIAL REPORTS', 'AURORA', 'DAWN NEWS'],
  ['EOS/ICON/YOUNG WORLD', 'CITYFM89', 'HERALD', 'TEELI'],
]

function App() {
  const [archive, setArchive] = useState(null)
  const [isLoadingArchive, setIsLoadingArchive] = useState(true)
  const [archiveError, setArchiveError] = useState(null)
  const [showMore, setShowMore] = useState(false)

  useEffect(() => {
    const loadArchive = async () => {
      try {
        const response = await fetch('/data/archive.json', {
          headers: { 'Cache-Control': 'no-cache' },
        })

        if (!response.ok) {
          throw new Error('Unable to load archive data')
        }

        const payload = await response.json()
        setArchive(payload)
      } catch (err) {
        setArchiveError(err.message)
      } finally {
        setIsLoadingArchive(false)
      }
    }

    loadArchive()
  }, [])

  const sections = archive?.sections ?? {}

  const frontPageArticles = sections['front-page'] ?? []
  const heroArticle = frontPageArticles[0]
  const relatedFrontPage = frontPageArticles.slice(1, 4)

  const mustReadStories = (sections.national ?? []).slice(0, 3)
  const buzzStories = (sections.business ?? []).slice(0, 8)

  const extendedSections = useMemo(
    () => [
      { key: 'back-page', label: 'Back Page', items: (sections['back-page'] ?? []).slice(0, 5) },
      { key: 'editorial', label: 'Editorial', items: (sections.editorial ?? []).slice(0, 5) },
    ],
    [sections],
  )

  return (
    <div className="app-shell">

    <Header 
      isLoadingArchive={isLoadingArchive}
      archiveError={archiveError}
      archiveDate={archive?.date}
    />


      <main>
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

        <aside className="mainTwo">
          <p className="section-label">National Highlights</p>
          {mustReadStories.length === 0 && (
            <p className="status-message">No national stories right now.</p>
          )}
          {mustReadStories.map((story) => (
            <div key={story.title} className="must-read-card">
              {story.imageUrl && <img src={story.imageUrl} alt={story.title} width="280" />}
              <h4>{story.title}</h4>
              {!story.imageUrl && <p className="story-summary">{story.summary}</p>}
            </div>
          ))}
          <hr />
        </aside>

        <section className="mainThree">
          <p className="section-label">Business Briefing</p>
          {buzzStories.length === 0 && (
            <p className="status-message">Business desk has no updates yet.</p>
          )}
          {buzzStories.map((story, index) => (
            <div key={story.title}>
              <div className="buzz-row">
                <div>
                  <h4>{story.title}</h4>
                  <p className="story-summary">{story.summary}</p>
                </div>
                {story.imageUrl && (
                  <img src={story.imageUrl} alt={story.title} width="80" height="80" />
                )}
              </div>
              {index < buzzStories.length - 1 && <hr />}
            </div>
          ))}
        </section>

        <section className="mainFour">

        </section>

        <section className="archive-section-grid">
          {extendedSections.map((section) => {
            if (section.items.length === 0) return null
            return (
              <div key={section.key} className="archive-section">
                <p className="section-label">{section.label}</p>
                <ul>
                  {section.items.map((item) => (
                    <li key={item.title}>
                      <a href={item.url} target="_blank" rel="noreferrer">
                        {item.title}
                      </a>
                      {item.summary && <p className="story-summary">{item.summary}</p>}
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </section>
      </main>

      <footer>
        <img src="/images/footerlogo.png" alt="Dawn footer logo" width="100" />
        <div className="footerlinks">
          {footerColumns.map((column, index) => (
            <div key={index}>
              <ul>
                {column.map((item) => (
                  <li key={item}>
                    <a href="#">{item}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="copyright">
          <p>Copyright © 2025, DAWN - Taimour Afzal</p>
        </div>
      </footer>
    </div>
  )
}

export default App
