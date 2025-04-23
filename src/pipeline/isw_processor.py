import pandas as pd
import os
import re
import pickle
import ftfy
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from src.data_receiver.isw_receiver import ISWDataCollector


def get_and_process_isw_reports(target_date, db_handler):
    isw_collector = ISWDataCollector()
    isw_data = isw_collector.collect_data(target_date, target_date)
    db_handler.insert_isw_report(isw_data)
    
    isw_data = db_handler.get_isw_reports(daily_fetcher=True)
    
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    custom_stops = {
        # report metadata
        'isw', 'report', 'assessment', 'update', 'backgrounder', 'pm', 'est',
        'eet', 'local', 'time', 'et', 'key', 'takeaway', 'item', 'watch',
        'click', 'map', 'interactive', 'see', 'figure', 'source', 'url', 'http',
        'https', 'www', 'published', 'updated', 'accessed', 'twitter', 'telegram',
        'note', 'isws', 'daily', 'reference', 'statement', 'backgrounder',
    
        # generic time references
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december', 'monday', 'tuesday',
        'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'day', 'week',
        'month', 'year', 'hour', 'date', 'recent', 'recently', 'past', 'future',
    
        # generic verbs
        'include', 'including', 'also', 'may', 'provide', 'provides', 'provided',
        'providing', 'conduct', 'conducts', 'conducted', 'conducting',
        'continue', 'continues', 'continued', 'continuing', 'develop', 'develops',
        'developed', 'developing', 'indicate', 'indicates', 'indicated',
        'indicating', 'use', 'using', 'used', 'state', 'stated', 'claim', 'claimed',
        'assess', 'assessed',
    
        # generic nouns
        'area', 'effort', 'system', 'process', 'part', 'level', 'type', 'way',
        'situation', 'presence', 'resource', 'result', 'status', 'structure',
        'support', 'basis', 'center', 'change', 'condition', 'facility',
        'material', 'measure', 'member', 'number', 'order', 'percent',
        'security', 'series', 'service', 'term', 'people', 'city', 'region',
        'plan', 'objective', 'potential', 'capability', 'capacity',
    
        # generic connectives
        'however', 'unspecified', 'element', 'although', 'another', 'available',
        'following', 'former', 'main', 'need', 'public', 'publicly', 'still',
        'throughout', 'well', 'would', 'yet', 'ability', 'able', 'access',
    
        # authors
        'fredrick', 'kagan', 'george', 'barros', 'kateryna', 'katya',
        'stepanenko', 'karolina', 'hird', 'mason', 'clark', 'frederick',
        'grace', 'mappes', 'katherine', 'lawlor', 'frederick', 'layne',
        'philipson', 'angela', 'howard', 'riley', 'bailey', 'nicole',
        'wolkov', 'angelica', 'evans', 'christina', 'harward',
    }
    stop_words.update(custom_stops)
    
    def preprocess_text(text):
        text = ftfy.fix_text(text)
    
        # author line patterns
        text = re.sub(r"Russian Offensive Campaign Assessment,.*?\d{1,2}:\d{2}\s*(?:am|pm)\s*ET", "", text, flags=re.IGNORECASE)
        # common map links
        text = re.sub(r"Click here to see ISW’s interactive map.*?\.", "", text, flags=re.IGNORECASE)
        # bracketed numbers
        text = re.sub(r'\[\d+\]', '', text)
    
        text = text.lower()
    
        # punctuation
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s-\s|\s-$|^-', ' ', text)
    
        # tokenization
        tokens = word_tokenize(text)
    
        # lemmatization
        processed_tokens = [
            lemmatizer.lemmatize(word) for word in tokens
            if word not in stop_words and len(word) > 2 and not word.startswith('-') and not word.endswith('-')
        ]
    
        return ' '.join(processed_tokens)
    
    isw_data['processed_text'] = isw_data['content'].apply(preprocess_text)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..')) 
    artifacts_dir = os.path.join(project_root, 'artifacts') 

    vectorizer_path = os.path.join(artifacts_dir, 'tfidf_vectorizer_isw.pkl')
    svd_path = os.path.join(artifacts_dir, 'svd_reducer_isw.pkl')

    with open(vectorizer_path, 'rb') as f:
        tfidf_vectorizer = pickle.load(f)

    with open(svd_path, 'rb') as f:
        svd_reducer = pickle.load(f)

    tfidf_matrix_today = tfidf_vectorizer.transform(isw_data['processed_text'])
    tfidf_svd_matrix_today = svd_reducer.transform(tfidf_matrix_today)
    svd_feature_names = [f'svd_comp_{i+1}' for i in range(30)]
    df_tfidf_svd = pd.DataFrame(tfidf_svd_matrix_today, columns=svd_feature_names, index=isw_data.index)
    
    df_tfidf_svd['date'] = isw_data['date']
    date_col = df_tfidf_svd.pop('date') # make the 'date' column appear first
    df_tfidf_svd.insert(0, 'date', date_col)
    
    return df_tfidf_svd