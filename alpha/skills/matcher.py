"""
Automatic Skill Matcher

Analyzes user requests and finds relevant skills from skills.sh marketplace.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    Intelligent skill matcher that finds relevant skills based on user queries.

    Features:
    - Search skills.sh API for relevant skills
    - Keyword-based matching
    - Ranking by install count and relevance
    - Local skill cache
    """

    def __init__(self, api_url: str = "https://skills.sh/api/skills"):
        self.api_url = api_url
        self.skills_cache: List[Dict] = []
        self.cache_loaded = False

    async def load_skills_cache(self) -> bool:
        """Load available skills from skills.sh API."""
        try:
            logger.info("Loading skills from skills.sh marketplace...")

            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.skills_cache = data.get('skills', [])
                        self.cache_loaded = True
                        logger.info(f"Loaded {len(self.skills_cache)} skills from marketplace")
                        return True
                    else:
                        logger.warning(f"Failed to load skills: HTTP {response.status}")
                        return False
        except asyncio.TimeoutError:
            logger.warning("Timeout loading skills from marketplace")
            return False
        except Exception as e:
            logger.error(f"Error loading skills: {e}")
            return False

    def match_skills(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Match skills based on query.

        Args:
            query: User query or task description
            max_results: Maximum number of results to return

        Returns:
            List of matching skills with relevance scores
        """
        if not self.cache_loaded:
            logger.warning("Skills cache not loaded")
            return []

        query_lower = query.lower()

        # Extract keywords from query
        keywords = self._extract_keywords(query_lower)

        # Score each skill
        scored_skills = []
        for skill in self.skills_cache:
            score = self._calculate_relevance(skill, keywords, query_lower)
            if score > 0:
                scored_skills.append({
                    'id': skill['id'],
                    'name': skill['name'],
                    'installs': skill.get('installs', 0),
                    'source': skill.get('topSource', ''),
                    'score': score
                })

        # Sort by score (descending) and installs (descending)
        scored_skills.sort(key=lambda x: (x['score'], x['installs']), reverse=True)

        return scored_skills[:max_results]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from query."""
        # Common task keywords
        keywords = []

        # Development keywords
        if any(word in query for word in ['react', 'next.js', 'nextjs', 'frontend', 'ui', 'component']):
            keywords.append('react')
        if any(word in query for word in ['design', 'ui', 'ux', 'interface', 'layout']):
            keywords.append('design')
        if any(word in query for word in ['test', 'testing', 'qa']):
            keywords.append('test')
        if any(word in query for word in ['pdf', 'document', 'doc']):
            keywords.append('pdf')
        if any(word in query for word in ['excel', 'spreadsheet', 'xlsx']):
            keywords.append('excel')
        if any(word in query for word in ['powerpoint', 'presentation', 'pptx', 'slides']):
            keywords.append('presentation')
        if any(word in query for word in ['word', 'docx', 'document']):
            keywords.append('word')
        if any(word in query for word in ['seo', 'search engine', 'optimization']):
            keywords.append('seo')
        if any(word in query for word in ['database', 'postgres', 'postgresql', 'sql', 'supabase', 'query', 'queries']):
            keywords.append('database')
        if any(word in query for word in ['auth', 'authentication', 'login', 'user']):
            keywords.append('auth')
        if any(word in query for word in ['mobile', 'react native', 'ios', 'android']):
            keywords.append('mobile')
        if any(word in query for word in ['video', 'animation', 'remotion']):
            keywords.append('video')
        if any(word in query for word in ['browse', 'browser', 'web scraping', 'automation']):
            keywords.append('browser')
        if any(word in query for word in ['audit', 'review', 'analyze', 'check']):
            keywords.append('audit')
        if any(word in query for word in ['copy', 'copywriting', 'content', 'writing']):
            keywords.append('copywriting')

        return keywords

    def _calculate_relevance(self, skill: Dict, keywords: List[str], query: str) -> float:
        """Calculate relevance score for a skill."""
        score = 0.0
        skill_name = skill['name'].lower()

        # Exact name match
        if query in skill_name or skill_name in query:
            score += 10.0

        # Keyword matches in name
        for keyword in keywords:
            if keyword in skill_name:
                score += 5.0

        # Special mappings for common mismatches
        keyword_to_skill = {
            'database': ['postgres', 'supabase', 'sql'],
            'presentation': ['pptx', 'powerpoint'],
            'excel': ['xlsx'],
            'word': ['docx'],
        }

        for keyword in keywords:
            if keyword in keyword_to_skill:
                for skill_keyword in keyword_to_skill[keyword]:
                    if skill_keyword in skill_name:
                        score += 5.0

        # Boost popular skills slightly
        installs = skill.get('installs', 0)
        if installs > 50000:
            score += 2.0
        elif installs > 20000:
            score += 1.0
        elif installs > 5000:
            score += 0.5

        return score

    async def find_best_skill(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Find the best matching skill for a query.

        Args:
            query: User query or task description

        Returns:
            Best matching skill or None
        """
        if not self.cache_loaded:
            await self.load_skills_cache()

        matches = self.match_skills(query, max_results=1)
        return matches[0] if matches else None

    async def find_skills(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Find multiple matching skills for a query.

        Args:
            query: User query or task description
            max_results: Maximum number of results

        Returns:
            List of matching skills
        """
        if not self.cache_loaded:
            await self.load_skills_cache()

        return self.match_skills(query, max_results=max_results)
