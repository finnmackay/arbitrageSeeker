"""
Market Matching Module
Uses semantic similarity to match markets across platforms
"""
import logging
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
import config

logger = logging.getLogger(__name__)


class MarketMatcher:
    """Matches markets across platforms using semantic similarity"""

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize the market matcher

        Args:
            model_name: SentenceTransformer model to use for embeddings
        """
        self.model_name = model_name
        self._model = None
        logger.info(f"MarketMatcher initialized with model: {model_name}")

    @property
    def model(self):
        """Lazy load the model to avoid slow startup"""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        return self._model

    def find_matches(
        self,
        polymarket_markets: List[Dict],
        kalshi_markets: List[Dict],
        similarity_threshold: float = None
    ) -> List[Dict]:
        """
        Find matching markets between Polymarket and Kalshi using semantic similarity

        Args:
            polymarket_markets: List of Polymarket market dicts with 'question' field
            kalshi_markets: List of Kalshi market dicts with 'title' and 'subtitle' fields
            similarity_threshold: Minimum similarity score (0-1). Defaults to config value.

        Returns:
            List[Dict]: Matched markets with similarity scores
        """
        threshold = similarity_threshold or config.SIMILARITY_THRESHOLD

        if not polymarket_markets:
            logger.warning("No Polymarket markets provided")
            return []

        if not kalshi_markets:
            logger.warning("No Kalshi markets provided")
            return []

        matches = []

        try:
            # Extract questions and titles
            poly_questions = []
            poly_market_map = []

            for p_market in polymarket_markets:
                if "question" in p_market:
                    poly_questions.append(p_market["question"])
                    poly_market_map.append(p_market)

            kalshi_titles = []
            kalshi_market_map = []

            for k_market in kalshi_markets:
                if "title" in k_market:
                    # Combine title and subtitle for better matching
                    full_title = k_market["title"]
                    if "subtitle" in k_market and k_market["subtitle"]:
                        full_title += " " + k_market["subtitle"]

                    kalshi_titles.append(full_title)
                    kalshi_market_map.append(k_market)

            if not poly_questions or not kalshi_titles:
                logger.warning("No valid questions/titles found after filtering")
                return []

            logger.info(
                f"Encoding {len(poly_questions)} Polymarket questions and "
                f"{len(kalshi_titles)} Kalshi titles"
            )

            # Encode all questions and titles
            poly_embeddings = self.model.encode(poly_questions, convert_to_tensor=True)
            kalshi_embeddings = self.model.encode(kalshi_titles, convert_to_tensor=True)

            # Compute pairwise cosine similarities
            similarities = util.cos_sim(poly_embeddings, kalshi_embeddings)

            # Find best match for each Polymarket question
            for i, p_market in enumerate(poly_market_map):
                # Get similarity scores for current Polymarket question
                similarity_scores = similarities[i].tolist()

                # Find best matching Kalshi market
                best_match_index = max(
                    range(len(similarity_scores)),
                    key=lambda j: similarity_scores[j]
                )
                best_match_score = similarity_scores[best_match_index]

                # Only add if meets threshold
                if best_match_score >= threshold:
                    k_market = kalshi_market_map[best_match_index]

                    matches.append({
                        "polymarket_question": p_market["question"],
                        "kalshi_title": k_market["title"],
                        "polymarket_id": p_market.get("condition_id"),
                        "kalshi_ticker": k_market.get("ticker"),
                        "similarity_score": float(best_match_score)
                    })

            logger.info(
                f"Found {len(matches)} matches with similarity >= {threshold:.2f}"
            )

        except Exception as e:
            logger.error(f"Error during market matching: {e}")
            raise

        return matches

    def validate_match(
        self,
        poly_question: str,
        kalshi_title: str,
        threshold: float = None
    ) -> float:
        """
        Validate a single match by computing similarity score

        Args:
            poly_question: Polymarket question text
            kalshi_title: Kalshi market title
            threshold: Optional threshold to check against

        Returns:
            float: Similarity score (0-1)
        """
        threshold = threshold or config.SIMILARITY_THRESHOLD

        try:
            embeddings = self.model.encode(
                [poly_question, kalshi_title],
                convert_to_tensor=True
            )

            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()

            logger.debug(
                f"Similarity score: {similarity:.4f} "
                f"(threshold: {threshold:.4f})"
            )

            return float(similarity)

        except Exception as e:
            logger.error(f"Error validating match: {e}")
            return 0.0
