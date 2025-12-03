import "./Header.css"
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
  'HOME',
  'LATEST',
  'GAZA SIEGE',
  'PAKISTAN',
  'OPINION',
  'BUSINESS',
  'IMAGE',
  'PRISM',
  'WORLD',
  'SPORTS',
  'BREATHE',
  'MAGAZINES',
  'TECH',
  'VIDEOS',
  'POPULAR',
  'ARCHIVE',
  'FLOOD DONATIONS',
]



export default function Header(){
     const { isLoadingArchive } = useData();
     const { archiveDate } = useData();
     const { archiveError } = useData();

    
    console.log("Loading:", isLoadingArchive);
    console.log("Error:", archiveError);     

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
            <img src={`${import.meta.env.BASE_URL}images/logo.png`} alt="Dawn logo" height="50" width="225" />
            <p>
                <b>EPAPER </b>
                <span>| September 09, 2025</span>
            </p>
            </div>
            <ul className="otherLinks">
            {secondaryNavLinks.map((link) => (
                <li key={link}>
                <a href="#">{link}</a>
                </li>
            ))}
            </ul>
        </nav>

        <section className="status-bar">
            {isLoadingArchive && <p className="status-message">Loading archive&hellip;</p>}
            {archiveError && <p className="status-message status-error">{archiveError}</p>}
            {!isLoadingArchive && !archiveError && archiveDate && (
            <p className="status-message">
                Showing Dawn archive for <strong>{archiveDate}</strong>
            </p>
            )}
        </section>
        </div>
    )
}


