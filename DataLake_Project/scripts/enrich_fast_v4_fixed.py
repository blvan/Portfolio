#!/usr/bin/env python3
"""
SUPER FAST Enrichment v6:
- Preserve ALL values from silver layer (original_title, programtype, season, episode, year, rating, duration)
- Fill gaps with TVMaze + optional OMDB + deterministic generator
- Proper rating extraction and coalescing
"""

import os
import re
import time
import json
import random
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import pandas as pd
import requests
from tqdm import tqdm

class FastEnricher:
    """Fast enricher with minimal API calls + deterministic generator."""

    def __init__(self):
        self.cache: Dict[str, object] = {}
        self.omdb_calls = 0
        self.tvmaze_calls = 0
        self.tmdb_calls = 0
        self.last_time = time.time()
        self.omdb_api_key = os.getenv("OMDB_API_KEY", "")
        self.tmdb_api_key = os.getenv("TMDB_API_KEY", "")

    def rate_limit(self, delay: float = 0.15):
        """Simple delay."""
        elapsed = time.time() - self.last_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_time = time.time()

    # ---------------- TVMAZE -----------------
    def tvmaze_search(self, title: str) -> Optional[Dict]:
        cache_key = f"tvmaze::{title}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.15)
            resp = requests.get(
                "https://api.tvmaze.com/search/shows",
                params={"q": title},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    show = data[0]["show"]
                    self.tvmaze_calls += 1
                    self.cache[cache_key] = show
                    return show
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            pass
        self.cache[cache_key] = None
        return None

    def tvmaze_get_episodes(self, show_id: int) -> List[Dict]:
        cache_key = f"tvmaze_eps::{show_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.15)
            resp = requests.get(
                f"https://api.tvmaze.com/shows/{show_id}/episodes",
                timeout=3,
            )
            if resp.status_code == 200:
                episodes = resp.json()
                self.cache[cache_key] = episodes
                return episodes
        except Exception:
            pass
        self.cache[cache_key] = []
        return []

    def tvmaze_get_cast(self, show_id: int) -> List[Dict]:
        cache_key = f"tvmaze_cast::{show_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.15)
            resp = requests.get(
                f"https://api.tvmaze.com/shows/{show_id}/cast",
                timeout=3,
            )
            if resp.status_code == 200:
                cast = resp.json()
                self.cache[cache_key] = cast
                return cast
        except Exception:
            pass
        self.cache[cache_key] = []
        return []

    def tvmaze_get_crew(self, show_id: int) -> List[Dict]:
        cache_key = f"tvmaze_crew::{show_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.15)
            resp = requests.get(
                f"https://api.tvmaze.com/shows/{show_id}/crew",
                timeout=3,
            )
            if resp.status_code == 200:
                crew = resp.json()
                self.cache[cache_key] = crew
                return crew
        except Exception:
            pass
        self.cache[cache_key] = []
        return []

    # ---------------- OMDB -----------------
    def omdb_search(self, title: str, year: Optional[str], search_type: str = "series") -> Optional[Dict]:
        if not self.omdb_api_key:
            return None
        cache_key = f"omdb::{title}::{year}::{search_type}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.5)
            params = {"t": title, "apikey": self.omdb_api_key, "type": search_type}
            if year:
                params["y"] = year
            resp = requests.get("https://www.omdbapi.com/", params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.omdb_calls += 1
                self.cache[cache_key] = data
                return data
        except (requests.RequestException, requests.Timeout, ConnectionError):
            pass
        self.cache[cache_key] = None
        return None

    # ---------------- TMDB -----------------
    def tmdb_search(self, title: str, year: Optional[str], search_type: str = "tv") -> Optional[Dict]:
        """Search TMDB for TV show or movie. search_type: 'tv' or 'movie'"""
        if not self.tmdb_api_key:
            return None
        cache_key = f"tmdb::{title}::{year}::{search_type}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.25)
            endpoint = f"https://api.themoviedb.org/3/search/{search_type}"
            params = {"api_key": self.tmdb_api_key, "query": title}
            if year:
                if search_type == "movie":
                    params["primary_release_year"] = year
                else:
                    params["first_air_date_year"] = year
            resp = requests.get(endpoint, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("results"):
                    self.tmdb_calls += 1
                    result = data["results"][0]
                    self.cache[cache_key] = result
                    return result
        except (requests.RequestException, requests.Timeout, ConnectionError):
            pass
        self.cache[cache_key] = None
        return None

    def tmdb_get_details(self, tmdb_id: int, search_type: str = "tv") -> Optional[Dict]:
        """Get full details for a TMDB show or movie"""
        if not self.tmdb_api_key:
            return None
        cache_key = f"tmdb_details::{tmdb_id}::{search_type}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            self.rate_limit(0.25)
            endpoint = f"https://api.themoviedb.org/3/{search_type}/{tmdb_id}"
            params = {"api_key": self.tmdb_api_key}
            resp = requests.get(endpoint, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.cache[cache_key] = data
                return data
        except (requests.RequestException, requests.Timeout, ConnectionError):
            pass
        self.cache[cache_key] = None
        return None

    def parse_crew_from_omdb(self, omdb: Dict) -> Tuple[str, str, str, str]:
        directors = omdb.get("Director", "N/A")
        if directors == "N/A":
            directors = "Unknown"
        writers = omdb.get("Writer", "N/A")
        if writers == "N/A":
            writers = "Unknown"
        actors = omdb.get("Actors", "N/A")
        if actors == "N/A":
            actors = "Unknown"
        producers = "Unknown"  # OMDB doesn't give producers
        return directors, writers, actors, producers

    # ---------------- GENERATION -----------------
    def _seed_rng(self, title: str) -> random.Random:
        if not title:
            title = "default"
        seed = int(hashlib.sha256(title.encode("utf-8")).hexdigest(), 16) % (2**32)
        return random.Random(seed)

    def generate_people(self, title: str, count: int, roles: List[str]) -> Tuple[List[str], List[str], List[str]]:
        rng = self._seed_rng(title)
        first_names = ["James", "Sarah", "Michael", "Emma", "David", "Anna", "Robert", "Lisa", "John", "Maria"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        genders = ["M", "F", "U", "U"]

        names, role_list, genders_list = [], [], []
        for i in range(min(count, len(roles))):
            name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
            names.append(name)
            role_list.append(roles[i % len(roles)])
            genders_list.append(rng.choice(genders))
        return names, role_list, genders_list

    def generate_season_episode(self, title: str, program_type: str) -> Tuple[int, int]:
        rng = self._seed_rng(title + "_ep")
        if "daily" in (program_type or "").lower():
            season, episode = 1, rng.randint(1, 365)
        elif "series" in (program_type or "").lower():
            season, episode = rng.randint(1, 8), rng.randint(1, 12)
        else:
            season, episode = 1, 1
        return season, episode

    def generate_genre_runtime(self, title: str, program_type: str) -> Tuple[str, int, str]:
        title_low = title.lower()
        if any(k in title_low for k in ["news", "daily", "live"]):
            genre = "News"
            runtime = 30
        elif any(k in title_low for k in ["sports", "match", "game"]):
            genre = "Sport"
            runtime = 90
        elif any(k in title_low for k in ["comedy", "funny", "laugh"]):
            genre = "Comedy"
            runtime = 25
        elif any(k in title_low for k in ["drama", "crime", "thriller"]):
            genre = "Drama"
            runtime = 50
        else:
            genre = "Entertainment"
            runtime = 50

        language = "English"
        if "es" in title_low:
            language = "Spanish"
        elif "fr" in title_low:
            language = "French"
        return genre, runtime, language

    def generate_rating(self, title: str, genre: str) -> float:
        """Generate deterministic rating based on title and genre (5.0-9.5 range)"""
        rng = self._seed_rng(title + (genre or ""))
        # Weight by genre
        if genre and "News" in genre:
            base = 6.0
            spread = 2.0
        elif genre and ("Drama" in genre or "Crime" in genre):
            base = 7.0
            spread = 2.5
        elif genre and "Comedy" in genre:
            base = 6.5
            spread = 2.5
        else:
            base = 6.5
            spread = 2.5
        rating = base + rng.random() * spread
        return round(rating, 1)

    # ---------------- ENRICH -----------------
    def enrich_title(self, title: str, year: Optional[str], program_type: str) -> Dict:
        # Guard against None title
        if not title:
            title = "Unknown"

        result = {
            "season": None,
            "episode": None,
            "directors": None,
            "writers": None,
            "actors": None,
            "producers": None,
            "runtime_minutes": None,
            "genre": None,
            "rating": None,
            "program_language": None,
            "programtype": None,  # Add programtype to result
            "cast_names": [],
            "cast_roles": [],
            "cast_genders": [],
            "crew_names": [],
            "crew_roles": [],
            "crew_genders": [],
            # Source-specific IDs
            "imdb_id": None,
            "tmdb_id": None,
            "tvmaze_id": None,
        }

        # Try TVMaze first (free, rich for TV)
        tvmaze_show = self.tvmaze_search(title)
        if tvmaze_show:
            # Save TVMaze ID
            if tvmaze_show.get("id"):
                result["tvmaze_id"] = str(tvmaze_show["id"])

            # Get type from TVMaze
            if tvmaze_show.get("type"):
                tv_type = tvmaze_show["type"]
                if tv_type in ["Scripted", "Reality", "Documentary", "Talk Show", "News", "Game Show", "Variety", "Animation"]:
                    result["programtype"] = "Series"
                elif tv_type == "Movie":
                    result["programtype"] = "Movie"

            # seasons/episodes
            episodes = self.tvmaze_get_episodes(tvmaze_show.get("id")) if tvmaze_show.get("id") else []
            if episodes:
                max_ep = max(episodes, key=lambda e: (e.get("season") or 0, e.get("number") or 0))
                result["season"] = max_ep.get("season", 1) or 1
                result["episode"] = max_ep.get("number", 1) or 1
            # runtime/genre/lang
            if tvmaze_show.get("runtime"):
                result["runtime_minutes"] = tvmaze_show.get("runtime")
            # Average runtime from episodes if show runtime is None
            elif episodes:
                runtimes = [ep.get("runtime") for ep in episodes if ep.get("runtime")]
                if runtimes:
                    result["runtime_minutes"] = int(sum(runtimes) / len(runtimes))

            if tvmaze_show.get("genres"):
                result["genre"] = ", ".join(tvmaze_show.get("genres")) or result["genre"]
            if tvmaze_show.get("language"):
                result["program_language"] = tvmaze_show.get("language")
            # rating from TVMaze
            if tvmaze_show.get("rating", {}).get("average"):
                try:
                    result["rating"] = float(tvmaze_show["rating"]["average"])
                except:
                    pass

            # Get IMDB ID from TVMaze externals
            if tvmaze_show.get("externals", {}).get("imdb"):
                result["imdb_id"] = tvmaze_show["externals"]["imdb"]
            if tvmaze_show.get("externals", {}).get("thetvdb"):
                result["tmdb_id"] = str(tvmaze_show["externals"]["thetvdb"])

            # cast
            cast = self.tvmaze_get_cast(tvmaze_show.get("id")) if tvmaze_show.get("id") else []
            for person in cast[:8]:
                name = person.get("person", {}).get("name")
                role = person.get("character", {}).get("name") or "Actor"
                gender = person.get("person", {}).get("gender") or "U"
                if name:
                    result["cast_names"].append(name)
                    result["cast_roles"].append(role)
                    result["cast_genders"].append(gender)

            # crew
            crew = self.tvmaze_get_crew(tvmaze_show.get("id")) if tvmaze_show.get("id") else []
            for person in crew[:10]:
                name = person.get("person", {}).get("name")
                role = person.get("type") or "Crew"
                gender = person.get("person", {}).get("gender") or "U"
                if name:
                    result["crew_names"].append(name)
                    result["crew_roles"].append(role)
                    result["crew_genders"].append(gender)

        # Only try OMDB if TVMaze didn't find good programtype (movies often misidentified as series in TVMaze)
        # or if we got low confidence
        omdb = None
        if self.omdb_api_key and (result["programtype"] is None or result["runtime_minutes"] is None or result["runtime_minutes"] < 30):
            # Try movie first
            omdb = self.omdb_search(title, year, "movie")
            if omdb and omdb.get("Response") == "True":
                result["programtype"] = "Movie"
            else:
                # Try series if not a movie
                omdb = self.omdb_search(title, year, "series")
                if omdb and omdb.get("Response") == "True":
                    if result["programtype"] is None:
                        result["programtype"] = "Series"

        if omdb and omdb.get("Response") == "True":
            # Save IMDB ID from OMDB (prefer over TVMaze)
            if omdb.get("imdbID") and omdb["imdbID"] != "N/A":
                result["imdb_id"] = omdb["imdbID"]

            # Get Type from OMDB
            if omdb.get("Type") and omdb["Type"] != "N/A":
                if omdb["Type"] == "movie":
                    result["programtype"] = "Movie"
                elif omdb["Type"] == "series":
                    result["programtype"] = "Series"

            d, w, a, p = self.parse_crew_from_omdb(omdb)
            if result["directors"] is None:
                result["directors"] = d
            if result["writers"] is None:
                result["writers"] = w
            if result["actors"] is None:
                result["actors"] = a
            if result["producers"] is None:
                result["producers"] = p
            if result["runtime_minutes"] is None and omdb.get("Runtime") and omdb["Runtime"] != "N/A":
                try:
                    result["runtime_minutes"] = int(omdb["Runtime"].split()[0])
                except Exception:
                    pass
            if result["genre"] is None and omdb.get("Genre") and omdb["Genre"] != "N/A":
                result["genre"] = omdb["Genre"]
            # Rating from OMDB - prioritize if not set yet
            if result["rating"] is None and omdb.get("imdbRating") and omdb["imdbRating"] != "N/A":
                try:
                    result["rating"] = float(omdb["imdbRating"])
                except Exception:
                    pass

        # Only try TMDB if still missing critical data
        tmdb = None
        tmdb_id = None
        if self.tmdb_api_key and (result["rating"] is None or result["genre"] is None):
            # Try TV first
            tmdb = self.tmdb_search(title, year, "tv")
            if tmdb:
                tmdb_id = tmdb.get("id")
                if not result["tmdb_id"]:
                    result["tmdb_id"] = str(tmdb_id)
            else:
                # Try movie if TV not found
                tmdb = self.tmdb_search(title, year, "movie")
                if tmdb:
                    tmdb_id = tmdb.get("id")
                    if not result["tmdb_id"]:
                        result["tmdb_id"] = str(tmdb_id)

        if tmdb and tmdb_id:
            # Get full details
            search_type = "movie" if tmdb.get("title") else "tv"
            tmdb_details = self.tmdb_get_details(tmdb_id, search_type)

            if tmdb_details:
                # Rating from TMDB (only if not already set)
                if result["rating"] is None and tmdb_details.get("vote_average"):
                    try:
                        result["rating"] = float(tmdb_details["vote_average"])
                    except Exception:
                        pass

                # Genre from TMDB (only if not already set)
                if result["genre"] is None and tmdb_details.get("genres"):
                    result["genre"] = ", ".join([g.get("name") for g in tmdb_details["genres"]])

                # Runtime
                if search_type == "movie" and result["runtime_minutes"] is None and tmdb_details.get("runtime"):
                    result["runtime_minutes"] = tmdb_details.get("runtime")
                elif search_type == "tv" and result["runtime_minutes"] is None and tmdb_details.get("episode_run_time"):
                    runtimes = tmdb_details.get("episode_run_time")
                    if runtimes and len(runtimes) > 0:
                        result["runtime_minutes"] = runtimes[0]

                # Imdb_id from TMDB external IDs (only if not already set)
                if result["imdb_id"] is None and tmdb_details.get("external_ids", {}).get("imdb_id"):
                    result["imdb_id"] = tmdb_details["external_ids"]["imdb_id"]

        # Fallback generation for missing values
        if not result["cast_names"]:
            names, roles, genders = self.generate_people(title, 5, ["Lead", "Support", "Guest"])
            result["cast_names"], result["cast_roles"], result["cast_genders"] = names, roles, genders

        if not result["crew_names"]:
            names, roles, genders = self.generate_people(title, 4, ["Director", "Writer", "Producer", "Editor"])
            result["crew_names"], result["crew_roles"], result["crew_genders"] = names, roles, genders

        # Fill None directors/writers/actors/producers from crew
        if result["directors"] is None and result["crew_names"]:
            result["directors"] = result["crew_names"][0]
        if result["writers"] is None and len(result["crew_names"]) > 1:
            result["writers"] = result["crew_names"][1]
        if result["actors"] is None and result["cast_names"]:
            result["actors"] = ", ".join(result["cast_names"][:5])
        if result["producers"] is None and len(result["crew_names"]) > 2:
            result["producers"] = result["crew_names"][2]

        # Set defaults for None values
        if result["directors"] is None:
            result["directors"] = "Unknown"
        if result["writers"] is None:
            result["writers"] = "Unknown"
        if result["actors"] is None:
            result["actors"] = "Unknown"
        if result["producers"] is None:
            result["producers"] = "Unknown"

        # Season/episode fallback
        if result["season"] is None or result["season"] <= 0:
            s, e = self.generate_season_episode(title, program_type)
            result["season"] = s
        if result["episode"] is None or result["episode"] <= 0:
            _, e = self.generate_season_episode(title, program_type)
            result["episode"] = e

        # Determine programtype intelligently if still not set
        if result["programtype"] is None:
            # Heuristic: if runtime > 60 min and season=1, episode=1 -> likely a movie
            if result["runtime_minutes"] and result["runtime_minutes"] > 60:
                if (result["season"] == 1 or result["season"] is None) and (result["episode"] == 1 or result["episode"] is None):
                    result["programtype"] = "Movie"

            # If still not determined, check title patterns
            if result["programtype"] is None:
                title_lower = title.lower()
                if any(word in title_lower for word in ["film", "movie", "película"]):
                    result["programtype"] = "Movie"
                elif any(word in title_lower for word in ["series", "serial", "show"]):
                    result["programtype"] = "Series"
                else:
                    # Default based on season/episode presence
                    if result["season"] and result["season"] > 1:
                        result["programtype"] = "Series"
                    elif result["episode"] and result["episode"] > 1:
                        result["programtype"] = "Series"
                    else:
                        result["programtype"] = "Series"  # Default to Series for TV content

        # Genre/runtime/language fallback
        if result["genre"] is None:
            g, rt, lang = self.generate_genre_runtime(title, result["programtype"] or program_type)
            result["genre"] = g
            if result["runtime_minutes"] is None:
                result["runtime_minutes"] = rt
            if result["program_language"] is None:
                result["program_language"] = lang

        if result["runtime_minutes"] is None:
            _, rt, _ = self.generate_genre_runtime(title, result["programtype"] or program_type)
            # For movies, default to 90-120 min, for series 30-50 min
            if result["programtype"] == "Movie":
                result["runtime_minutes"] = 100
            else:
                result["runtime_minutes"] = rt

        if result["program_language"] is None:
            _, _, lang = self.generate_genre_runtime(title, result["programtype"] or program_type)
            result["program_language"] = lang

        # Generate rating if not available from APIs
        if result["rating"] is None:
            result["rating"] = self.generate_rating(title, result["genre"])

        return result


def main():
    print("\n" + "=" * 90)
    print("⚡ SUPER FAST ENRICHMENT v6 - Preserve silver + enrich gaps")
    print("=" * 90)

    # Read all silver partitions
    from glob import glob as glob_files
    silver_dir = Path("datalake/silver/now_playing")
    if not silver_dir.exists():
        print(f"❌ Silver dir not found: {silver_dir}")
        return

    silver_files = sorted(glob_files(str(silver_dir / "load_date=*/part.parquet")))
    if not silver_files:
        print(f"❌ No silver parquet files found in {silver_dir}")
        return

    print(f"📖 Reading {len(silver_files)} silver partitions...")
    dfs = [pd.read_parquet(f) for f in silver_files]
    df = pd.concat(dfs, ignore_index=True)
    print(f"\n✅ Loaded {len(df):,} rows, {df['title'].nunique():,} unique titles")

    unique = df[["title", "year", "programtype"]].drop_duplicates().reset_index(drop=True)
    print(f"📝 Processing {len(unique):,} unique titles...\n")

    enricher = FastEnricher()
    enrichments = []

    for _, row in tqdm(unique.iterrows(), total=len(unique), desc="🔍 Enriching", ncols=90):
        title = row["title"]
        year = str(row["year"]).strip() if pd.notna(row["year"]) else None
        program_type = str(row["programtype"]).strip() if pd.notna(row["programtype"]) else ""
        enriched = enricher.enrich_title(title, year, program_type)
        enriched["title"] = title
        enrichments.append(enriched)

    enrichment_df = pd.DataFrame(enrichments)
    print(f"\n✅ Enriched {len(enrichment_df):,} titles")

    # Merge enrichment data back to silver
    # Left join on title to preserve all silver data
    df_result = df.merge(enrichment_df, on="title", how="left", suffixes=("_silver", "_api"))

    # Coalesce: prefer silver values, fall back to API enrichment
    for col in ["season", "episode", "runtime_minutes"]:
        silver_col = f"{col}_silver"
        api_col = f"{col}_api"

        if silver_col in df_result.columns and api_col in df_result.columns:
            # Use silver if valid (not null and > 0), otherwise use API
            mask = df_result[silver_col].isna() | (df_result[silver_col] <= 0)
            df_result[col] = df_result[silver_col].copy()
            df_result.loc[mask, col] = df_result.loc[mask, api_col]
            df_result.drop(columns=[silver_col, api_col], inplace=True)
        elif silver_col in df_result.columns:
            df_result[col] = df_result[silver_col]
            df_result.drop(columns=[silver_col], inplace=True)
        elif api_col in df_result.columns:
            df_result[col] = df_result[api_col]
            df_result.drop(columns=[api_col], inplace=True)

    # String coalesce: prefer silver if not null/empty, otherwise use API
    for col in ["directors", "writers", "actors", "producers", "genre", "program_language", "programtype"]:
        silver_col = f"{col}_silver"
        api_col = f"{col}_api"

        if silver_col in df_result.columns and api_col in df_result.columns:
            # Use silver if valid, otherwise API
            mask = df_result[silver_col].isna() | (df_result[silver_col] == "")
            df_result[col] = df_result[silver_col].copy()
            df_result.loc[mask, col] = df_result.loc[mask, api_col]
            df_result.drop(columns=[silver_col, api_col], inplace=True)
        elif silver_col in df_result.columns:
            df_result[col] = df_result[silver_col]
            df_result.drop(columns=[silver_col], inplace=True)
        elif api_col in df_result.columns:
            df_result[col] = df_result[api_col]
            df_result.drop(columns=[api_col], inplace=True)

    # Rating: coalesce silver rating with API enrichment
    silver_rating_col = "rating_silver"
    api_rating_col = "rating_api"
    if silver_rating_col in df_result.columns and api_rating_col in df_result.columns:
        mask = df_result[silver_rating_col].isna()
        df_result["rating"] = df_result[silver_rating_col].copy()
        df_result.loc[mask, "rating"] = df_result.loc[mask, api_rating_col]
        df_result.drop(columns=[silver_rating_col, api_rating_col], inplace=True)
    elif silver_rating_col in df_result.columns:
        df_result["rating"] = df_result[silver_rating_col]
        df_result.drop(columns=[silver_rating_col], inplace=True)
    elif api_rating_col in df_result.columns:
        df_result["rating"] = df_result[api_rating_col]
        df_result.drop(columns=[api_rating_col], inplace=True)

    # Year: coalesce
    if "year_silver" in df_result.columns and "year_api" in df_result.columns:
        mask = df_result["year_silver"].isna()
        df_result["year"] = df_result["year_silver"].copy()
        df_result.loc[mask, "year"] = df_result.loc[mask, "year_api"]
        df_result.drop(columns=["year_silver", "year_api"], inplace=True)
    elif "year_silver" in df_result.columns:
        df_result["year"] = df_result["year_silver"]
        df_result.drop(columns=["year_silver"], inplace=True)
    elif "year_api" in df_result.columns:
        df_result["year"] = df_result["year_api"]
        df_result.drop(columns=["year_api"], inplace=True)

    # List fields: prefer API
    for col in ["cast_names", "cast_roles", "cast_genders", "crew_names", "crew_roles", "crew_genders"]:
        api_col = f"{col}_api"
        if api_col in df_result.columns:
            df_result[col] = df_result[api_col]
            df_result.drop(columns=[api_col], inplace=True)
        silver_col = f"{col}_silver"
        if silver_col in df_result.columns:
            df_result.drop(columns=[silver_col], inplace=True)

    # ID fields: prefer API, coalesce with silver if exists
    for col in ["imdb_id", "tmdb_id", "tvmaze_id"]:
        api_col = f"{col}_api"
        silver_col = f"{col}_silver"

        if api_col in df_result.columns and silver_col in df_result.columns:
            # Use API if available, otherwise silver
            mask = df_result[api_col].isna()
            df_result[col] = df_result[api_col].copy()
            df_result.loc[mask, col] = df_result.loc[mask, silver_col]
            df_result.drop(columns=[api_col, silver_col], inplace=True)
        elif api_col in df_result.columns:
            df_result[col] = df_result[api_col]
            df_result.drop(columns=[api_col], inplace=True)
        elif silver_col in df_result.columns:
            df_result[col] = df_result[silver_col]
            df_result.drop(columns=[silver_col], inplace=True)

    # original_title and programtype are preserved from silver (no _api suffix)

    # Write to unified gold output
    out_dir = Path("datalake/gold/all_teams")
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "TV_data.parquet"
    df_result.to_parquet(output, engine="pyarrow", index=False)
    print(f"\n✅ Saved: {output}")

    print("\n" + "=" * 90)
    print("📊 ENRICHMENT SUMMARY:")
    print(f"   Rows: {len(df_result):,}")
    print(f"   Columns: {len(df_result.columns)}")
    print(f"   Original titles present: {df_result['original_title'].notna().sum():,}")
    print(f"   Programtypes present: {df_result['programtype'].notna().sum():,} ({100*df_result['programtype'].notna().sum()/len(df_result):.1f}%)")
    if df_result['programtype'].notna().sum() > 0:
        print(f"      Movies: {(df_result['programtype'] == 'Movie').sum():,}")
        print(f"      Series: {(df_result['programtype'] == 'Series').sum():,}")
    print(f"   Unique seasons: {df_result['season'].nunique():,}")
    print(f"   Unique episodes: {df_result['episode'].nunique():,}")
    print(f"   Unique runtimes: {df_result['runtime_minutes'].nunique():,}")
    print(f"   Years present: {df_result['year'].notna().sum():,}")
    print(f"   Ratings present: {df_result['rating'].notna().sum():,} ({100*df_result['rating'].notna().sum()/len(df_result):.1f}%)")
    print(f"   IMDB IDs: {df_result['imdb_id'].notna().sum():,}")
    print(f"   TMDB IDs: {df_result['tmdb_id'].notna().sum():,}")
    print(f"   TVMaze IDs: {df_result['tvmaze_id'].notna().sum():,}")
    print(f"   OMDB calls: {enricher.omdb_calls}")
    print(f"   TVMaze calls: {enricher.tvmaze_calls}")
    print(f"   TMDB calls: {enricher.tmdb_calls}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
