"""
Service module that processes user feedback on AI-generated responses and implements
reinforcement learning to improve response quality over time. This module analyzes
feedback patterns, identifies successful and unsuccessful response strategies, and
updates the response generation parameters accordingly.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
import collections

import numpy as np  # version 1.24.0+
try:
    import ray  # version 2.5.0+
    import ray.rllib  # version 2.5.0+
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False

from ..core.logging import get_logger
from ..core.config import feedback_settings
from ..db.session import get_db, get_async_db
from ..models.feedback import Feedback
from ..models.query import Query
from ..schemas.feedback import FeedbackStats
from ..crud.crud_feedback import feedback
from ..crud.crud_query import crud_query
from .llm_service import LLMService

# Initialize logger
logger = get_logger(__name__)

# Global state
last_update_time = datetime.min
model_parameters = {}


class RLModel:
    """Reinforcement learning model for improving response generation."""
    
    def __init__(self, learning_rate: float):
        """
        Initializes the reinforcement learning model.
        
        Args:
            learning_rate: Learning rate for the model
        """
        self.learning_rate = learning_rate
        self.parameters = {
            "prompt_adjustments": {},
            "context_selection": {
                "relevance_threshold": 0.7,
                "max_chunks": 5
            },
            "response_patterns": {
                "positive": [],
                "negative": []
            }
        }
        self._algorithm = None
        
        # Try to set up Ray RLlib algorithm if available
        if RAY_AVAILABLE:
            try:
                from ray.rllib.algorithms.ppo import PPOConfig
                
                # Initialize Ray if not already initialized
                if not ray.is_initialized():
                    ray.init(ignore_reinit_error=True)
                
                # Create a simple config for PPO
                config = (
                    PPOConfig()
                    .environment("CartPole-v1")  # Placeholder environment
                    .rollouts(num_rollout_workers=0)
                    .resources(num_gpus=0)
                    .training(lr=learning_rate)
                )
                
                # Build algorithm
                self._algorithm = config.build()
                logger.info("Ray RLlib algorithm initialized")
            except Exception as e:
                logger.warning(f"Ray RLlib could not be initialized: {e}")
                logger.info("Using simplified supervised learning approach")
    
    def train(self, examples: List[dict]) -> dict:
        """
        Trains the RL model on feedback examples.
        
        Args:
            examples: List of learning examples with query, context, response, and rating
            
        Returns:
            Updated model parameters
        """
        if len(examples) == 0:
            return self.parameters
        
        # Separate examples by rating
        positive_examples = [ex for ex in examples if ex.get("rating", 0) >= 4]
        negative_examples = [ex for ex in examples if ex.get("rating", 0) <= 2]
        
        # If we have Ray RLlib available, use it for training
        if RAY_AVAILABLE and self._algorithm is not None:
            try:
                # This is a simplified placeholder for actual RL training
                # In a real implementation, we would need to define a proper environment,
                # observation and action spaces, reward function, etc.
                for _ in range(10):  # Simple training loop
                    self._algorithm.train()
                
                # Extract learned parameters (placeholder)
                trained_params = self._algorithm.get_policy().get_weights()
                
                # Update our parameters based on trained model
                # This is a simplification; in reality, we would map the trained
                # parameters to our model parameters in a meaningful way
                logger.info("Updated parameters using Ray RLlib")
            except Exception as e:
                logger.error(f"Error in RL training: {e}")
                logger.info("Falling back to simplified approach")
        
        # Simplified supervised learning approach
        # We'll analyze patterns in positive and negative examples
        
        # Extract patterns from positive examples
        if positive_examples:
            # Identify common patterns in successful responses
            response_patterns = self._extract_patterns([ex["response"] for ex in positive_examples])
            self.parameters["response_patterns"]["positive"] = response_patterns
            
            # Analyze context usage
            context_relevance = self._analyze_context_usage(positive_examples)
            if context_relevance:
                self.parameters["context_selection"]["relevance_threshold"] = context_relevance
            
            # Update prompt adjustments
            self.parameters["prompt_adjustments"] = self._derive_prompt_adjustments(positive_examples)
        
        # Learn from negative examples
        if negative_examples:
            # Identify patterns to avoid
            negative_patterns = self._extract_patterns([ex["response"] for ex in negative_examples])
            self.parameters["response_patterns"]["negative"] = negative_patterns
        
        logger.info(f"Updated model parameters based on {len(examples)} examples")
        return self.parameters
    
    def predict(self, prompt: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predicts improvements for a given prompt based on learned parameters.
        
        Args:
            prompt: The base prompt messages
            
        Returns:
            Improved prompt messages
        """
        if not prompt:
            return prompt
        
        improved_prompt = prompt.copy()
        
        # Apply learned adjustments to system message
        if prompt[0]["role"] == "system" and self.parameters["prompt_adjustments"]:
            system_content = prompt[0]["content"]
            
            # Apply adjustments based on learned parameters
            for pattern, replacement in self.parameters["prompt_adjustments"].items():
                if pattern in system_content:
                    system_content = system_content.replace(pattern, replacement)
            
            # Add suggestions for response patterns to include
            positive_patterns = self.parameters["response_patterns"]["positive"]
            if positive_patterns:
                patterns_text = "\n".join([f"- {pattern}" for pattern in positive_patterns[:3]])
                system_content += f"\n\nTry to include these elements in your response:\n{patterns_text}"
            
            # Add suggestions for response patterns to avoid
            negative_patterns = self.parameters["response_patterns"]["negative"]
            if negative_patterns:
                patterns_text = "\n".join([f"- {pattern}" for pattern in negative_patterns[:3]])
                system_content += f"\n\nAvoid these elements in your response:\n{patterns_text}"
            
            improved_prompt[0]["content"] = system_content
        
        # Optimize context selection if user prompt contains context
        if len(prompt) > 1 and prompt[1]["role"] == "user" and "Context:" in prompt[1]["content"]:
            user_content = prompt[1]["content"]
            
            # Apply relevance threshold for context selection
            # This is a simplified placeholder - in a real implementation,
            # we would actually filter context based on relevance scores
            relevance_threshold = self.parameters["context_selection"]["relevance_threshold"]
            max_chunks = self.parameters["context_selection"]["max_chunks"]
            
            improved_prompt[1]["content"] = user_content
        
        return improved_prompt
    
    def save_model(self, path: str) -> bool:
        """
        Saves the current model parameters to a file.
        
        Args:
            path: File path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, 'w') as f:
                json.dump(self.parameters, f, indent=2)
            logger.info(f"Model parameters saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, path: str) -> bool:
        """
        Loads model parameters from a file.
        
        Args:
            path: File path to load the model from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, 'r') as f:
                loaded_params = json.load(f)
            self.parameters.update(loaded_params)
            logger.info(f"Model parameters loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def _extract_patterns(self, texts: List[str]) -> List[str]:
        """
        Extracts common patterns from a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of common patterns
        """
        # This is a simplified implementation
        # In a real system, we would use NLP techniques like:
        # - N-gram analysis
        # - Named entity recognition
        # - Part-of-speech patterns
        # - Topic modeling
        
        patterns = []
        
        # Simple pattern: look for phrases that appear in multiple texts
        common_phrases = []
        for text in texts:
            # Split into sentences
            sentences = text.split('. ')
            for sentence in sentences:
                if len(sentence) > 20 and sentence not in common_phrases:
                    # Check if similar sentence appears in other texts
                    if any(sentence in other_text for other_text in texts if other_text != text):
                        common_phrases.append(sentence)
        
        # Take the top 5 common phrases as patterns
        patterns = common_phrases[:5]
        
        return patterns
    
    def _analyze_context_usage(self, examples: List[dict]) -> float:
        """
        Analyzes how context is used in successful responses.
        
        Args:
            examples: List of examples with context and response
            
        Returns:
            Optimal relevance threshold value
        """
        # This is a simplified implementation
        # In a real system, we would analyze:
        # - How much of the context was used in the response
        # - Which context chunks were most useful
        # - Correlation between context relevance scores and response quality
        
        # Default relevance threshold
        threshold = 0.7
        
        # If we have enough examples, we could adjust the threshold
        if len(examples) >= 10:
            # This would be based on actual analysis in a real implementation
            # For now, we'll just return a slightly adjusted value
            threshold = 0.65 + (0.1 * (sum(ex.get("rating", 0) for ex in examples) / (5 * len(examples))))
        
        return threshold
    
    def _derive_prompt_adjustments(self, examples: List[dict]) -> Dict[str, str]:
        """
        Derives prompt adjustments based on successful examples.
        
        Args:
            examples: List of examples with prompts and successful responses
            
        Returns:
            Dictionary of pattern-replacement pairs for prompt adjustment
        """
        # This is a simplified implementation
        # In a real system, we would analyze prompts that led to good responses
        # and identify patterns to adjust
        
        adjustments = {}
        
        # For now, we'll just add a few generic improvements
        adjustments["Answer the question"] = "Answer the question clearly and concisely"
        adjustments["Use information from the provided context"] = "Use information from the provided context, citing specific documents"
        
        return adjustments


class FeedbackProcessor:
    """
    Service class that processes user feedback and implements reinforcement learning
    to improve response quality.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initializes the FeedbackProcessor with default parameters.
        
        Args:
            llm_service: The LLM service for prompt formatting and response generation
        """
        self._model_parameters = {}
        self._last_update_time = datetime.min
        self._llm_service = llm_service
        logger.info("FeedbackProcessor initialized")
    
    def analyze_feedback(self, feedback_data: List[Feedback]) -> dict:
        """
        Analyzes feedback data to identify patterns and trends.
        
        Args:
            feedback_data: List of feedback objects
            
        Returns:
            Analysis results including patterns and trends
        """
        if not feedback_data:
            return {"error": "No feedback data provided"}
        
        # Group feedback by rating category
        positive_feedback = [f for f in feedback_data if f.is_positive()]
        negative_feedback = [f for f in feedback_data if f.is_negative()]
        neutral_feedback = [f for f in feedback_data if not f.is_positive() and not f.is_negative()]
        
        # Calculate basic statistics
        total_feedback = len(feedback_data)
        avg_rating = sum(f.rating for f in feedback_data) / total_feedback if total_feedback > 0 else 0
        
        # Create rating distribution
        rating_distribution = {i: 0 for i in range(1, 6)}
        for f in feedback_data:
            rating_distribution[f.rating] += 1
        
        # Extract common themes from comments
        positive_themes = self._extract_themes([f.comments for f in positive_feedback if f.comments])
        negative_themes = self._extract_themes([f.comments for f in negative_feedback if f.comments])
        
        # Create analysis result
        analysis = {
            "statistics": {
                "total_feedback": total_feedback,
                "average_rating": avg_rating,
                "rating_distribution": rating_distribution,
                "positive_percentage": len(positive_feedback) / total_feedback * 100 if total_feedback > 0 else 0,
                "negative_percentage": len(negative_feedback) / total_feedback * 100 if total_feedback > 0 else 0,
                "neutral_percentage": len(neutral_feedback) / total_feedback * 100 if total_feedback > 0 else 0
            },
            "themes": {
                "positive": positive_themes,
                "negative": negative_themes
            }
        }
        
        return analysis
    
    def extract_learning_examples(self, feedback_data: List[Feedback]) -> List[dict]:
        """
        Extracts learning examples from feedback data for reinforcement learning.
        
        Args:
            feedback_data: List of feedback objects
            
        Returns:
            List of learning examples with query, context, response, and rating
        """
        examples = []
        
        with get_db() as db:
            for feedback_item in feedback_data:
                # Retrieve the associated query
                query = crud_query.get_with_feedback(db, feedback_item.query_id)
                if not query:
                    logger.warning(f"Query not found for feedback ID: {feedback_item.id}")
                    continue
                
                # Create learning example
                example = {
                    "feedback_id": str(feedback_item.id),
                    "query_id": str(query.id),
                    "query": query.query_text,
                    "response": query.response_text,
                    "context": query.context_documents,
                    "rating": feedback_item.rating,
                    "comments": feedback_item.comments
                }
                
                examples.append(example)
        
        logger.info(f"Extracted {len(examples)} learning examples")
        return examples
    
    def update_response_model(self, analysis_results: dict, learning_examples: List[dict]) -> dict:
        """
        Updates the response generation model based on feedback analysis.
        
        Args:
            analysis_results: Results from feedback analysis
            learning_examples: Learning examples extracted from feedback
            
        Returns:
            Updated model parameters
        """
        if not learning_examples:
            logger.warning("No learning examples provided for model update")
            return self._model_parameters
        
        # Create RL model with current parameters
        rl_model = RLModel(learning_rate=feedback_settings.LEARNING_RATE)
        
        # If we have existing parameters, load them
        if self._model_parameters:
            rl_model.parameters = self._model_parameters
        
        # Train the model on learning examples
        updated_parameters = rl_model.train(learning_examples)
        
        # Update our stored parameters
        self._model_parameters = updated_parameters
        
        logger.info("Response model updated based on feedback analysis")
        return self._model_parameters
    
    def process_feedback_batch(self) -> bool:
        """
        Processes a batch of feedback for reinforcement learning.
        
        Returns:
            True if processing was successful, False otherwise
        """
        # Check if RL is enabled
        if not feedback_settings.ENABLE_REINFORCEMENT_LEARNING:
            logger.info("Reinforcement learning is disabled in settings")
            return False
        
        # Check if enough time has passed since last update
        now = datetime.now()
        hours_since_update = (now - self._last_update_time).total_seconds() / 3600
        
        if hours_since_update < feedback_settings.RL_UPDATE_FREQUENCY_HOURS:
            logger.info(f"Not enough time has passed since last update. Hours since last update: {hours_since_update:.2f}")
            return False
        
        # Get feedback data
        with get_db() as db:
            # Get feedback since last update
            filter_params = None
            if self._last_update_time > datetime.min:
                # We would use a proper filter object here, but for simplicity:
                # Get all feedback for now
                pass
            
            # Retrieve feedback data
            feedback_data = feedback.get_filtered(db, filter_params, limit=feedback_settings.FEEDBACK_BATCH_SIZE)
            
            if len(feedback_data) < 10:  # Arbitrary minimum threshold
                logger.info(f"Insufficient feedback data for processing: {len(feedback_data)} items")
                return False
            
            # Analyze feedback
            analysis_results = self.analyze_feedback(feedback_data)
            
            # Extract learning examples
            learning_examples = self.extract_learning_examples(feedback_data)
            
            # Update response model
            updated_params = self.update_response_model(analysis_results, learning_examples)
            
            # Update last update time
            self._last_update_time = now
            
            logger.info(f"Processed {len(feedback_data)} feedback items for reinforcement learning")
            return True
    
    def should_update_model(self) -> bool:
        """
        Determines if the model should be updated based on time and available feedback.
        
        Returns:
            True if model should be updated, False otherwise
        """
        # Check if RL is enabled
        if not feedback_settings.ENABLE_REINFORCEMENT_LEARNING:
            return False
        
        # Check if enough time has passed since last update
        now = datetime.now()
        hours_since_update = (now - self._last_update_time).total_seconds() / 3600
        
        if hours_since_update < feedback_settings.RL_UPDATE_FREQUENCY_HOURS:
            return False
        
        # Check if we have enough feedback data
        with get_db() as db:
            stats = feedback.get_statistics(db)
            
            # Arbitrary threshold - we want at least 10 feedback items
            if stats.total_feedback < 10:
                return False
        
        return True
    
    def get_model_parameters(self) -> dict:
        """
        Retrieves current model parameters for response generation.
        
        Returns:
            Current model parameters
        """
        # If parameters are empty, return default
        if not self._model_parameters:
            return {
                "prompt_adjustments": {},
                "context_selection": {
                    "relevance_threshold": 0.7,
                    "max_chunks": 5
                },
                "response_patterns": {
                    "positive": [],
                    "negative": []
                }
            }
        
        return self._model_parameters.copy()
    
    def apply_feedback_to_prompt(self, query: str, context_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applies learned parameters to improve prompt formatting.
        
        Args:
            query: The user's query
            context_documents: List of context documents
            
        Returns:
            Improved prompt messages
        """
        # Get base prompt from LLM service
        base_prompt = self._llm_service.format_prompt(query, context_documents)
        
        # If we don't have learned parameters, return the base prompt
        if not self._model_parameters:
            return base_prompt
        
        # Create RL model with current parameters
        rl_model = RLModel(learning_rate=feedback_settings.LEARNING_RATE)
        rl_model.parameters = self._model_parameters
        
        # Apply learned improvements
        improved_prompt = rl_model.predict(base_prompt)
        
        return improved_prompt
    
    def schedule_feedback_processing(self) -> None:
        """
        Schedules periodic feedback processing for reinforcement learning.
        """
        if not feedback_settings.ENABLE_REINFORCEMENT_LEARNING:
            logger.info("Reinforcement learning is disabled, not scheduling feedback processing")
            return
        
        # This is a placeholder for actual scheduling logic
        # In a real application, this would use a task scheduler like Celery or APScheduler
        # For now, we'll just log that scheduling would happen
        logger.info(f"Would schedule feedback processing every {feedback_settings.RL_UPDATE_FREQUENCY_HOURS} hours")
        
        # Example of how this might be implemented with APScheduler:
        '''
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            self.process_feedback_batch, 
            'interval', 
            hours=feedback_settings.RL_UPDATE_FREQUENCY_HOURS
        )
        scheduler.start()
        '''
    
    def _extract_themes(self, comments: List[str]) -> List[str]:
        """
        Extracts common themes from feedback comments.
        
        Args:
            comments: List of feedback comment strings
            
        Returns:
            List of common themes
        """
        # This is a simplified implementation
        # In a real system, we would use NLP techniques
        
        # Count word frequencies
        word_counts = collections.Counter()
        for comment in comments:
            if comment:  # Ensure comment is not None
                # Simple tokenization by splitting on whitespace
                words = comment.lower().split()
                word_counts.update(words)
        
        # Remove common stopwords (simplified list)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'is', 'are', 'was', 'were'}
        for word in stopwords:
            if word in word_counts:
                del word_counts[word]
        
        # Get most common words
        common_words = [word for word, count in word_counts.most_common(10) if count > 1]
        
        return common_words


# Standalone functions that use FeedbackProcessor

def analyze_feedback(feedback_data: List[Feedback]) -> dict:
    """
    Analyzes feedback data to identify patterns and trends.
    
    Args:
        feedback_data: List of feedback objects
        
    Returns:
        Analysis results including patterns and trends
    """
    processor = FeedbackProcessor(LLMService())
    return processor.analyze_feedback(feedback_data)


def extract_learning_examples(feedback_data: List[Feedback]) -> List[dict]:
    """
    Extracts learning examples from feedback data for reinforcement learning.
    
    Args:
        feedback_data: List of feedback objects
        
    Returns:
        List of learning examples with query, context, response, and rating
    """
    processor = FeedbackProcessor(LLMService())
    return processor.extract_learning_examples(feedback_data)


def update_response_model(analysis_results: dict, learning_examples: List[dict]) -> dict:
    """
    Updates the response generation model based on feedback analysis.
    
    Args:
        analysis_results: Results from feedback analysis
        learning_examples: Learning examples extracted from feedback
        
    Returns:
        Updated model parameters
    """
    processor = FeedbackProcessor(LLMService())
    return processor.update_response_model(analysis_results, learning_examples)


def process_feedback_batch() -> bool:
    """
    Processes a batch of feedback for reinforcement learning.
    
    Returns:
        True if processing was successful, False otherwise
    """
    global last_update_time, model_parameters
    
    # Check if RL is enabled
    if not feedback_settings.ENABLE_REINFORCEMENT_LEARNING:
        logger.info("Reinforcement learning is disabled in settings")
        return False
    
    # Check if enough time has passed since last update
    now = datetime.now()
    hours_since_update = (now - last_update_time).total_seconds() / 3600
    
    if hours_since_update < feedback_settings.RL_UPDATE_FREQUENCY_HOURS:
        logger.info(f"Not enough time has passed since last update. Hours since last update: {hours_since_update:.2f}")
        return False
    
    # Get feedback data
    with get_db() as db:
        # Get feedback since last update
        filter_params = None
        if last_update_time > datetime.min:
            # We would use a proper filter object here, but for simplicity:
            # Get all feedback for now
            pass
        
        # Retrieve feedback data
        feedback_data = feedback.get_filtered(db, filter_params, limit=feedback_settings.FEEDBACK_BATCH_SIZE)
        
        if len(feedback_data) < 10:  # Arbitrary minimum threshold
            logger.info(f"Insufficient feedback data for processing: {len(feedback_data)} items")
            return False
        
        # Process feedback using FeedbackProcessor
        processor = FeedbackProcessor(LLMService())
        
        # Analyze feedback
        analysis_results = processor.analyze_feedback(feedback_data)
        
        # Extract learning examples
        learning_examples = processor.extract_learning_examples(feedback_data)
        
        # Update response model
        model_parameters = processor.update_response_model(analysis_results, learning_examples)
        
        # Update last update time
        last_update_time = now
        
        logger.info(f"Processed {len(feedback_data)} feedback items for reinforcement learning")
        return True


def should_update_model() -> bool:
    """
    Determines if the model should be updated based on time and available feedback.
    
    Returns:
        True if model should be updated, False otherwise
    """
    # Check if RL is enabled
    if not feedback_settings.ENABLE_REINFORCEMENT_LEARNING:
        return False
    
    # Check if enough time has passed since last update
    now = datetime.now()
    hours_since_update = (now - last_update_time).total_seconds() / 3600
    
    if hours_since_update < feedback_settings.RL_UPDATE_FREQUENCY_HOURS:
        return False
    
    # Check if we have enough feedback data
    with get_db() as db:
        stats = feedback.get_statistics(db)
        
        # Arbitrary threshold - we want at least 10 feedback items
        if stats.total_feedback < 10:
            return False
    
    return True


def get_model_parameters() -> dict:
    """
    Retrieves current model parameters for response generation.
    
    Returns:
        Current model parameters
    """
    global model_parameters
    
    # If model_parameters is empty, return default
    if not model_parameters:
        model_parameters = {
            "prompt_adjustments": {},
            "context_selection": {
                "relevance_threshold": 0.7,
                "max_chunks": 5
            },
            "response_patterns": {
                "positive": [],
                "negative": []
            }
        }
    
    return model_parameters


def apply_feedback_to_prompt(query: str, context_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applies learned parameters to improve prompt formatting.
    
    Args:
        query: The user's query
        context_documents: List of context documents
        
    Returns:
        Improved prompt messages
    """
    llm_service = LLMService()
    base_prompt = llm_service.format_prompt(query, context_documents)
    
    # If we don't have learned parameters, return the base prompt
    if not model_parameters:
        return base_prompt
    
    # Create RL model with current parameters
    rl_model = RLModel(learning_rate=feedback_settings.LEARNING_RATE)
    rl_model.parameters = model_parameters
    
    # Apply learned improvements
    improved_prompt = rl_model.predict(base_prompt)
    
    return improved_prompt


def schedule_feedback_processing() -> None:
    """
    Schedules periodic feedback processing for reinforcement learning.
    """
    if not feedback_settings.ENABLE_REINFORCEMENT_LEARNING:
        logger.info("Reinforcement learning is disabled, not scheduling feedback processing")
        return
    
    # This is a placeholder for actual scheduling logic
    # In a real application, this would use a task scheduler like Celery or APScheduler
    logger.info(f"Would schedule feedback processing every {feedback_settings.RL_UPDATE_FREQUENCY_HOURS} hours")