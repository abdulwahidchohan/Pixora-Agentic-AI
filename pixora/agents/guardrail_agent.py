"""
Guardrail Agent for Pixora system.

Implements safety checks, content moderation, and policy enforcement
for image generation requests.
"""

import re
from typing import List, Dict, Any, Optional
from ..models import UserRequest, EnhancedPrompt
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GuardrailAgent:
    """
    Agent responsible for safety checks and content moderation.
    
    Performs:
    - Content policy validation
    - Safety checks
    - Rate limiting validation
    - User permission checks
    """
    
    def __init__(self):
        """Initialize the GuardrailAgent."""
        self.logger = logger
        self.blocked_keywords = self._load_blocked_keywords()
        self.safety_thresholds = self._load_safety_thresholds()
        
    def _load_blocked_keywords(self) -> List[str]:
        """Load blocked keywords from configuration."""
        return [
            "explicit", "nude", "violence", "gore", "hate", "discrimination",
            "illegal", "harmful", "dangerous", "weapon", "drug", "alcohol"
        ]
    
    def _load_safety_thresholds(self) -> Dict[str, float]:
        """Load safety thresholds for different categories."""
        return {
            "violence": 0.7,
            "sexual": 0.8,
            "hate": 0.9,
            "harassment": 0.8,
            "self_harm": 0.9,
            "shock": 0.7
        }
    
    async def validate_request(self, request: UserRequest) -> Dict[str, Any]:
        """
        Validate a user request against safety policies.
        
        Args:
            request: The user request to validate
            
        Returns:
            Dict containing validation results and any warnings
        """
        self.logger.info("Validating user request", user_id=request.user_id)
        
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "blocked_reasons": [],
            "safety_scores": {}
        }
        
        # Check prompt content
        prompt_validation = await self._validate_prompt(request.prompt)
        if not prompt_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["blocked_reasons"].extend(prompt_validation["blocked_reasons"])
        
        validation_result["warnings"].extend(prompt_validation["warnings"])
        
        # Check user permissions
        permission_check = await self._check_user_permissions(request.user_id)
        if not permission_check["has_permission"]:
            validation_result["is_valid"] = False
            validation_result["blocked_reasons"].append("Insufficient permissions")
        
        # Check rate limits
        rate_limit_check = await self._check_rate_limits(request.user_id)
        if not rate_limit_check["within_limits"]:
            validation_result["is_valid"] = False
            validation_result["blocked_reasons"].append("Rate limit exceeded")
        
        self.logger.info("Request validation completed", 
                        is_valid=validation_result["is_valid"],
                        warnings_count=len(validation_result["warnings"]),
                        blocked_reasons_count=len(validation_result["blocked_reasons"]))
        
        return validation_result
    
    async def _validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate prompt content for safety and policy compliance.
        
        Args:
            prompt: The prompt text to validate
            
        Returns:
            Dict containing validation results
        """
        result = {
            "is_valid": True,
            "warnings": [],
            "blocked_reasons": []
        }
        
        # Check for blocked keywords
        prompt_lower = prompt.lower()
        for keyword in self.blocked_keywords:
            if keyword in prompt_lower:
                result["warnings"].append(f"Potentially problematic keyword: {keyword}")
        
        # Check for excessive length
        if len(prompt) > 1000:
            result["warnings"].append("Prompt is very long, may affect generation quality")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\b(create|generate|make)\s+(a\s+)?(fake|false|counterfeit)',
            r'\b(impersonate|pretend\s+to\s+be)',
            r'\b(unauthorized|illegal|criminal)'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, prompt_lower):
                result["warnings"].append("Suspicious content pattern detected")
        
        # If too many warnings, consider blocking
        if len(result["warnings"]) > 3:
            result["is_valid"] = False
            result["blocked_reasons"].append("Too many safety warnings")
        
        return result
    
    async def _check_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has permission to generate images.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            Dict containing permission status
        """
        # TODO: Implement actual user permission checking
        # For now, allow all users
        return {
            "has_permission": True,
            "permission_level": "standard",
            "restrictions": []
        }
    
    async def _check_rate_limits(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user is within rate limits.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            Dict containing rate limit status
        """
        # TODO: Implement actual rate limiting
        # For now, allow all requests
        return {
            "within_limits": True,
            "requests_remaining": 100,
            "reset_time": None
        }
    
    async def apply_safety_filters(self, enhanced_prompt: EnhancedPrompt) -> EnhancedPrompt:
        """
        Apply safety filters to an enhanced prompt.
        
        Args:
            enhanced_prompt: The enhanced prompt to filter
            
        Returns:
            The filtered enhanced prompt
        """
        self.logger.info("Applying safety filters to enhanced prompt")
        
        # Apply content filtering
        filtered_prompt = enhanced_prompt.prompt
        for keyword in self.blocked_keywords:
            filtered_prompt = filtered_prompt.replace(keyword, f"[{keyword}]")
        
        # Create filtered enhanced prompt
        filtered_enhanced = EnhancedPrompt(
            prompt=filtered_prompt,
            style_preferences=enhanced_prompt.style_preferences,
            safety_level="filtered",
            original_prompt=enhanced_prompt.original_prompt
        )
        
        self.logger.info("Safety filters applied", 
                        original_length=len(enhanced_prompt.prompt),
                        filtered_length=len(filtered_prompt))
        
        return filtered_enhanced
    
    async def get_safety_report(self, request: UserRequest) -> Dict[str, Any]:
        """
        Generate a comprehensive safety report for a request.
        
        Args:
            request: The user request to analyze
            
        Returns:
            Dict containing safety analysis
        """
        self.logger.info("Generating safety report", user_id=request.user_id)
        
        # Perform comprehensive validation
        validation = await self.validate_request(request)
        
        # Generate safety scores
        safety_scores = await self._calculate_safety_scores(request.prompt)
        
        report = {
            "request_id": request.request_id,
            "user_id": request.user_id,
            "timestamp": request.timestamp,
            "overall_safety_score": sum(safety_scores.values()) / len(safety_scores),
            "safety_scores": safety_scores,
            "validation_result": validation,
            "recommendations": self._generate_safety_recommendations(validation, safety_scores)
        }
        
        self.logger.info("Safety report generated", 
                        overall_score=report["overall_safety_score"],
                        is_safe=validation["is_valid"])
        
        return report
    
    async def _calculate_safety_scores(self, prompt: str) -> Dict[str, float]:
        """
        Calculate safety scores for different categories.
        
        Args:
            prompt: The prompt to analyze
            
        Returns:
            Dict containing safety scores for each category
        """
        # TODO: Implement actual safety scoring using AI models
        # For now, return placeholder scores
        prompt_lower = prompt.lower()
        
        scores = {}
        for category, threshold in self.safety_thresholds.items():
            # Simple heuristic scoring based on keyword presence
            risk_keywords = {
                "violence": ["fight", "war", "blood", "weapon"],
                "sexual": ["nude", "explicit", "intimate"],
                "hate": ["hate", "discrimination", "racist"],
                "harassment": ["bully", "harass", "threaten"],
                "self_harm": ["suicide", "self-harm", "cut"],
                "shock": ["shock", "disturbing", "horror"]
            }
            
            if category in risk_keywords:
                risk_count = sum(1 for word in risk_keywords[category] if word in prompt_lower)
                scores[category] = max(0.1, 1.0 - (risk_count * 0.2))
            else:
                scores[category] = 0.9
        
        return scores
    
    def _generate_safety_recommendations(self, validation: Dict[str, Any], 
                                       safety_scores: Dict[str, float]) -> List[str]:
        """
        Generate safety recommendations based on validation and scores.
        
        Args:
            validation: The validation results
            safety_scores: The safety scores for different categories
            
        Returns:
            List of safety recommendations
        """
        recommendations = []
        
        # Add recommendations based on validation results
        if validation["warnings"]:
            recommendations.append("Review and refine your prompt to address safety concerns")
        
        if validation["blocked_reasons"]:
            recommendations.append("Your request was blocked due to policy violations")
        
        # Add recommendations based on safety scores
        for category, score in safety_scores.items():
            if score < 0.5:
                recommendations.append(f"High risk in {category} category - consider alternative approach")
            elif score < 0.7:
                recommendations.append(f"Moderate risk in {category} category - proceed with caution")
        
        if not recommendations:
            recommendations.append("Your request appears safe to proceed")
        
        return recommendations
