import { useEffect, useMemo, useState } from 'react'
import  Header  from './components/Header/Header.jsx'
import  Footer  from './components/Footer/Footer.jsx'
import  Frontpage from './components/Frontpage/Frontpage.jsx'



function App() {
  const [archive, setArchive] = useState(null)
  const [isLoadingArchive, setIsLoadingArchive] = useState(true)
  const [archiveError, setArchiveError] = useState(null)
  

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
  const heroArticle = frontPageArticles[0] ?? null;
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

      <Frontpage 
        heroArticle={heroArticle}
        relatedFrontPage={relatedFrontPage}
      />

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

      <Footer/>

    </div>
  )
}

export default App
