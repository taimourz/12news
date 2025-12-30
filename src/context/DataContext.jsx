import { createContext, useContext, useState, useEffect } from 'react';

const DataContext = createContext();

export function DataProvider({ children }) {
  const [archive, setArchive] = useState(null)
  const [isLoadingArchive, setIsLoadingArchive] = useState(true)
  const [archiveError, setArchiveError] = useState(null)
  const [isFallbackData, setIsFallbackData] = useState(false)  
  const API_KEY = import.meta.env.VITE_TAIMOUR_API_KEY;  

  useEffect(() => {
  const loadArchive = async () => {
      try {
      const response = await fetch('https://taimourz-dawnnews.hf.space/api/v1/archive/today', {
      // const response = await fetch('http://localhost:8003/api/v1/archive/today', {
          headers: {
          'Cache-Control': 'no-cache',
          'x-api-key': API_KEY
          }
      })

      if (!response.ok) {
          throw new Error('Unable to load archive data')
      }
      const payload = await response.json()
      const isFallback = payload.date === "2013-12-28"
      setIsFallbackData(isFallback)
      setArchive(payload)
      } catch (err) {
      setArchiveError(err.message)
      } finally {
      setIsLoadingArchive(false)
      }
  }
  loadArchive()
  }, [])  
    const sections = archive?.sections || {};
    const archiveDate = archive?.date || null;
    const getFrontPageStories = () => sections["front-page"] || [];
    const getNationalStories = () => sections["national"] || [];
    const getBackPageStories = () => sections["back-page"] || [];
    const getSportStories = () => sections["sport"] || [];
    const getOtherVoicesStories = () => sections["other-voices"] || [];
    const getLettersStories = () => sections["letters"] || [];
    const getBooksAuthorsStories = () => sections["books-authors"] || [];
    const getBusinessStories = () => sections["business"] || [];
    const getSundayMagzineStories = () => sections["sunday-magazine"] || [];
    const getBusinessFinanceStories = () => sections["business-finance"] || [];  
    const getEditorialStories = () => sections["editorial"] || [];  
    const getInternationalStories = () => sections["international"] || [];  
    const getYoungWorldStories = () => sections["young-world"] || [];  
    const getIconStories = () => sections["icon"] || [];      
  return (
    <DataContext.Provider value={{
            sections,
            isLoadingArchive,
            archiveError,
            archiveDate,
            isFallbackData,
            getFrontPageStories,
            getNationalStories,
            getBackPageStories,
            getSportStories,
            getOtherVoicesStories,
            getLettersStories,
            getBooksAuthorsStories,
            getBusinessFinanceStories,
            getSundayMagzineStories,
            getIconStories,
            getYoungWorldStories,
            getInternationalStories,
            getEditorialStories,
            getBusinessStories
         }}>
      {children}
    </DataContext.Provider>
  );
}
export function useData() {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within DataProvider');
  }
  return context;
}