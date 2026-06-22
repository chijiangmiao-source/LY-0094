from database import execute_query, execute_non_query
import datetime

def generate_record_no():
    today = datetime.datetime.now().strftime('%Y%m%d')
    count = execute_query('SELECT COUNT(*) FROM host_script WHERE record_no LIKE ?', (f'{today}%',))[0][0]
    return f'{today}{str(count + 1).zfill(3)}'

def add_host_script(bride_name, groom_name, wedding_date, host_name, current_version=1.0, feedback_round=0, finalized_status='未定稿', remarks=''):
    record_no = generate_record_no()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        script_id = execute_non_query('''
            INSERT INTO host_script (record_no, bride_name, groom_name, wedding_date, host_name, 
                                    current_version, feedback_round, finalized_status, remarks, 
                                    created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record_no, bride_name, groom_name, wedding_date, host_name, current_version, feedback_round, finalized_status, remarks, now, now))
        return script_id, None
    except Exception as e:
        return None, str(e)

def get_all_host_scripts():
    return execute_query('''
        SELECT id, record_no, bride_name, groom_name, wedding_date, host_name, 
               current_version, feedback_round, finalized_status, remarks, updated_at
        FROM host_script ORDER BY updated_at DESC
    ''')

def get_host_script_by_id(script_id):
    return execute_query('''
        SELECT id, record_no, bride_name, groom_name, wedding_date, host_name, 
               current_version, feedback_round, finalized_status, remarks
        FROM host_script WHERE id = ?
    ''', (script_id,), fetch_one=True)

def update_host_script(script_id, bride_name, groom_name, wedding_date, host_name, current_version, feedback_round, finalized_status, remarks):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        execute_non_query('''
            UPDATE host_script SET bride_name=?, groom_name=?, wedding_date=?, host_name=?, 
                                  current_version=?, feedback_round=?, finalized_status=?, 
                                  remarks=?, updated_at=?
            WHERE id = ?
        ''', (bride_name, groom_name, wedding_date, host_name, current_version, feedback_round, finalized_status, remarks, now, script_id))
        return True, None
    except Exception as e:
        return False, str(e)

def delete_host_script(script_id):
    try:
        execute_non_query('DELETE FROM host_script WHERE id = ?', (script_id,))
        return True, None
    except Exception as e:
        return False, str(e)

def check_duplicate(bride_name, groom_name, wedding_date, exclude_id=None):
    if exclude_id:
        count = execute_query('''
            SELECT COUNT(*) FROM host_script 
            WHERE bride_name=? AND groom_name=? AND wedding_date=? AND id != ?
        ''', (bride_name, groom_name, wedding_date, exclude_id), fetch_one=True)[0]
    else:
        count = execute_query('''
            SELECT COUNT(*) FROM host_script 
            WHERE bride_name=? AND groom_name=? AND wedding_date=?
        ''', (bride_name, groom_name, wedding_date), fetch_one=True)[0]
    return count > 0

def add_change_record(script_id, modify_paragraph, modify_reason, feedback_source, is_adopted=1):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        record_id = execute_non_query('''
            INSERT INTO change_record (script_id, modify_date, modify_paragraph, 
                                       modify_reason, feedback_source, is_adopted, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (script_id, now, modify_paragraph, modify_reason, feedback_source, is_adopted, now))
        check_high_freq_issue(modify_reason)
        return record_id, None
    except Exception as e:
        return None, str(e)

def get_change_records_by_script_id(script_id):
    return execute_query('''
        SELECT id, script_id, modify_date, modify_paragraph, modify_reason, 
               feedback_source, is_adopted, created_at
        FROM change_record WHERE script_id = ? ORDER BY created_at DESC
    ''', (script_id,))

def get_change_record_count(script_id):
    count = execute_query('SELECT COUNT(*) FROM change_record WHERE script_id = ?', (script_id,), fetch_one=True)[0]
    return count

def delete_change_record(record_id):
    try:
        execute_non_query('DELETE FROM change_record WHERE id = ?', (record_id,))
        return True, None
    except Exception as e:
        return False, str(e)

def check_high_freq_issue(reason_text):
    existing = execute_query('SELECT id, occurrence_count FROM high_freq_issues WHERE issue_text = ?', (reason_text,), fetch_one=True)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if existing:
        issue_id, count = existing
        new_count = count + 1
        execute_non_query('''
            UPDATE high_freq_issues SET occurrence_count=?, last_occurrence=? WHERE id = ?
        ''', (new_count, now, issue_id))
    else:
        execute_non_query('''
            INSERT INTO high_freq_issues (issue_text, occurrence_count, first_occurrence, last_occurrence)
            VALUES (?, 1, ?, ?)
        ''', (reason_text, now, now))

def get_high_freq_issues():
    return execute_query('''
        SELECT issue_text, occurrence_count, first_occurrence, last_occurrence
        FROM high_freq_issues ORDER BY occurrence_count DESC
    ''')

def search_host_scripts(keyword):
    return execute_query('''
        SELECT id, record_no, bride_name, groom_name, wedding_date, host_name, 
               current_version, feedback_round, finalized_status, remarks, updated_at
        FROM host_script 
        WHERE record_no LIKE ? OR bride_name LIKE ? OR groom_name LIKE ? OR 
              host_name LIKE ? OR remarks LIKE ?
        ORDER BY updated_at DESC
    ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))

def filter_host_scripts(host_name=None, finalized_status=None, date_range=None):
    sql = '''
        SELECT id, record_no, bride_name, groom_name, wedding_date, host_name, 
               current_version, feedback_round, finalized_status, remarks, updated_at
        FROM host_script WHERE 1=1
    '''
    params = []
    
    if host_name:
        sql += ' AND host_name = ?'
        params.append(host_name)
    
    if finalized_status:
        sql += ' AND finalized_status = ?'
        params.append(finalized_status)
    
    if date_range and len(date_range) == 2:
        sql += ' AND wedding_date BETWEEN ? AND ?'
        params.extend(date_range)
    
    sql += ' ORDER BY updated_at DESC'
    return execute_query(sql, params)

def get_stats_overview():
    total = execute_query('SELECT COUNT(*) FROM host_script', fetch_one=True)[0]
    finalized = execute_query("SELECT COUNT(*) FROM host_script WHERE finalized_status = '已定稿'", fetch_one=True)[0]
    avg_round = execute_query("SELECT AVG(feedback_round) FROM host_script", fetch_one=True)[0]
    total_changes = execute_query('SELECT COUNT(*) FROM change_record', fetch_one=True)[0]
    return {
        'total': total,
        'finalized': finalized,
        'avg_round': round(avg_round, 1) if avg_round else 0,
        'total_changes': total_changes
    }

def get_version_stats():
    return execute_query('''
        SELECT current_version, COUNT(*) as cnt 
        FROM host_script GROUP BY current_version ORDER BY current_version
    ''')

def get_feedback_source_stats():
    return execute_query('''
        SELECT feedback_source, COUNT(*) as cnt 
        FROM change_record WHERE feedback_source IS NOT NULL 
        GROUP BY feedback_source ORDER BY cnt DESC
    ''')

def get_change_reason_stats():
    return execute_query('''
        SELECT modify_reason, COUNT(*) as cnt 
        FROM change_record GROUP BY modify_reason ORDER BY cnt DESC LIMIT 10
    ''')

def get_host_names():
    return execute_query('SELECT DISTINCT host_name FROM host_script ORDER BY host_name')