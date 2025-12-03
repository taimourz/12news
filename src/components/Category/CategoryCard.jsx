import { useData } from '../../context/DataContext.jsx';
import NewsCard from '../NewsCard/NewsCard.jsx';

export default function CategoryCard({ category }) {


    const { 
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
        isLoadingArchive
    } = useData();

    if (isLoadingArchive) { 
        return <div>Loading...</div>;
    }

    const categoryFunctions = {
        'sport': getSportStories,
        'front-page': getFrontPageStories,
        'national': getNationalStories,
        'back-page': getBackPageStories,
        'other-voices': getOtherVoicesStories,
        'letters': getLettersStories,
        'books-authors': getBooksAuthorsStories,
        'business-finance': getBusinessFinanceStories,
        'sunday-magazine': getSundayMagzineStories,
        'icon': getIconStories
    };

    const categoryNames = {
        'sport': 'Sports',
        'front-page': 'Front Page',
        'national': 'National',
        'back-page': 'Back Page',
        'other-voices': 'Other Voices',
        'letters': 'Letters',
        'books-authors': 'Books & Authors',
        'business-finance': 'Business & Finance',
        'sunday-magazine': 'Sunday Magazine',
        'icon': 'Icon'
    };


    if (isLoadingArchive) { 
        return <div style={{textAlign: 'center', padding: '40px'}}>Loading...</div>;
    }

    if (category === 'all' || category === 'front-page') {
        return (
            <div className="news-grid">
                <NewsCard newsStories={getFrontPageStories()} storyType="" featured={true} />
                <NewsCard newsStories={getNationalStories()} storyType="" />
                <NewsCard newsStories={getSportStories()} storyType="" />
                <NewsCard newsStories={getBusinessFinanceStories()} storyType="PRISM" />
                <NewsCard newsStories={getBackPageStories()} storyType="" />
            </div>
        );
    }

    const stories = categoryFunctions[category] ? categoryFunctions[category]() : [];

    return (
        <div className="news-grid">
            <NewsCard newsStories={stories} storyType="" />
        </div>
    );
}