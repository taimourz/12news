import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DataProvider } from './context/DataContext.jsx';
import Header from './components/Header/Header.jsx';
import Footer from './components/Footer/Footer.jsx';
import CategoryCard from './components/Category/CategoryCard.jsx';

function App() {
  return (
    <BrowserRouter>
      <DataProvider>
        <div className="app-shell">
          <Header/>
          <Routes>

            <Route path="*" element={<CategoryCard category="front-page" />} />
            <Route path="/front-page" element={<CategoryCard category="front-page" />} />
          </Routes>

          <Footer />

        </div>
      </DataProvider>
    </BrowserRouter>
  );
}

export default App;
