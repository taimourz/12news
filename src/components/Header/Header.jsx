import "./Header.css"

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



export default function Header({isLoadingArchive, archiveError, archiveDate }){
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
            <img src="/images/logo.png" alt="Dawn logo" height="50" width="225" />
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


