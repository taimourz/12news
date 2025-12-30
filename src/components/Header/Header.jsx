import "./Header.css"
import { Link } from 'react-router-dom';
import { useData } from '../../context/DataContext.jsx';

const topNavLinks = [
  'EPAPER',
  'LIVE TV',
  'DAWNNEWS URDU',
  'IMAGES',
  'HERALD',
  'AURORA',
  'CITYFM89',
  'ADVERTISE',
  'EVENTS',
  'SUPPLEMENT',
  'CAREERS',
  'OBITUARIES',
]

const secondaryNavLinks = [
  { label: 'LATEST', path: '/front-page', sectionKey: 'front-page' },
  { label: 'NATIONAL', path: '/national', sectionKey: 'national' },
  { label: 'BACK PAGE', path: '/back-page', sectionKey: 'back-page' },
  { label: 'SPORTS', path: '/sports', sectionKey: 'sport' },
  { label: 'BUSINESS', path: '/business', sectionKey: 'business' },
  { label: 'LETTERS', path: '/letters', sectionKey: 'letters' },
  { label: 'OTHER VOICES', path: '/other-voices', sectionKey: 'other-voices' },
  { label: 'SUNDAY MAGAZINE', path: '/sunday-magazine', sectionKey: 'sunday-magazine' },
  { label: 'ICON', path: '/icon', sectionKey: 'icon' },
  { label: 'YOUNG WORLD', path: '/young-world', sectionKey: 'young-world' },
  { label: 'INTERNATIONAL', path: '/international', sectionKey: 'international' },
  { label: 'EDITORIAL', path: '/editorial', sectionKey: 'editorial' },
  { label: 'BUSINESS FINANCE', path: '/business-finance', sectionKey: 'business-finance' },
]

function formatArchiveDate(dateString) {
  if (!dateString) return '';
  try {
    const date = new Date(dateString + 'T00:00:00');
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: '2-digit',
    }).format(date);
  } catch (e) {
    console.error('Error formatting date:', e);
    return dateString;
  }
}

export default function Header(){
  const { isLoadingArchive, archiveDate, archiveError, sections, isFallbackData } = useData();
   
    
  console.log("Loading:", isLoadingArchive);
  console.log("Error:", archiveError);
  console.log("Archive Date:", archiveDate);
  
  const availableLinks = secondaryNavLinks.filter(link => {
    const stories = sections[link.sectionKey];
    return stories && stories.length > 0;
  });
  const formattedDate = formatArchiveDate(archiveDate);
  
  return(
    <div>
      <nav className="navbar">
        <ul className="links">
          {topNavLinks.map((link) => (
            <li key={link}>
              <a href="#">{link}</a>
            </li>
          ))}
        </ul>
        <div className="brand">
          <Link to="/">
            <img src={`${import.meta.env.BASE_URL}images/logo.png`} alt="Dawn logo" height="50" width="225" />
          </Link>
          <p>
            <b>EPAPER </b>
            <span>| {formattedDate || 'Loading...'}</span>
          </p>
        </div>
        <ul className="otherLinks">
          {isLoadingArchive ? (
            <li><span>Loading sections...</span></li>
          ) : (
            availableLinks.map((link) => (
              <li key={link.label}>
                <Link to={link.path}>{link.label}</Link>
              </li>
            ))
          )}
        </ul>
      </nav>
      <section className="status-bar">
        {isLoadingArchive ? (
          <p className="status-message">Loading archive&hellip;</p>
        ) : archiveError ? (
          <p className="status-message status-error">{archiveError}</p>
        ) : archiveDate ? (
          isFallbackData ? (
            <p className="status-message">
              Showing Dawn archive for <strong>{formattedDate}</strong> ( fallback data - scraping is currently disabled )
            </p>
          ) : (
            <p className="status-message">
              Showing Dawn archive for <strong>{formattedDate}</strong>
            </p>
          )
        ) : null}
      </section>
    </div>
  )
}