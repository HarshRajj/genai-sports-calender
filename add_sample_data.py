from step5_database_storage import TournamentDatabase
import json

def add_sample_tournament_data():
    db = TournamentDatabase()
    if not db.connect_to_database():
        print("Failed to connect to database")
        return
    
    cursor = db.connection.cursor()
    
    # Update a tournament with complete sample data
    sample_data = {
        'venue': json.dumps(["Mumbai Cricket Stadium", "Wankhede Stadium"]),
        'date_info': json.dumps(["Registration: Till Aug 30, 2025", "Tournament: Sep 15-20, 2025"]),
        'entry_fees': "₹500 per team",
        'eligibility': json.dumps(["Age 18-35", "Mumbai residents only"]),
        'prizes': json.dumps(["Winner: ₹50,000", "Runner-up: ₹25,000"]),
        'link': "https://www.nclindia.in/"
    }
    
    cursor.execute("""
        UPDATE tournaments 
        SET venue = %s, date_info = %s, entry_fees = %s, 
            eligibility = %s, prizes = %s, link = %s
        WHERE name = 'National Cricket League'
    """, (
        sample_data['venue'],
        sample_data['date_info'],
        sample_data['entry_fees'],
        sample_data['eligibility'],
        sample_data['prizes'],
        sample_data['link']
    ))
    
    db.connection.commit()
    print(f"Updated {cursor.rowcount} tournament with complete sample data")
    
    db.close_connection()

if __name__ == "__main__":
    add_sample_tournament_data()
