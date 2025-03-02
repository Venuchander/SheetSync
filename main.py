import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz


def setup_sheets_api():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    return gspread.authorize(credentials)

def sync_debugging_participants():
    
    client = setup_sheets_api()
    
    
    source_sheet_id = "1sGhG6paIApPv7CT8F7LOkI7RU0uGweMd_b31uct6a0k"
    source = client.open_by_key(source_sheet_id)
    
    
    source_worksheet = source.get_worksheet_by_id(964701258)
    
    
    all_values = source_worksheet.get_all_values()
    headers = all_values[0]
    
    
    event_column = None
    for header in headers:
        if "event" in header.lower():
            event_column = header
            break
    
    if not event_column:
        print("Could not find event column in the spreadsheet")
        return
    
    
    debugging_rows = []
    for i, row in enumerate(all_values[1:], 1):  
        row_dict = {headers[j]: row[j] for j in range(len(headers))}
        event_value = row_dict.get(event_column, "")
        if "debug" in event_value.lower():
            debugging_rows.append((i, row))  
    
    
    dest_sheet_id = "1xZLkDj7d07LmK3VpLaHnuEkjZL2NOSxdHlqu0ZXCGRg" 
    
    try:
        dest = client.open_by_key(dest_sheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Destination spreadsheet with ID {dest_sheet_id} not found.")
        return
    
    
    try:
        dest_worksheet = dest.get_worksheet(0)  
    except:
        dest_worksheet = dest.add_worksheet("Debugging Participants", 1000, 26)
    
    
    dest_values = dest_worksheet.get_all_values()
    if not dest_values:
        
        dest_worksheet.update_cell(1, 1, "Timestamp")  
        dest_worksheet.update([headers])  
        
        
        rows_to_add = [row for _, row in debugging_rows]
        if rows_to_add:
            dest_worksheet.append_rows(rows_to_add)
        new_count = len(rows_to_add)
    else:
        
        email_col_idx = -1
        for i, header in enumerate(headers):
            if "email" in header.lower():
                email_col_idx = i
                break
        
        if email_col_idx == -1:
            print("Could not find email column for uniqueness check")
            return
            
        
        existing_emails = set()
        for row in dest_values[1:]:  
            if email_col_idx < len(row) and row[email_col_idx]:
                existing_emails.add(row[email_col_idx])
        
        
        new_count = 0
        rows_to_add = []
        for _, row in debugging_rows:
            if email_col_idx < len(row) and row[email_col_idx] not in existing_emails:
                rows_to_add.append(row)
                existing_emails.add(row[email_col_idx])
                
        if rows_to_add:
            dest_worksheet.append_rows(rows_to_add)  
            new_count = len(rows_to_add)
    
    
    try:
        timestamp_sheet = dest.worksheet("Sync Log")
    except:
        timestamp_sheet = dest.add_worksheet("Sync Log", 3, 2)
    
    timestamp = datetime.now(pytz.timezone('UTC')).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    
    timestamp_sheet.update_cell(1, 1, "Last Synced")
    timestamp_sheet.update_cell(1, 2, timestamp)
    timestamp_sheet.update_cell(2, 1, "New Entries Added")
    timestamp_sheet.update_cell(2, 2, str(new_count))
    timestamp_sheet.update_cell(3, 1, "Total Entries")
    timestamp_sheet.update_cell(3, 2, str(len(dest_worksheet.get_all_values()) - 1))  
    
    print(f"Sync completed at {timestamp}. Added {new_count} new debugging participants.")

if __name__ == "__main__":
    sync_debugging_participants()
