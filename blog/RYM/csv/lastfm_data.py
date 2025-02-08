import argparse
import json
import requests
from datetime import datetime, timedelta
import time
import sys
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LastFMStats:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        
    def _make_request(self, method: str, params: Dict, max_retries: int = 3) -> Dict:
        """Make a request to Last.fm API with robust error handling"""
        params.update({
            'method': method,
            'api_key': self.api_key,
            'format': 'json'
        })
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                
                # Log raw response for debugging
                logger.debug(f"Raw response: {response.text[:500]}...")
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Check for Last.fm API errors
                json_response = response.json()
                if 'error' in json_response:
                    logger.error(f"Last.fm API Error: {json_response}")
                    return {}
                
                time.sleep(0.1)  # Rate limiting
                return json_response
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(0.1)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error (attempt {attempt+1}/{max_retries}): {e}")
                logger.error(f"Response content: {response.text}")
                time.sleep(0.1)
        
        logger.error("Max retries reached. Failed to fetch data.")
        return {}
    
    def get_track_info(self, artist: str, track: str) -> Dict:
        """Get detailed track information including duration, mbid, and genres"""
        try:
            params = {
                'artist': artist,
                'track': track
            }
            track_info = self._make_request('track.getInfo', params)

            if not track_info:
                return {}

            # Extraer géneros si existen
            tags = track_info.get("track", {}).get("toptags", {}).get("tag", [])
            genres = [tag["name"] for tag in tags] if isinstance(tags, list) else []

            # Agregar géneros a la respuesta
            track_info["track"]["genres"] = genres

            return track_info
        except Exception as e:
            logger.warning(f"Could not fetch track info for {artist} - {track}: {e}")
            return {}
    
    def get_user_tracks(self, username: str, start_time: int, end_time: int) -> List[Dict]:
        """Get user's scrobbled tracks within a time period"""
        tracks = []
        page = 1
        while True:
            params = {
                'user': username,
                'from': start_time,
                'to': end_time,
                'page': page,
                'limit': 200
            }
            
            try:
                response = self._make_request('user.getRecentTracks', params)
                
                if not response or 'recenttracks' not in response or 'track' not in response['recenttracks']:
                    logger.warning(f"No tracks found for {username} in this period")
                    break
                
                current_tracks = response['recenttracks']['track']
                if not current_tracks:
                    break
                
                tracks.extend(current_tracks)
                
                # Check if there are more pages
                total_pages = int(response['recenttracks']['@attr'].get('totalPages', 1))
                if page >= total_pages:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching tracks for {username}: {e}")
                break
        
        return tracks

    def process_tracks(self, tracks: List[Dict], period_type: str) -> List[Dict]:
        """Process tracks and add additional information"""
        if not tracks:
            logger.warning("No tracks to process")
            return []
        
        track_stats = {}
        
        for track in tracks:
            try:
                # Skip now playing tracks
                if '@attr' in track and 'nowplaying' in track['@attr']:
                    continue
                
                # Ensure required keys exist
                if not all(key in track for key in ['artist', 'name', 'date', 'album']):
                    continue
                
                key = f"{track['artist']['#text']}-{track['name']}"
                timestamp = int(track['date']['uts'])
                
                if key not in track_stats:
                    # Try to get track information
                    track_info = self.get_track_info(track['artist']['#text'], track['name'])
                    
                    track_stats[key] = {
                        'name': track['name'],
                        'artist': {
                            'name': track['artist']['#text'],
                            'mbid': track['artist'].get('mbid', '')
                        },
                        'album': {
                            'name': track['album']['#text'],
                            'mbid': track['album'].get('mbid', ''),
                            'image': next((img['#text'] for img in track.get('image', []) if img['#text']), '')
                        },
                        'mbid': track.get('mbid', ''),
                        'duration': int(track_info.get('track', {}).get('duration', 0)),
                        'url': track.get('url', ''),
                        'plays': 1,
                        'timestamps': [timestamp]
                    }
                else:
                    track_stats[key]['plays'] += 1
                    track_stats[key]['timestamps'].append(timestamp)
            
            except Exception as e:
                logger.warning(f"Error processing track: {e}")
        
        # Convert to list and add ranks
        result = list(track_stats.values())
        result.sort(key=lambda x: x['plays'], reverse=True)
        for i, track in enumerate(result):
            track['rank'] = i + 1
        
        return result

def create_weekly_stats(api_key: str, usernames: List[str], year: int, week: int):
    stats = LastFMStats(api_key)
    result = {'period': 'weekly', 'year': year, 'week': week, 'users': {}}
    
    # Calculate week start and end timestamps
    start_date = datetime.strptime(f'{year}-W{week}-1', '%Y-W%W-%w')
    end_date = start_date + timedelta(days=7)
    
    for username in usernames:
        logger.info(f"Processing weekly stats for {username}")
        tracks = stats.get_user_tracks(
            username,
            int(start_date.timestamp()),
            int(end_date.timestamp())
        )
        result['users'][username] = stats.process_tracks(tracks, 'weekly')
    
    return result

def create_monthly_stats(api_key: str, usernames: List[str], year: int, month: int):
    stats = LastFMStats(api_key)
    result = {'period': 'monthly', 'year': year, 'month': month, 'users': {}}
    
    # Calculate month start and end timestamps
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    for username in usernames:
        logger.info(f"Processing monthly stats for {username}")
        tracks = stats.get_user_tracks(
            username,
            int(start_date.timestamp()),
            int(end_date.timestamp())
        )
        result['users'][username] = stats.process_tracks(tracks, 'monthly')
    
    return result

def create_yearly_stats(api_key: str, usernames: List[str], year: int):
    stats = LastFMStats(api_key)
    result = {'period': 'yearly', 'year': year, 'users': {}}
    
    # Calculate year start and end timestamps
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    
    for username in usernames:
        logger.info(f"Processing yearly stats for {username}")
        tracks = stats.get_user_tracks(
            username,
            int(start_date.timestamp()),
            int(end_date.timestamp())
        )
        result['users'][username] = stats.process_tracks(tracks, 'yearly')
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Last.fm statistics')
    parser.add_argument('--api-key', required=True, help='Last.fm API key')
    parser.add_argument('--users', required=True, nargs='+', help='List of Last.fm usernames')
    parser.add_argument('--period', required=True, choices=['weekly', 'monthly', 'yearly'], 
                      help='Statistics period')
    parser.add_argument('--year', required=True, type=int, help='Year')
    parser.add_argument('--month', type=int, help='Month (1-12, required for monthly stats)')
    parser.add_argument('--week', type=int, help='Week number (1-52, required for weekly stats)')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configurar nivel de registro si se activa el modo de depuración
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    if args.period == 'weekly' and args.week is None:
        parser.error('Week number is required for weekly statistics')
    if args.period == 'monthly' and args.month is None:
        parser.error('Month is required for monthly statistics')
    
    try:
        # Generate statistics based on period
        if args.period == 'weekly':
            result = create_weekly_stats(args.api_key, args.users, args.year, args.week)
        elif args.period == 'monthly':
            result = create_monthly_stats(args.api_key, args.users, args.year, args.month)
        else:  # yearly
            result = create_yearly_stats(args.api_key, args.users, args.year)
        
        # Save results to JSON file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Statistics saved to {args.output}")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)