import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN

class TopicModeler:
    """
    Groups articles into topic clusters using TF-IDF and DBSCAN.
    Fast, offline, and doesn't require predefined cluster counts (unlike KMeans).
    """
    
    @staticmethod
    def cluster_articles(articles: List[Dict[str, Any]], eps: float = 0.8, min_samples: int = 2) -> List[Dict[str, Any]]:
        if len(articles) < min_samples:
            return [{"topic_id": -1, "articles": articles, "keywords": []}]
            
        # Extract text (title + clean_text)
        texts = [f"{a.get('title', '')} {a.get('clean_text', '')}" for a in articles]
        
        # Vectorize
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        try:
            X = vectorizer.fit_transform(texts)
        except ValueError:
            # Vocabulary empty (e.g. all stop words)
            return [{"topic_id": -1, "articles": articles, "keywords": []}]
            
        # Cluster
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(X)
        
        feature_names = np.array(vectorizer.get_feature_names_out())
        
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = {"topic_id": int(label), "articles": [], "keywords": []}
            clusters[label]["articles"].append(articles[idx])
            
        # Extract top keywords for each non-noise cluster
        for label, cluster in clusters.items():
            if label == -1:
                cluster["keywords"] = ["unclassified_noise"]
                continue
                
            # Get tfidf mean for this cluster
            cluster_indices = [idx for idx, l in enumerate(labels) if l == label]
            cluster_tfidf = X[cluster_indices].mean(axis=0)
            
            # Sort by tfidf score
            top_indices = np.asarray(cluster_tfidf).argsort()[0][-5:][::-1]
            cluster["keywords"] = feature_names[top_indices].tolist()
            
        return list(clusters.values())
