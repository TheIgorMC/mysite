"""
Email grouping utility for sending grouped notifications to users managing multiple athletes
"""
from flask import current_app

def get_user_emails_for_athlete_cached(tessera_atleta, cache=None):
    """
    Get all user emails who are authorized to manage this athlete.
    Uses a cache to avoid repeated database queries.
    
    Args:
        tessera_atleta: Athlete's tessera ID
        cache: Optional dict mapping tessera -> list of emails
        
    Returns:
        List of email addresses
    """
    if cache is not None and tessera_atleta in cache:
        return cache[tessera_atleta]
    
    # Import here to avoid circular imports
    from app.routes.archery import get_user_emails_for_athlete
    emails = get_user_emails_for_athlete(tessera_atleta)
    
    if cache is not None:
        cache[tessera_atleta] = emails
    
    return emails


def send_grouped_emails(athletes_data, mail_type, subject_prefix, body_text, client):
    """
    Send grouped emails for multiple athletes.
    Groups athletes by email address and sends one email per address with all athlete details.
    
    Args:
        athletes_data: List of dicts with keys: 'tessera_atleta', 'details' (dict)
        mail_type: Email template type (e.g., 'subscription', 'cancellation_confirmed')
        subject_prefix: Email subject prefix
        body_text: Email body text
        client: OrionAPIClient instance
    """
    # Group athletes by email address
    email_to_athletes = {}
    email_cache = {}
    
    for athlete_data in athletes_data:
        tessera = athlete_data['tessera_atleta']
        details = athlete_data['details']
        
        # Get all emails for this athlete (with caching)
        user_emails = get_user_emails_for_athlete_cached(tessera, email_cache)
        
        for email in user_emails:
            if email not in email_to_athletes:
                email_to_athletes[email] = []
            email_to_athletes[email].append({
                'tessera': tessera,
                'details': details
            })
    
    # Send one email per email address
    for email, athletes in email_to_athletes.items():
        current_app.logger.info(f'[EMAIL] Sending grouped email to {email} for {len(athletes)} athlete(s)')
        
        try:
            # If multiple athletes, combine their details
            if len(athletes) == 1:
                # Single athlete - use original details format
                combined_details = athletes[0]['details']
            else:
                # Multiple athletes - create grouped format
                combined_details = {}
                
                # Add competition info from first athlete (should be same for all)
                first_details = athletes[0]['details']
                for key in ['Nome Gara', 'Codice Gara']:
                    if key in first_details:
                        combined_details[key] = first_details[key]
                
                # Add each athlete's info
                for i, athlete in enumerate(athletes, 1):
                    prefix = f"Atleta {i}"
                    for key, value in athlete['details'].items():
                        if key not in ['Nome Gara', 'Codice Gara']:
                            combined_details[f"{prefix} - {key}"] = value
            
            # Adjust subject for multiple athletes
            subject = subject_prefix
            if len(athletes) > 1:
                subject += f" ({len(athletes)} atleti)"
            
            result = client.send_email(
                recipient_email=email,
                mail_type=mail_type,
                locale='it',
                subject=subject,
                body_text=body_text,
                details_json=combined_details
            )
            current_app.logger.info(f'[EMAIL] Successfully queued grouped email to {email}: {result}')
        except Exception as send_err:
            current_app.logger.error(f'[EMAIL] Failed to send grouped email to {email}: {send_err}')
