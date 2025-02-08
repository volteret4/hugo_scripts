import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns
from datetime import datetime
import calendar
import os
import sys

def load_data(file_path):
    """Load and parse JSON data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_song_matches(users_data, exclude_tags=None, by_service=False):
    """
    Find song matches between users.
    
    Args:
        users_data (dict): Dictionary containing user listening data
        exclude_tags (list): List of tags/genres to exclude from matching
        by_service (bool): If True, separate matches by music service source
    
    Returns:
        If by_service is False:
            dict: Dictionary of dictionaries with user matches
        If by_service is True:
            dict: Dictionary with service keys, each containing user matches
    """
    if exclude_tags is None:
        exclude_tags = []
    
    def should_include_song(song):
        """Check if song should be included based on excluded tags."""
        song_genres = set(song.get('genres', []))
        return not bool(song_genres.intersection(exclude_tags))
    
    def get_song_sources(song):
        """Get the sources/services for a song based on its genre sources."""
        sources = []
        genres_by_source = song.get('genres_by_source', {})
        
        for source, genres in genres_by_source.items():
            if genres:  # If this source has any genres
                sources.append(source)
        
        # If no specific sources found, consider it as general
        return sources if sources else ['general']
    
    if by_service:
        # Initialize matches dictionary with service keys
        matches = {
            service: defaultdict(lambda: defaultdict(int))
            for service in ['lastfm', 'spotify', 'musicbrainz', 'discogs', 'general']
        }
        
        # Create dictionaries to store songs for each user, separated by service
        user_songs_by_service = {
            service: {user: set() for user in users_data.keys()}
            for service in matches.keys()
        }
        
        # Populate songs by service
        for user, songs in users_data.items():
            for song in songs:
                if should_include_song(song):
                    song_key = (song['name'], song['artist']['name'])
                    sources = get_song_sources(song)
                    
                    for source in sources:
                        user_songs_by_service[source][user].add(song_key)
        
        # Calculate matches for each service
        users = list(users_data.keys())
        for service in matches.keys():
            for i, user1 in enumerate(users):
                for user2 in users[i+1:]:
                    common_songs = len(
                        user_songs_by_service[service][user1].intersection(
                            user_songs_by_service[service][user2]
                        )
                    )
                    if common_songs > 0:
                        matches[service][user1][user2] = common_songs
                        matches[service][user2][user1] = common_songs
        
        return matches
        
    else:
        # Original behavior but with tag exclusion
        matches = defaultdict(lambda: defaultdict(int))
        
        # Create a dictionary to store songs for each user
        user_songs = {
            user: set(
                (song['name'], song['artist']['name'])
                for song in songs
                if should_include_song(song)
            )
            for user, songs in users_data.items()
        }
        
        # Calculate matches between users
        users = list(users_data.keys())
        for i, user1 in enumerate(users):
            for user2 in users[i+1:]:
                common_songs = len(user_songs[user1].intersection(user_songs[user2]))
                if common_songs > 0:
                    matches[user1][user2] = common_songs
                    matches[user2][user1] = common_songs
        
        return matches

def create_user_similarity_bar_chart(matches, output_file='user_similarities.png', by_service=False):
    """
    Create bar charts showing song matches between users.
    
    Args:
        matches: Dictionary of user matches (either simple or by service)
        output_file: Base name for output file
        by_service: Whether the matches are separated by service
    """
    if by_service:
        # Create a directory for service-specific charts
        os.makedirs('by_service', exist_ok=True)
        
        for service, service_matches in matches.items():
            if not service_matches:  # Skip empty services
                continue
                
            # Create visualization for this service
            users = list(service_matches.keys())
            data_matrix = np.zeros((len(users), len(users)))
            
            for i, user1 in enumerate(users):
                for j, user2 in enumerate(users):
                    if user1 != user2:
                        data_matrix[i][j] = service_matches[user1].get(user2, 0)
            
            plt.figure(figsize=(12, 6))
            bottom = np.zeros(len(users))
            colors = sns.color_palette("husl", len(users))
            
            for i, user in enumerate(users):
                values = data_matrix[i]
                plt.bar(users, values, bottom=bottom, label=user, color=colors[i])
                bottom += values
            
            plt.title(f'Song Matches Between Users - {service.title()}')
            plt.xlabel('Users')
            plt.ylabel('Number of Matching Songs')
            plt.xticks(rotation=45)
            plt.legend(title='Matching with', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            
            # Save service-specific plot
            service_file = os.path.join('by_service', f'user_similarities_{service}.png')
            plt.savefig(service_file, dpi=300, bbox_inches='tight')
            plt.close()
            
        # Create a combined visualization
        plt.figure(figsize=(12, 6))
        services = list(matches.keys())
        users = list(set().union(*[service_data.keys() for service_data in matches.values()]))
        x = np.arange(len(users))
        width = 0.8 / len(services)
        
        for i, service in enumerate(services):
            service_data = matches[service]
            totals = [sum(service_data.get(user, {}).values()) for user in users]
            plt.bar(x + i * width - width * len(services)/2, 
                   totals,
                   width,
                   label=service.title())
        
        plt.title('Total Song Matches by Service')
        plt.xlabel('Users')
        plt.ylabel('Number of Matching Songs')
        plt.xticks(x, users, rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
    else:
        # Original single chart behavior
        users = list(matches.keys())
        data_matrix = np.zeros((len(users), len(users)))
        
        for i, user1 in enumerate(users):
            for j, user2 in enumerate(users):
                if user1 != user2:
                    data_matrix[i][j] = matches[user1].get(user2, 0)
        
        plt.figure(figsize=(12, 6))
        bottom = np.zeros(len(users))
        colors = sns.color_palette("husl", len(users))
        
        for i, user in enumerate(users):
            values = data_matrix[i]
            plt.bar(users, values, bottom=bottom, label=user, color=colors[i])
            bottom += values
        
        plt.title('Song Matches Between Users')
        plt.xlabel('Users')
        plt.ylabel('Number of Matching Songs')
        plt.xticks(rotation=45)
        plt.legend(title='Matching with', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

def create_top_genres_growth(users_data, matches=None, output_file='top_genres_growth.png', by_service=False):
    """Create line plots showing the growth of top 20 genres over months."""
    if by_service:
        os.makedirs('by_service', exist_ok=True)
        services = ['lastfm', 'spotify', 'musicbrainz', 'discogs']
        
        for service in services:
            # Extract genres and timestamps for this service
            genre_timestamps = defaultdict(list)
            
            for user_songs in users_data.values():
                for song in user_songs:
                    timestamps = song['timestamps']
                    service_genres = song.get('genres_by_source', {}).get(service, [])
                    
                    for genre in service_genres:
                        for ts in timestamps:
                            genre_timestamps[genre].append(ts)
            
            if not genre_timestamps:  # Skip if no data for this service
                continue
                
            # Get top 20 genres for this service
            top_genres = sorted(
                genre_timestamps.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:20]
            
            # Create service-specific visualization
            create_genre_growth_plot(
                top_genres,
                title=f'Top 20 Genres Growth Over Time - {service.title()}',
                output_file=os.path.join('by_service', f'genres_growth_{service}.png')
            )
        
        # Create combined view of top genres across all services
        genre_timestamps = defaultdict(list)
        for user_songs in users_data.values():
            for song in user_songs:
                timestamps = song['timestamps']
                genres = song.get('genres', [])
                
                for genre in genres:
                    for ts in timestamps:
                        genre_timestamps[genre].append(ts)
        
        top_genres = sorted(
            genre_timestamps.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]
        
        create_genre_growth_plot(
            top_genres,
            title='Top 20 Genres Growth Over Time - All Services',
            output_file=output_file
        )
    
    else:
        # Original single chart behavior
        genre_timestamps = defaultdict(list)
        
        for user_songs in users_data.values():
            for song in user_songs:
                timestamps = song['timestamps']
                genres = song.get('genres', [])
                
                for genre in genres:
                    for ts in timestamps:
                        genre_timestamps[genre].append(ts)
        
        top_genres = sorted(
            genre_timestamps.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]
        
        create_genre_growth_plot(
            top_genres,
            title='Top 20 Genres Growth Over Time',
            output_file=output_file
        )

def create_genre_growth_plot(top_genres, title, output_file):
    """Helper function to create genre growth plots."""
    monthly_matches = defaultdict(lambda: defaultdict(int))
    
    for genre, timestamps in top_genres:
        for ts in timestamps:
            date = datetime.fromtimestamp(ts)
            month_key = f"{date.year}-{date.month:02d}"
            monthly_matches[genre][month_key] += 1
    
    plt.figure(figsize=(15, 8))
    
    all_months = sorted(set(
        month
        for genre_data in monthly_matches.values()
        for month in genre_data.keys()
    ))
    
    for genre, timestamps in monthly_matches.items():
        values = [timestamps.get(month, 0) for month in all_months]
        plt.plot(all_months, values, marker='o', label=genre)
    
    plt.title(title)
    plt.xlabel('Month')
    plt.ylabel('Number of User Matches')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def create_user_genres_growth(users_data, output_dir='user_genres/', by_service=False):
    """Create individual genre growth plots for each user."""
    os.makedirs(output_dir, exist_ok=True)
    
    for username, songs in users_data.items():
        if by_service:
            services = ['lastfm', 'spotify', 'musicbrainz', 'discogs']
            
            for service in services:
                # Extract genres and timestamps for this service and user
                genre_timestamps = defaultdict(list)
                
                for song in songs:
                    timestamps = song['timestamps']
                    service_genres = song.get('genres_by_source', {}).get(service, [])
                    
                    for genre in service_genres:
                        for ts in timestamps:
                            genre_timestamps[genre].append(ts)
                
                if not genre_timestamps:  # Skip if no data for this service
                    continue
                
                # Get top 20 genres for this user and service
                top_genres = sorted(
                    genre_timestamps.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:20]
                
                # Create visualization
                service_dir = os.path.join(output_dir, service)
                os.makedirs(service_dir, exist_ok=True)
                
                create_genre_growth_plot(
                    top_genres,
                    title=f'Top 20 Genres Growth Over Time - {username} ({service.title()})',
                    output_file=os.path.join(service_dir, f'{username}_genres_growth.png')
                )
        
        # Create combined view for user
        genre_timestamps = defaultdict(list)
        for song in songs:
            timestamps = song['timestamps']
            genres = song.get('genres', [])
            
            for genre in genres:
                for ts in timestamps:
                    genre_timestamps[genre].append(ts)
        
        top_genres = sorted(
            genre_timestamps.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]
        
        create_genre_growth_plot(
            top_genres,
            title=f'Top 20 Genres Growth Over Time - {username} (All Services)',
            output_file=os.path.join(output_dir, f'{username}_genres_growth.png')
        )

def main(json_file_path, exclude_tags=None, by_service=False):
    """Main function to process data and generate visualizations."""
    # Load data
    data = load_data(json_file_path)
    users_data = data['users']
    
    # Generate all visualizations
    matches = find_song_matches(users_data, exclude_tags, by_service)
    create_user_similarity_bar_chart(matches, by_service=by_service)
    create_top_genres_growth(users_data, matches, by_service=by_service)
    create_user_genres_growth(users_data, by_service=by_service)

if __name__ == "__main__":
    # Example usage with excluded tags and service separation
    json_file_path = sys.argv[1]
    excluded_tags = ['seen live', 'spotify', 'favorites']
    main(json_file_path, exclude_tags=excluded_tags, by_service=True)