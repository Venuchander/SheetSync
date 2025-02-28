import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# Setup the Sheets API
def setup_sheets_api():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # Load credentials from credentials.json file
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    return gspread.authorize(credentials)

def sync_debugging_participants():
    # Setup API client
    client = setup_sheets_api()
    
    # Open source spreadsheet (your form responses sheet)
    source_sheet_id = "1sGhG6paIApPv7CT8F7LOkI7RU0uGweMd_b31uct6a0k"
    source = client.open_by_key(source_sheet_id)
    
    # Based on your spreadsheet link, gid=964701258 points to a specific worksheet
    source_worksheet = source.get_worksheet_by_id(964701258)
    
    # Get all data from source including headers
    all_values = source_worksheet.get_all_values()
    headers = all_values[0]
    
    # Convert to list of dictionaries for easier processing
    all_data = []
    for row in all_values[1:]:  # Skip the header row
        row_dict = {headers[i]: row[i] for i in range(len(headers))}
        all_data.append(row_dict)
    
    # Find the column that contains event information (likely "Which events would you like to participate in?")
    event_column = None
    for header in headers:
        if "event" in header.lower():
            event_column = header
            break
    
    if not event_column:
        print("Could not find event column in the spreadsheet")
        return
    
    # Filter for participants who registered for debugging events (case insensitive)
    debugging_participants = []
    for row in all_data:
        if row.get(event_column) and "debug" in row.get(event_column).lower():
            debugging_participants.append(row)
    
    # Open destination spreadsheet - replace with your destination sheet ID
    dest_sheet_id = "1xZLkDj7d07LmK3VpLaHnuEkjZL2NOSxdHlqu0ZXCGRg"  # Replace this with your actual destination sheet ID
    
    try:
        dest = client.open_by_key(dest_sheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Destination spreadsheet with ID {dest_sheet_id} not found.")
        return
    
    # Get or create the main worksheet in the destination spreadsheet
    try:
        dest_worksheet = dest.get_worksheet(0)  # First worksheet
        # Clear all existing data for complete overwrite
        dest_worksheet.clear()
    except:
        dest_worksheet = dest.add_worksheet("Debugging Participants", 1000, 26)
    
    # If there's data to add
    if debugging_participants:
        # Add header row
        dest_worksheet.append_row(headers)
        
        # Add data rows
        for participant in debugging_participants:
            dest_worksheet.append_row([participant.get(h, '') for h in headers])
    
    # Add timestamp for last sync
    try:
        timestamp_sheet = dest.worksheet("Sync Log")
    except:
        timestamp_sheet = dest.add_worksheet("Sync Log", 1, 2)
    
    timestamp = datetime.now(pytz.timezone('UTC')).strftime("%Y-%m-%d %H:%M:%S UTC")
    timestamp_sheet.update_cell(1, 1, "Last Synced")
    timestamp_sheet.update_cell(1, 2, timestamp)
    
    print(f"Sync completed at {timestamp}. Found {len(debugging_participants)} debugging participants.")

if __name__ == "__main__":
    sync_debugging_participants()