"""
Agent Skill Marketplace

Discover and download skills from local and remote sources.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

import aiohttp
import yaml

from alpha.skills.base import SkillMetadata

logger = logging.getLogger(__name__)


class SkillMarketplace:
    """
    Skill marketplace for discovering skills.

    Features:
    - Search skills by name, category, or tags
    - Download skills from remote repositories
    - Support multiple skill sources (GitHub, local registry, etc.)
    - Cache skill metadata for fast lookup
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".alpha" / "skill_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_cache: Dict[str, SkillMetadata] = {}
        self.sources: List[str] = []

        # Default skill sources
        self._load_default_sources()

    def _load_default_sources(self):
        """Load default skill sources."""
        # Builtin skills registry (highest priority)
        builtin_registry = Path(__file__).parent / "builtin" / "registry.json"
        if builtin_registry.exists():
            self.sources.append(str(builtin_registry))

        # Alpha official skill repository (example)
        self.sources.append("https://raw.githubusercontent.com/alpha-ai/skills/main/registry.json")

        # Local skill directory
        local_registry = Path.home() / ".alpha" / "local_skills" / "registry.json"
        if local_registry.exists():
            self.sources.append(str(local_registry))

    def add_source(self, source: str):
        """
        Add a skill source.

        Args:
            source: URL or file path to skill registry
        """
        if source not in self.sources:
            self.sources.append(source)
            logger.info(f"Added skill source: {source}")

    def remove_source(self, source: str):
        """Remove a skill source."""
        if source in self.sources:
            self.sources.remove(source)
            logger.info(f"Removed skill source: {source}")

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[SkillMetadata]:
        """
        Search for skills.

        Args:
            query: Search query (skill name or description)
            category: Filter by category
            tags: Filter by tags
            limit: Maximum number of results

        Returns:
            List of matching skill metadata
        """
        logger.info(f"Searching skills: query='{query}', category={category}, tags={tags}")

        # Update cache if empty
        if not self.metadata_cache:
            await self._update_cache()

        # Search in cache
        results = []
        query_lower = query.lower()

        for skill_meta in self.metadata_cache.values():
            # Filter by category
            if category and skill_meta.category != category:
                continue

            # Filter by tags
            if tags and not any(tag in skill_meta.tags for tag in tags):
                continue

            # Match query in name or description
            if (query_lower in skill_meta.name.lower() or
                query_lower in skill_meta.description.lower()):
                results.append(skill_meta)

            if len(results) >= limit:
                break

        logger.info(f"Found {len(results)} skills matching query")
        return results

    async def get_skill_info(self, skill_name: str) -> Optional[SkillMetadata]:
        """
        Get detailed skill information.

        Args:
            skill_name: Skill name

        Returns:
            SkillMetadata or None if not found
        """
        # Check cache first
        if skill_name in self.metadata_cache:
            return self.metadata_cache[skill_name]

        # Update cache and search again
        await self._update_cache()
        return self.metadata_cache.get(skill_name)

    async def download_skill(
        self,
        skill_name: str,
        target_dir: Path,
        version: Optional[str] = None
    ) -> Optional[Path]:
        """
        Download a skill.

        Args:
            skill_name: Skill name
            target_dir: Target directory for installation
            version: Specific version (default: latest)

        Returns:
            Path to downloaded skill directory or None if failed
        """
        logger.info(f"Downloading skill: {skill_name} (version: {version or 'latest'})")

        # Get skill metadata
        skill_meta = await self.get_skill_info(skill_name)
        if not skill_meta:
            logger.error(f"Skill not found: {skill_name}")
            return None

        # Check version compatibility
        if version and skill_meta.version != version:
            logger.warning(
                f"Requested version {version} but found {skill_meta.version}"
            )

        # Download from repository
        if not skill_meta.repository:
            logger.error(f"No repository URL for skill: {skill_name}")
            return None

        # Check if it's a builtin skill
        if skill_meta.repository == "builtin":
            # Builtin skills are already on disk
            builtin_skill_dir = Path(__file__).parent / "builtin" / skill_name
            if builtin_skill_dir.exists():
                logger.info(f"Using builtin skill at: {builtin_skill_dir}")
                return builtin_skill_dir
            else:
                logger.error(f"Builtin skill directory not found: {builtin_skill_dir}")
                return None

        skill_dir = target_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download skill files
            success = await self._download_from_repo(
                skill_meta.repository,
                skill_dir
            )

            if success:
                logger.info(f"Successfully downloaded skill to: {skill_dir}")
                return skill_dir
            else:
                logger.error(f"Failed to download skill: {skill_name}")
                return None

        except Exception as e:
            logger.error(f"Error downloading skill {skill_name}: {e}", exc_info=True)
            return None

    async def _update_cache(self):
        """Update skill metadata cache from all sources."""
        logger.info("Updating skill metadata cache...")

        for source in self.sources:
            try:
                if source.startswith("http://") or source.startswith("https://"):
                    # Remote source
                    await self._fetch_remote_registry(source)
                else:
                    # Local source
                    await self._load_local_registry(source)

            except Exception as e:
                logger.error(f"Error loading source {source}: {e}", exc_info=True)

        logger.info(f"Cache updated: {len(self.metadata_cache)} skills available")

    async def _fetch_remote_registry(self, url: str):
        """Fetch skill registry from remote URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._parse_registry(data)
                    else:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")

        except Exception as e:
            logger.error(f"Error fetching remote registry {url}: {e}")

    async def _load_local_registry(self, path: str):
        """Load skill registry from local file."""
        try:
            registry_path = Path(path)
            if not registry_path.exists():
                return

            with open(registry_path, 'r') as f:
                if path.endswith('.json'):
                    data = json.load(f)
                elif path.endswith('.yaml') or path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    logger.warning(f"Unsupported registry format: {path}")
                    return

            self._parse_registry(data)

        except Exception as e:
            logger.error(f"Error loading local registry {path}: {e}")

    def _parse_registry(self, data: Dict):
        """Parse registry data and update cache."""
        if "skills" not in data:
            return

        for skill_data in data["skills"]:
            try:
                metadata = SkillMetadata(
                    name=skill_data["name"],
                    version=skill_data["version"],
                    description=skill_data["description"],
                    author=skill_data["author"],
                    category=skill_data.get("category", "general"),
                    tags=skill_data.get("tags", []),
                    dependencies=skill_data.get("dependencies", []),
                    python_version=skill_data.get("python_version", ">=3.8"),
                    homepage=skill_data.get("homepage"),
                    repository=skill_data.get("repository"),
                    license=skill_data.get("license"),
                )

                self.metadata_cache[metadata.name] = metadata

            except KeyError as e:
                logger.warning(f"Invalid skill metadata: missing field {e}")
            except Exception as e:
                logger.error(f"Error parsing skill metadata: {e}")

    async def _download_from_repo(self, repo_url: str, target_dir: Path) -> bool:
        """
        Download skill files from repository.

        Supports:
        - GitHub repositories
        - Direct download URLs
        - Git clone

        Args:
            repo_url: Repository URL
            target_dir: Target directory

        Returns:
            True if successful
        """
        # For now, implement simple GitHub download
        # In production, you'd want more robust handling

        if "github.com" in repo_url:
            # Convert GitHub URL to raw content URL
            # Example: https://github.com/user/repo -> https://raw.githubusercontent.com/user/repo/main/
            raw_url = repo_url.replace("github.com", "raw.githubusercontent.com")
            if not raw_url.endswith("/"):
                raw_url += "/"
            raw_url += "main/"  # Assume main branch

            # Download essential files
            files_to_download = ["skill.yaml", "skill.py", "README.md", "requirements.txt"]

            async with aiohttp.ClientSession() as session:
                for filename in files_to_download:
                    file_url = raw_url + filename
                    try:
                        async with session.get(
                            file_url,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status == 200:
                                content = await response.read()
                                file_path = target_dir / filename
                                file_path.write_bytes(content)
                                logger.info(f"Downloaded: {filename}")
                            elif filename in ["skill.yaml", "skill.py"]:
                                # These are required
                                logger.error(f"Failed to download required file: {filename}")
                                return False

                    except Exception as e:
                        if filename in ["skill.yaml", "skill.py"]:
                            logger.error(f"Error downloading {filename}: {e}")
                            return False

            return True

        else:
            logger.error(f"Unsupported repository type: {repo_url}")
            return False

    def clear_cache(self):
        """Clear metadata cache."""
        self.metadata_cache.clear()
        logger.info("Skill metadata cache cleared")
