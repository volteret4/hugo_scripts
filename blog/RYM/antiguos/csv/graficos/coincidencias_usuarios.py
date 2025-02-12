import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns

def load_data(file_path):
    """Load and parse JSON data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_song_matches(users_data):
    """Find song matches between users."""
    # Create a dictionary to store songs for each user
    user_songs = {user: set((song['name'], song['artist']['name']) 
                           for song in songs)
                 for user, songs in users_data.items()}
    
    # Calculate matches between users
    matches = defaultdict(lambda: defaultdict(int))
    users = list(users_data.keys())
    
    for i, user1 in enumerate(users):
        for user2 in users[i+1:]:
            common_songs = len(user_songs[user1].intersection(user_songs[user2]))
            matches[user1][user2] = common_songs
            matches[user2][user1] = common_songs
    
    return matches

def create_user_similarity_bar_chart(matches, output_file='user_similarities.png'):
    """Create a stacked bar chart showing song matches between users."""
    # Prepare data for visualization
    users = list(matches.keys())
    data_matrix = np.zeros((len(users), len(users)))
    
    for i, user1 in enumerate(users):
        for j, user2 in enumerate(users):
            if user1 != user2:
                data_matrix[i][j] = matches[user1][user2]

    # Create color palette
    colors = sns.color_palette("husl", len(users))
    
    # Create stacked bar chart
    plt.figure(figsize=(12, 6))
    bottom = np.zeros(len(users))
    
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
    
    # Save the plot
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main(json_file_path):
    """Main function to process data and generate visualizations."""
    # Load data
    data = load_data(json_file_path)
    users_data = data['users']
    
    # Find matches between users
    matches = find_song_matches(users_data)
    
    # Create visualizations
    create_user_similarity_bar_chart(matches)

if __name__ == "__main__":
    # Replace with your JSON file path
    json_file_path = sys.argv[1]
    main(json_file_path)