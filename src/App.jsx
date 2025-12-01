import { useEffect, useState } from 'react'
import  Header  from './components/Header/Header.jsx'
import  Footer  from './components/Footer/Footer.jsx'
import  NewsCard from './components/NewsCard/NewsCard.jsx'


function App() {
  const [archive, setArchive] = useState(null)
  const [isLoadingArchive, setIsLoadingArchive] = useState(true)
  const [archiveError, setArchiveError] = useState(null)

  const API_KEY = import.meta.env.VITE_TAIMOUR_API_KEY;

  useEffect(() => {
    const loadArchive = async () => {
      try {
        const response = await fetch('https://taimourz-dawnnews12yearsago.hf.space/api/today', {
        // const response = await fetch('http://localhost:8000/api/today', {          
          headers: {
            'Cache-Control': 'no-cache',
            'x-api-key': API_KEY
          }
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
  const mustReadStories = sections['national'] ?? []
  const buzzStories = sections['business'] ?? []
  const backPageStories = sections['back-page'] ?? []
  const editorialStories = sections['editorial'] ?? []
  const sportStories = sections['sport'] ?? []
  const otherVoicesStories = sections['other-voices'] ?? []
  const letterStories = sections['letters'] ?? []
  const booksStories = sections['books-authors'] ?? []
  const bfinanceStories = sections['business-finance'] ?? []
  const youngWorldStories = sections['young-world'] ?? []
  const sundayMagzineStories = sections['sunday-magzine'] ?? []
  const iconStories = sections['icon'] ?? []

  return (
    <div className="app-shell">

    <Header 
      isLoadingArchive={isLoadingArchive}
      archiveError={archiveError}
      archiveDate={archive?.date}
    />
      <main>
        <NewsCard
          newsStories={frontPageArticles}
          storyType={"Front Page"}
        />
        <NewsCard
          newsStories={mustReadStories}
          storyType={"National Highlights"}
        />
        <NewsCard
          newsStories={buzzStories}
          storyType={"Business Briefing"}
        />
        <NewsCard
          newsStories={backPageStories}
          storyType="Back Page"
        />
        <NewsCard
          newsStories={editorialStories}
          storyType="Editorial"
        />
        <NewsCard
          newsStories={sportStories}
          storyType="Sports"
        />
        <NewsCard
          newsStories={otherVoicesStories}
          storyType="Other Voices Stories"
        />
        <NewsCard
          newsStories={letterStories}
          storyType="Letters to the Editor"
        />
        <NewsCard
          newsStories={booksStories}
          storyType="Books"
        />
        <NewsCard
          newsStories={bfinanceStories}
          storyType="Business Finance"
        />
        <NewsCard
          newsStories={youngWorldStories}
          storyType="Young World Sports"
        />
        <NewsCard
          newsStories={sundayMagzineStories}
          storyType="Sunday Magzine"
        />
        <NewsCard
          newsStories={iconStories}
          storyType="Icon"
        />
      </main>
      <Footer/>
    </div>
  )
}

export default App
